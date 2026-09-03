#!/usr/bin/env python3
"""
soil_model_core.py

Core ODE + analysis for the multi-land soil model.
No Streamlit or plotting here.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional



import numpy as np
from scipy import signal
from scipy.signal import savgol_filter
from scipy.integrate import solve_ivp
from scipy.stats import gamma
from scipy.special import gammaln  # stable log-gamma for analytic Gini


# ------------------------------------------------------------
# Farming Modes
# ------------------------------------------------------------

# def B_pulse_train(
#     t: float,
#     omega: int,
#     tau: int = 1,
#     phase: float = 0.0,
#     eps: float = 1e-10
# ) -> float:
#     """
#     Pulse train for farming mode (cash crops vs cover crops).

#     B(t) in {0,1}
#       - B(t) = 0 during cover-crop window of length tau at start of each cycle
#       - B(t) = 1 otherwise (cash crops)

#     General implemented form:
#       B_i(t)=0 if t in [k*omega + phase, k*omega + phase + tau), else 1
#     """
#     omega = int(omega)
#     tau = int(tau)

#     if omega <= 0:
#         return 1.0
#     if tau <= 0:
#         return 1.0
#     if tau >= omega:
#         return 0.0
#     if t < 0:
#         return 1.0  # pre-cycle, assume cash crops

#     cycle_time = (t - phase) % omega
#     return 0.0 if (cycle_time < tau - eps) else 1.0


def savgol_smooth_years(
    y,
    t,
    window_years: float = 3.0,
    polyorder: int = 2,
    preserve_initial: bool = True,
):
    y = np.asarray(y, dtype=float)
    t = np.asarray(t, dtype=float)

    if y.size < 5:
        return y.copy()

    dt = float(np.median(np.diff(t)))
    if dt <= 0:
        return y.copy()

    # Convert a physical window in years to a number of samples
    window_length = int(round(window_years / dt))

    # Savitzky-Golay requires an odd window length
    if window_length % 2 == 0:
        window_length += 1

    # Window must be larger than polyorder
    min_window = polyorder + 2
    if min_window % 2 == 0:
        min_window += 1

    window_length = max(window_length, min_window)

    # Window cannot exceed length of data
    if window_length >= y.size:
        window_length = y.size if y.size % 2 == 1 else y.size - 1

    if window_length <= polyorder or window_length < 3:
        return y.copy()

    y_smooth = savgol_filter(
        y,
        window_length=window_length,
        polyorder=polyorder,
        mode="interp",
    )

    # Optional: force the plotted curve to respect the exact initial value
    if preserve_initial:
        y_smooth[0] = y[0]

    return y_smooth


def B_pulse_train(t, omega=3.0, tau=1.0, phase=0.0):
    """
    Simple pulse train for farming state.

    Interpretation
    --------------
    B(t) = 0 → cover crop (LOW state, no degradation)
    B(t) = 1 → cash crop (HIGH state, degradation active)

    One full cycle (length = omega) is:
        LOW plateau → HIGH plateau
    """
 # Shift time
    t_shift = np.asarray(t) - phase

    # Fold into repeating interval [0, omega)
    cycle = np.mod(t_shift, omega)

    low = 0.1
    high = 1-low

    # LOW for cycle < tau, HIGH otherwise
    y = np.where(cycle < tau, low, high)

    return y


# def B_pulse_train(t, omega=3.0, tau=1.0, phase=0.0, amp=1.0):
#     """
#     Trapezoidal wave for farming state.

#     Interpretation
#     --------------
#     B(t) = 0 → cover crop (LOW state, no degradation)
#     B(t) = 1 → cash crop (HIGH state, degradation active)

#     One full cycle (length = omega) is:
#         LOW plateau → ramp up → HIGH plateau → ramp down

#     Parameters
#     ----------
#     t : array-like
#         Time values.
#     omega : float
#         Total length of one cycle.
#     tau : float
#         Duration of LOW plateau (cover crop).
#     phase : float
#         Shifts the signal in time.
#     amp : float
#         Maximum value (default = 1).

#     Returns
#     -------
#     y : array-like
#         Signal in [0, amp].
#     """

#     # Shift time for phase offset
#     t_shift = t - phase

#     # Fold time into one repeating cycle [0, omega)
#     cycle = np.mod(t_shift, omega)

#     # Duration of the smooth transitions (up and down)
#     ramp = 0.5

#     # Output array
#     y = np.zeros_like(cycle, dtype=float)

#     # --- Sanity check ---
#     # Need space for: LOW + ramp up + HIGH + ramp down
#     if tau + 2 * ramp > omega:
#         raise ValueError(
#             "tau + 2*ramp must be <= omega "
#             "(otherwise no room for HIGH plateau)"
#         )

#     # =====================================
#     # Define regions of the trapezoid shape
#     # =====================================

#     # 1) LOW plateau (cover crop)
#     # From start of cycle up to tau
#     mask_low = cycle < tau

#     # 2) RISING edge (transition 0 → amp)
#     # Linear increase over 'ramp' time
#     mask_rise = (cycle >= tau) & (cycle < tau + ramp)

#     # 3) HIGH plateau (cash crop / degradation active)
#     # Starts AFTER ramp-up finishes
#     mask_high = (cycle >= tau + ramp) & (cycle < omega - ramp)

#     # 4) FALLING edge (transition amp → 0)
#     # Last 'ramp' portion of the cycle
#     mask_fall = cycle >= omega - ramp

#     # =====================================
#     # Assign values to each region
#     # =====================================

#     # LOW plateau → 0
#     y[mask_low] = 0.0

#     # RAMP UP → linear increase from 0 to amp
#     y[mask_rise] = amp * (
#         (cycle[mask_rise] - tau) / ramp
#     )

#     # HIGH plateau → constant amp
#     y[mask_high] = amp

#     # RAMP DOWN → linear decrease from amp to 0
#     y[mask_fall] = amp * (
#         1 - (cycle[mask_fall] - (omega - ramp)) / ramp
#     )

#     return y

# ------------------------------------------------------------
# Degradation functions
# ------------------------------------------------------------

def g_fertiliser(F: float, zeta: float, D0: float) -> float:
    """g(F) = F^2 - 2*zeta*F + D0"""
    F = float(F)
    zeta = float(zeta)
    D0 = float(D0)
    return F * F - 2.0 * zeta * F + D0


def degradation_constant(t: float, params: Dict) -> float:
    return float(params["D_const"])


def degradation_phaseout(t: float, params: Dict) -> float:
    return float(params["D_high"] if t < params["T_int"] else params["D_low"])


def degradation_natural_synthetic(t: float, params: Dict) -> float:
    """
    Natural -> synthetic degradation transition.
    D(t) = a0 * exp(-alpha * t) + a1 * (1 - exp(-beta * t))
    """
    alpha = float(params.get("alpha", 0.5))
    beta = float(params.get("beta", 0.5))
    a0 = float(params.get("a0", 1.0))
    a1 = float(params.get("a1", 1.0))
    return a0 * np.exp(-alpha * t) + a1 * (1.0 - np.exp(-beta * t))


def degradation_fertiliser_parabola(t: float, params: Dict) -> float:
    """
    Returns g(F) (time-constant). B(t) is applied outside (in the ODE).

    params expects:
      - F
      - zeta
      - D0
    """
    F = float(params.get("F", 1.0))
    zeta = float(params.get("zeta", 1.0))
    D0 = float(params.get("D0", 1.2))
    return g_fertiliser(F, zeta, D0)


SCENARIOS = {
    "Constant degradation D": degradation_constant,
    "Phase-out at T_int": degradation_phaseout,
    "Natural to synthetic": degradation_natural_synthetic,
    "Fertiliser parabola": degradation_fertiliser_parabola,
}


# ------------------------------------------------------------
# Recovery functions
# ------------------------------------------------------------

def alpha_constant(S: float, params: Dict) -> float:
    return float(params["alpha_const"])


def alpha_logistic(S: float, params: Dict) -> float:
    alpha_max = float(params.get("alpha_max", 0.25))
    rho = float(params.get("rho", 50.0))
    S_T = float(params.get("S_T", 0.2))
    z = np.clip(-rho * (S - S_T), -160, 160)
    return alpha_max / (1.0 + np.exp(z))


RECOVERY_MODES = {
    "Constant alpha": alpha_constant,
    "Logistic alpha(S)": alpha_logistic,
}


# ------------------------------------------------------------
# Yield response
# ------------------------------------------------------------

def h_yield(F: float, xi: float, psi: float) -> float:
    """
    h(F) = max(0, (-F^2 + xi*F) * exp(-psi*F))
    """
    F = float(F)
    xi = float(xi)
    psi = float(psi)
    val = (-F * F + xi * F) * np.exp(-psi * F)
    return float(max(0.0, val))


# ------------------------------------------------------------
# Reinvestment function
# ------------------------------------------------------------

def J_investment_func(
    pop,
    C,
    P_tilde,
    I,
    nu: float,
    eta: float,
    beta_q: float,
    theta: float,
    eps: float = 1e-12,
):
    """
    Reinvestment potential J(t).

    Mathematical form:
        J(t) = -nu/2 + sqrt(nu^2/4
               + nu*eta*beta_q*theta*U(t)*C(t) / (I(t)*P_tilde(t)))

    Notes
    -----
    - P_tilde is the baseline soil-driven production, before reinvestment.
    - C food consumption per capita per year
    - I inflatio index 
    - pop population at time t
    """
    pop = np.asarray(pop, dtype=float)
    C = np.asarray(C, dtype=float)
    P_tilde = np.maximum(np.asarray(P_tilde, dtype=float), eps)
    I = np.maximum(np.asarray(I, dtype=float), eps)

    nu = float(nu)
    eta = float(eta)
    beta_q = float(beta_q)
    theta = float(theta)

    half_nu = nu / 2.0
    inside = half_nu**2 + (nu * eta * beta_q * theta * pop * C) / (I * P_tilde)
    inside = np.maximum(inside, 0.0)

    return -half_nu + np.sqrt(inside)


# ------------------------------------------------------------
# Income distribution helpers
# ------------------------------------------------------------

def gamma_pdf(x: np.ndarray, alpha: float, rate: float) -> np.ndarray:
    """
    Gamma PDF with shape alpha and rate=rate (scale = 1/rate).
    """
    out = gamma.pdf(x, a=alpha, scale=1.0 / rate)
    out = np.maximum(out, 1e-12)  # avoid exact zeros for numerical stability
    return out


# ------------------------------------------------------------
# Data structures
# ------------------------------------------------------------

@dataclass
class LandConfig:
    """Configuration for a single land / land owner."""
    name: str
    alpha: float
    S0: float
    scenario_name: str
    deg_params: Dict
    land_fraction: float
    P_max: float
    recovery_name: str = "Constant alpha"
    recovery_params: Dict = None

    # Farming mode
    omega: int = 1
    tau: int = 0
    phase: float = 0.0

    # Per-land emissions factors (tCO2eq/(ha*yr))
    # E_H > 0 = cultivation emissions magnitude
    # E_S > 0 = cover-crop sequestration magnitude
    E_H: Optional[float] = None
    E_S: Optional[float] = None


@dataclass
class SimulationResult:
    t: np.ndarray
    soils: np.ndarray
    degradations: np.ndarray

    productions: np.ndarray              # (n_lands, n_times) tonnes/yr, baseline/soil-driven
    total_production: np.ndarray         # (n_times,) tonnes/yr, baseline/soil-driven P_tilde
    total_production_real: np.ndarray    # (n_times,) tonnes/yr, boosted production P
    J_investment: np.ndarray             # (n_times,) reinvestment potential J(t)
    weighted_soil: np.ndarray

    land_names: List[str]
    land_fractions: np.ndarray
    alphas: np.ndarray
    P_max_vec: np.ndarray

    population: np.ndarray
    food_consumption: np.ndarray         # calorie demand
    self_sufficiency_ratio: np.ndarray
    average_real_income: np.ndarray

    inflation_index: Optional[np.ndarray] = None
    redistribution_lambda: Optional[np.ndarray] = None

    palma_ratio: Optional[np.ndarray] = None
    gini_coefficient: Optional[np.ndarray] = None

    income_x20: Optional[np.ndarray] = None

    harvest_per_land: Optional[np.ndarray] = None
    total_harvest: Optional[np.ndarray] = None

    emissions_by_land: Optional[np.ndarray] = None   # (n_lands, n_times) tCO2eq/yr
    total_emissions: Optional[np.ndarray] = None     # (n_times,) tCO2eq/yr

    income_x: Optional[np.ndarray] = None            # (n_x,)
    income_pdf: Optional[np.ndarray] = None          # (n_times, n_x)
    food_price_index: Optional[np.ndarray] = None   # (n_times,)
    food_insecurity_index: Optional[np.ndarray] = None  # (n_times,)

# ------------------------------------------------------------
# Core solver
# ------------------------------------------------------------

def _soil_ode_single(
    t: float,
    S: np.ndarray,
    D_fun,
    deg_params: Dict,
    alpha_fun,
    recovery_params: Dict,
    omega: int,
    tau: int,
    phase: float,
) -> np.ndarray:
    S_val = float(S[0])

    a = float(alpha_fun(S_val, recovery_params))
    D_base = float(D_fun(t, deg_params))
    B_t = B_pulse_train(t, omega=omega, tau=tau, phase=phase)

    # Degradation active only during cultivated phase
    D_t = D_base * B_t

    net = a - D_t
    if abs(net) < 1e-12:
        net = 0.0

    return np.array([net * S_val * (1.0 - S_val)], dtype=float)


# ------------------------------------------------------------
# Macro ODEs
# ------------------------------------------------------------

def _population_ODE(P: float, population_growth_rate: float) -> float:
    return population_growth_rate * P


def _inflation_index_ODE(I: float, inflation_rate: float) -> float:
    return inflation_rate * I


def _average_real_income_ODE(mu_real: float, income_growth_rate: float) -> float:
    """
    Evolves real income directly.
    """
    return income_growth_rate * mu_real


def _redistribution_factor_ODE(
    lam: float,
    redistribution_rate: float,
    mu_real: float
) -> float:

    mu_eff = max(float(mu_real), 1e-12)
    return redistribution_rate * (lam - 1.0 / mu_eff)


def rolling_mean(a, window):
    a = np.asarray(a, dtype=float)
    window = max(1, int(window))

    if window == 1:
        return a.copy()
    if window >= len(a):
        return np.full_like(a, np.mean(a), dtype=float)

    windows = np.lib.stride_tricks.sliding_window_view(a, window)
    means = windows.mean(axis=-1)
    pad_left = window // 2
    pad_right = window - pad_left - 1

    return np.pad(means, (pad_left, pad_right), mode='edge')


def all_ODEs(
    t: float,
    y: np.ndarray,
    population_growth_rate: float,
    income_growth_rate: float,
    inflation_rate: float,
    redistribution_rate: float,
) -> np.ndarray:
    """
    State ordering:
      y = [P, mu_real, inflation_index, lambda]
    """
    P, mu_real, infl, lam = y

    dP = _population_ODE(P, population_growth_rate)
    dmu = _average_real_income_ODE(mu_real, income_growth_rate)
    dinfl = _inflation_index_ODE(infl, inflation_rate)
    dlam = _redistribution_factor_ODE(lam, redistribution_rate, mu_real)

    return np.array([dP, dmu, dinfl, dlam], dtype=float)


def initial_conditions(P0: float, mu0: float, infl0: float, lam0: float) -> np.ndarray:
    return np.array([P0, mu0, infl0, lam0], dtype=float)


def simulate_multi_land(
    lands: List[LandConfig],
    T_max: float,
    n_points: int = 500,

    # macro initial conditions + rates
    initial_population: float = 5_000_000,
    population_growth_rate: float = 0.01,

    initial_income: float = 36_203.15,
    income_growth_rate: float = 0.014,

    initial_inflation_index: float = 1.0,
    inflation_rate: float = 0.017,

    initial_redistribution_factor: float = 7.786169e-5,
    redistribution_rate: float = 0.0,

    # income pdf grid
    income_x_max_mult: float = 10.0,
    income_nx: int = 400,

    # production / demand conversion
    harvest_fraction: float = 1.0,
    calories_per_unit: float = 255_000,
    calorie_per_person: float = 700_000,

    # land area
    total_land_area: float = 560_000,

    # GLOBAL defaults
    E_H_default: float = 1.6,
    E_S_default: float = 1.28,

    # Baseline constants for food price equation
    Q_0: float = 5000.0,
    R_0: float = 120.0,
    I_0: float = 1.0,

    # Reinvestment parameters
    theta: float = 0.51,
    eta: float = 0.05,
    U_0: float | None = None,
    J_0: float | None = None,
    nu: float | None = None,


) -> SimulationResult:

    if len(lands) == 0:
        raise ValueError("simulate_multi_land: need at least one LandConfig")

    n_lands = len(lands)
    n_steps = int(round(float(n_points) * float(T_max)))
    t_eval = np.linspace(0.0, float(T_max), n_steps + 1)

    soils = np.zeros((n_lands, t_eval.size))
    degradations = np.zeros((n_lands, t_eval.size))
    productions = np.zeros((n_lands, t_eval.size))
    emissions = np.zeros((n_lands, t_eval.size))

    land_names: List[str] = []
    land_fractions: List[float] = []
    alphas: List[float] = []
    P_max_vec: List[float] = []

    # ---- land loops ----
    for i, land in enumerate(lands):
        land_names.append(land.name)
        land_fractions.append(float(land.land_fraction))
        alphas.append(float(land.alpha))
        P_max_vec.append(float(land.P_max))

        if land.scenario_name not in SCENARIOS:
            raise ValueError(f"Unknown scenario '{land.scenario_name}' for land {land.name}")
        if land.recovery_name not in RECOVERY_MODES:
            raise ValueError(f"Unknown recovery mode '{land.recovery_name}' for land {land.name}")

        alpha_fun = RECOVERY_MODES[land.recovery_name]

        if land.recovery_name == "Logistic alpha(S)":
            rp = dict(land.recovery_params or {})
            rp.setdefault("alpha_max", 0.25)
            rp.setdefault("rho", 50.0)
            rp.setdefault("S_T", 0.2)
        else:
            rp = {"alpha_const": land.alpha}

        D_fun = SCENARIOS[land.scenario_name]
        min_window = max(0.1, land.omega / 10.0)

        sol = solve_ivp(
            _soil_ode_single,
            method="RK45",
            t_span=(0.0, T_max),
            y0=[land.S0],
            t_eval=t_eval,
            max_step=min_window / 10.0,
            rtol=1e-8,
            atol=1e-10,
            args=(D_fun, land.deg_params, alpha_fun, rp, land.omega, land.tau, land.phase),
        )

        S_i = sol.y[0]
        soils[i, :] = S_i

        B_series = np.array(
            [B_pulse_train(tt, land.omega, land.tau, land.phase) for tt in t_eval],
            dtype=float
        )
        D_base_series = np.array([D_fun(tt, land.deg_params) for tt in t_eval], dtype=float)
        degradations[i, :] = D_base_series * B_series

        # production
        L_i = float(total_land_area) * float(land.land_fraction)

        F_i = float(land.deg_params.get("F", 1.0))
        xi = float(land.deg_params.get("xi", 10.0))
        psi = float(land.deg_params.get("psi", 0.5))
        hF = h_yield(F_i, xi, psi)

        Y_rate = float(land.P_max) * hF * B_series * S_i
        productions[i, :] = Y_rate * L_i

        # emissions / sequestration
        # Convention:
        #   cultivation phase: +E_H * L_i
        #   cover-crop phase: -E_S * L_i
        E_H = float(land.E_H) if land.E_H is not None else float(E_H_default)
        E_S = float(land.E_S) if land.E_S is not None else float(E_S_default)
        emissions[i, :] = (E_H * B_series - E_S * (1.0 - B_series)) * L_i

    land_fractions_arr = np.array(land_fractions, dtype=float)
    alphas_arr = np.array(alphas, dtype=float)
    P_max_arr = np.array(P_max_vec, dtype=float)

    total_production = productions.sum(axis=0)

    # ---- macro solve ----
    sol_all = solve_ivp(
        all_ODEs,
        method="RK45",
        t_span=(0.0, T_max),
        y0=initial_conditions(
            initial_population,
            initial_income,
            initial_inflation_index,
            initial_redistribution_factor
        ),
        t_eval=t_eval,
        args=(population_growth_rate, income_growth_rate, inflation_rate, redistribution_rate),
        rtol=1e-8,
        atol=1e-10,
    )

    population = sol_all.y[0]
    average_real_income = sol_all.y[1]
    inflation_index = sol_all.y[2]
    lam_series = sol_all.y[3]

    # enforce alpha = mu_real * lambda > 1
    mu_real = np.maximum(average_real_income, 1e-12)
    lam_min = (1.0 / mu_real) + 1e-12
    lam_series = np.maximum(lam_series, lam_min)
    alpha_series = mu_real * lam_series

    # ---- income distribution PDF over time ----
    x_max = float(income_x_max_mult) * float(np.max(mu_real))
    income_x = np.linspace(0.0, x_max, int(income_nx))
    income_pdf = np.zeros((t_eval.size, income_x.size), dtype=float)

    for k in range(t_eval.size):
        income_pdf[k, :] = gamma_pdf(
            income_x,
            alpha=float(alpha_series[k]),
            rate=float(lam_series[k])
        )

    k_shape = np.maximum(alpha_series.astype(float), 1e-8)
    rate = np.maximum(lam_series.astype(float), 1e-12)
    scale = 1.0 / rate

    # percentiles for inequality metrics
    x40 = gamma.ppf(0.40, a=k_shape, scale=scale)
    x90 = gamma.ppf(0.90, a=k_shape, scale=scale)

    # Palma ratio using weighted-income Gamma identities
    share_bottom40 = gamma.cdf(x40, a=k_shape + 1.0, scale=scale)
    share_top10 = 1.0 - gamma.cdf(x90, a=k_shape + 1.0, scale=scale)
    palma = share_top10 / np.maximum(share_bottom40, 1e-15)

    # Closed-form Gini for Gamma(shape=k, rate=lambda)
    log_gini = (
        gammaln(2.0 * k_shape + 1.0)
        - (2.0 * k_shape) * np.log(2.0)
        - 2.0 * gammaln(k_shape + 1.0)
    )
    gini = np.exp(log_gini)

    palma = np.where(np.isfinite(palma), palma, np.nan)
    gini = np.where(np.isfinite(gini), gini, np.nan)
    gini = np.clip(gini, 0.0, 1.0)

    # ---- food consumption / demand ----
    # Food consumption is taken to be calorie demand.
    food_consumption = population * float(calorie_per_person) 

    # ---- reinvestment boost ----
    # total_production is P_tilde(t): baseline production from the soil/land model.
    # total_production_real is P(t): realised production after reinvestment.
    # beta_q = float(Q_0) * float(R_0) * float(I_0) / 100
    beta_q = total_production[0]*(1.01) / (1000 * calorie_per_person / calories_per_unit)  # scale to current production for more dynamic response

    if U_0 is None:
        U_0 = 2.55e6 / theta

    if J_0 is None:
        J_0 = eta * theta * U_0 * Q_0

    if nu is None:
        nu = J_0 / 0.01

    J_investment_series = J_investment_func(
        pop=population,
        C=food_consumption / calories_per_unit,
        P_tilde=total_production,
        I=inflation_index,
        nu=nu,
        eta=eta,
        beta_q=beta_q,
        theta=theta,
    )

    # Debug system prints
    # print(f"J_investment_series: {J_investment_series}")
    # print(f"U_0: {U_0}")
    # print(f"Q_0: {Q_0}")
    # print(f"J_0: {J_0}")
    # print(f"nu: {nu} ")

    total_production_real = total_production * (1.0 + J_investment_series / float(nu))

    # ---- self-sufficiency ratio ----
    # Use instantaneous boosted production.
    # Important: this preserves the true t=0 value and makes results independent
    # of the plotting/time resolution n_points.
    calorie_production = total_production_real * float(calories_per_unit)

    self_sufficiency_ratio = 100.0 * (
        calorie_production / np.maximum(food_consumption, 1e-12)
    )

    # ---- harvest ----
    hf = float(np.clip(harvest_fraction, 0.0, 1.0))
    harvest_per_land = hf * productions
    # The reinvestment boost is applied only at total-system level, not per land.
    total_harvest = hf * total_production_real

    total_emissions = emissions.sum(axis=0)

    income_x20 = gamma.ppf(0.20, a=k_shape, scale=scale)

    # ---- food price index Q(t) ----
    # beta_q was already computed above for the reinvestment equation.
    food_price_index = 100 * beta_q / (
        np.maximum(self_sufficiency_ratio, 1e-12)
        * np.maximum(inflation_index, 1e-12)
    )

    # ---- food insecurity index Z(t) ----
    food_insecurity_index = 100 * food_price_index / np.maximum(income_x20, 1e-12)

    # ---- weighted soil ----
    if land_fractions_arr.sum() > 0:
        weighted_soil = (land_fractions_arr[:, None] * soils).sum(axis=0) / land_fractions_arr.sum()
    else:
        weighted_soil = soils.mean(axis=0)

    return SimulationResult(
        t=t_eval,
        soils=soils,
        degradations=degradations,
        productions=productions,
        total_production=total_production,
        total_production_real=total_production_real,
        J_investment=J_investment_series,
        weighted_soil=weighted_soil,
        land_names=land_names,
        land_fractions=land_fractions_arr,
        alphas=alphas_arr,
        P_max_vec=P_max_arr,

        population=population,
        food_consumption=food_consumption,
        self_sufficiency_ratio=self_sufficiency_ratio,
        average_real_income=average_real_income,

        inflation_index=inflation_index,
        redistribution_lambda=lam_series,

        palma_ratio=palma,
        gini_coefficient=gini,

        income_x20=income_x20,

        harvest_per_land=harvest_per_land,
        total_harvest=total_harvest,

        emissions_by_land=emissions,
        total_emissions=total_emissions,

        income_x=income_x,
        income_pdf=income_pdf,
        food_price_index=food_price_index,
        food_insecurity_index=food_insecurity_index,
    )