#!/usr/bin/env python3
"""
soil_model_core.py

Core ODE + analysis for the multi-land soil model.
No Streamlit or plotting here.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
from scipy.integrate import solve_ivp
from scipy.stats import gamma
from scipy.special import gammaln  # stable log-gamma for analytic Gini


# ------------------------------------------------------------
# Farming Modes
# ------------------------------------------------------------

def B_pulse_train(t: float, omega: int, tau: int = 1, phase: float = 0.0, eps: float = 1e-10) -> float:
    """
    Pulse train for farming mode (cash crops vs cover crops).

    B(t) in {0,1}
      - B(t) = 0 during cover-crop window of length tau at start of each cycle
      - B(t) = 1 otherwise (cash crops)

    Matches:
      Bi(t)=0 if t in [k*omega, k*omega + tau), else 1
    """
    omega = int(omega)
    tau = int(tau)
    if omega <= 0:
        return 1.0
    if t < 0:
        return 1.0  # pre-cycle, assume cash crops

    cycle_time = (t - phase) % omega
    return 0.0 if (cycle_time < tau - eps) else 1.0


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
    Natural → synthetic degradation transition.
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
    E_H: Optional[float] = None
    E_S: Optional[float] = None


@dataclass
class SimulationResult:
    t: np.ndarray
    soils: np.ndarray
    degradations: np.ndarray

    productions: np.ndarray              # (n_lands, n_times) tonnes/yr
    total_production: np.ndarray         # (n_times,) tonnes/yr
    weighted_soil: np.ndarray

    land_names: List[str]
    land_fractions: np.ndarray
    alphas: np.ndarray
    P_max_vec: np.ndarray

    population: np.ndarray
    self_sufficiency_ratio: np.ndarray
    average_real_income: np.ndarray
    affordability_index: np.ndarray

    # --- macro series you want to plot in the app ---
    inflation_index: Optional[np.ndarray] = None        # I(t)
    average_nominal_income: Optional[np.ndarray] = None # μ_nom(t)
    redistribution_lambda: Optional[np.ndarray] = None  # λ(t)

    # --- inequality indices ---
    palma_ratio: Optional[np.ndarray] = None            # R(t)
    gini_coefficient: Optional[np.ndarray] = None       # G(t)

    # --- NEW: food price + food security ---
    food_price_index: Optional[np.ndarray] = None       # Q(t) £/yr (real)
    income_x20: Optional[np.ndarray] = None             # x20(t) £/yr
    food_security_index: Optional[np.ndarray] = None    # Z(t) = Q/x20

    harvest_per_land: Optional[np.ndarray] = None
    total_harvest: Optional[np.ndarray] = None
    price: Optional[np.ndarray] = None
    affordability: Optional[np.ndarray] = None

    emissions_by_land: Optional[np.ndarray] = None   # (n_lands, n_times) tCO2eq/yr
    total_emissions: Optional[np.ndarray] = None     # (n_times,) tCO2eq/yr

    # --- income distribution outputs ---
    income_x: Optional[np.ndarray] = None                # (n_x,)
    income_pdf: Optional[np.ndarray] = None              # (n_times, n_x)


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

    # degradation off during cover-crop phase
    D_t = D_base * B_t

    net = a - D_t
    if abs(net) < 1e-12:
        net = 0.0

    return np.array([net * S_val * (1.0 - S_val)], dtype=float)


# --- Macro ODEs ---

def _population_ODE(P: float, population_growth_rate: float) -> float:
    return population_growth_rate * P


def _inflation_index_ODE(I: float, inflation_rate: float) -> float:
    return inflation_rate * I


def _average_income_ODE(mu_nom: float, income_growth_rate: float) -> float:
    return income_growth_rate * mu_nom


def _redistribution_factor_ODE(lam: float, redistribution_rate: float) -> float:
    return redistribution_rate * lam


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
      y = [P, mu_nominal, inflation_index, lambda]
    """
    P, mu_nom, infl, lam = y

    dP = _population_ODE(P, population_growth_rate)
    dmu = _average_income_ODE(mu_nom, income_growth_rate)
    dinfl = _inflation_index_ODE(infl, inflation_rate)
    dlam = _redistribution_factor_ODE(lam, redistribution_rate)

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

    # economics
    harvest_fraction: float = 1.0,
    price_demand_scale: float = 1.0,
    price_demand_elasticity: float = 0.8,

    # affordability (your older index — unchanged)
    income: float = 1.0,
    calories_per_unit: float = 1_100_000,
    min_calories: float = 1.0,
    calorie_per_person: float = 700_000,

    # land area
    total_land_area: float = 560_000,

    # GLOBAL defaults
    E_H_default: float = 1.6,
    E_S_default: float = 1.28,
) -> SimulationResult:

    if len(lands) == 0:
        raise ValueError("simulate_multi_land: need at least one LandConfig")

    n_lands = len(lands)
    t_eval = np.linspace(0.0, T_max, int(n_points))

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

        B_series = np.array([B_pulse_train(tt, land.omega, land.tau, land.phase) for tt in t_eval], dtype=float)
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

        # emissions
        E_H = float(land.E_H) if land.E_H is not None else float(E_H_default)
        E_S = float(land.E_S) if land.E_S is not None else float(E_S_default)
        emissions[i, :] = (E_H * B_series + E_S * (1.0 - B_series)) * L_i

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
    mu_nominal = sol_all.y[1]
    inflation_index = sol_all.y[2]
    lam_series = sol_all.y[3]

    average_real_income = mu_nominal / np.maximum(inflation_index, 1e-12)

    # ---- enforce alpha = mu_real*lambda > 1 ----
    mu_real = np.maximum(average_real_income, 1e-12)
    lam_min = (1.0 / mu_real) + 1e-12
    lam_series = np.maximum(lam_series, lam_min)
    alpha_series = mu_real * lam_series

    # ---- income distribution PDF over time (kept for PDF plot) ----
    x_max = float(income_x_max_mult) * float(np.max(mu_real))
    income_x = np.linspace(0.0, x_max, int(income_nx))
    income_pdf = np.zeros((t_eval.size, income_x.size), dtype=float)
    for k in range(t_eval.size):
        income_pdf[k, :] = gamma_pdf(income_x, alpha=float(alpha_series[k]), rate=float(lam_series[k]))

    k_shape = np.maximum(alpha_series.astype(float), 1e-8)
    rate = np.maximum(lam_series.astype(float), 1e-12)
    scale = 1.0 / rate

    x40 = gamma.ppf(0.40, a=k_shape, scale=scale)
    x90 = gamma.ppf(0.90, a=k_shape, scale=scale)

    share_bottom40 = gamma.cdf(x40, a=k_shape + 1.0, scale=scale)
    share_top10 = 1.0 - gamma.cdf(x90, a=k_shape + 1.0, scale=scale)

    palma = share_top10 / np.maximum(share_bottom40, 1e-15)

    log_gini = (
        gammaln(2.0 * k_shape + 1.0)
        - (2.0 * k_shape) * np.log(2.0)
        - 2.0 * gammaln(k_shape + 1.0)
    )
    gini = np.exp(log_gini)

    palma = np.where(np.isfinite(palma), palma, np.nan)
    gini = np.where(np.isfinite(gini), gini, np.nan)
    gini = np.clip(gini, 0.0, 1.0)

    # ---- self sufficiency ratio ----
    calorie_demand = population * float(calorie_per_person)
    calorie_production = total_production * float(calories_per_unit)
    self_sufficiency_ratio = 100.0 * (calorie_production / np.maximum(calorie_demand, 1e-12))  # %

    # ---- affordability index (older version, unchanged) ---
    Q0 = 5_000.0
    I0 = 1.0
    SSR0 = 100.0
    betaQ = Q0 * SSR0 * I0
    
    denom_Q = np.maximum(self_sufficiency_ratio * inflation_index, 1e-12)
    food_price_index = betaQ / denom_Q  # £/yr (real)
    food_price_index = np.clip(food_price_index, 0.0, 50_000.0) #TODO CHANGE this NOT CORRECT

    income_x20 = gamma.ppf(0.20, a=k_shape, scale=scale)  # £/yr
    food_security_index = food_price_index / np.maximum(income_x20, 1e-12)  # fraction of income
    food_security_index = np.clip(food_security_index, 0.0, 2.0)         #TODO CHANGE this NOT CORRECT

    # ---- weighted soil ----
    if land_fractions_arr.sum() > 0:
        weighted_soil = (land_fractions_arr[:, None] * soils).sum(axis=0) / land_fractions_arr.sum()
    else:
        weighted_soil = soils.mean(axis=0)

    # ---- harvest ----
    hf = float(np.clip(harvest_fraction, 0.0, 1.0))
    harvest_per_land = hf * productions
    total_harvest = harvest_per_land.sum(axis=0)

    # ---- price model (unchanged) ----
    tiny = 1e-8
    eps = float(price_demand_elasticity) if price_demand_elasticity > 0 else 0.8
    A = float(price_demand_scale)
    Q_eff = np.maximum(total_harvest, tiny)
    price = (A / Q_eff) ** (1.0 / eps)

    # ---- affordability model (unchanged) ----
    cal_per_unit_eff = max(float(calories_per_unit), tiny)
    price_per_calorie = price / cal_per_unit_eff
    C_min = price_per_calorie * float(min_calories)
    C_min_eff = np.maximum(C_min, tiny)

    income_used = average_real_income if float(income) == 1.0 else float(income)
    affordability = income_used / C_min_eff

    affordability_index = 0.01 * (self_sufficiency_ratio * average_real_income) / float(initial_income)

    total_emissions = emissions.sum(axis=0)

    return SimulationResult(
        t=t_eval,
        soils=soils,
        degradations=degradations,
        productions=productions,
        total_production=total_production,
        weighted_soil=weighted_soil,
        land_names=land_names,
        land_fractions=land_fractions_arr,
        alphas=alphas_arr,
        P_max_vec=P_max_arr,

        population=population,
        self_sufficiency_ratio=self_sufficiency_ratio,
        average_real_income=average_real_income,
        affordability_index=affordability_index,

        inflation_index=inflation_index,
        average_nominal_income=mu_nominal,
        redistribution_lambda=lam_series,

        palma_ratio=palma,
        gini_coefficient=gini,

        # NEW: food indices
        food_price_index=food_price_index,
        income_x20=income_x20,
        food_security_index=food_security_index,

        harvest_per_land=harvest_per_land,
        total_harvest=total_harvest,
        price=price,
        affordability=affordability,

        emissions_by_land=emissions,
        total_emissions=total_emissions,

        income_x=income_x,
        income_pdf=income_pdf,
    )