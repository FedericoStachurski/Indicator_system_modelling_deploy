import numpy as np
from typing import Dict
from scipy.integrate import solve_ivp
from scipy.stats import truncnorm
from scipy.stats import gamma
from scipy.special import gammaln  # stable log-gamma for analytic Gini
def g_fertiliser(F: float, zeta: float, D0: float) -> float:
    """g(F) = F^2 - 2*zeta*F + D0"""
    F = float(F)
    zeta = float(zeta)
    D0 = float(D0)
    return F * F - 2.0 * zeta * F + D0

def low_intervals_from_phase_row(phase_row: np.ndarray, tau: np.ndarray | float) -> np.ndarray:
    """Return absolute time intervals [start, end) where B is low for one parcel."""
    phase_row = np.asarray(phase_row, dtype=float)
    tau_values = np.asarray(tau, dtype=float)
    T = len(phase_row)

    if tau_values.ndim == 0:
        tau_values = np.full(T, float(tau_values))
    elif tau_values.size != T:
        raise ValueError(f"tau length {tau_values.size} does not match phase row length {T}")

    intervals = np.zeros((T, 2), dtype=float)
    for j in range(T):
        start = j + float(phase_row[j])
        end = start + float(tau_values[j])
        intervals[j, 0] = start
        intervals[j, 1] = end
    return intervals

def B_continuous_from_intervals(
    t: float,
    low_intervals: np.ndarray,
    high: float = 0.9,
    low: float = 0.1,
) -> float:
    """Evaluate B(t) using low intervals [start, end)."""
    t_val = float(t)
    starts = low_intervals[:, 0]
    ends = low_intervals[:, 1]
    idx = int(np.searchsorted(starts, t_val, side="right") - 1) # index of the last start time that is <= t_val
    if idx >= 0 and t_val < ends[idx]:
        return low
    return high

def alpha_logistic(S: float, alpha_max: float, rho: float, S_T: float) -> float:
    z = np.clip(-rho * (S - S_T), -160, 160)
    return alpha_max / (1.0 + np.exp(z))

def h_yield(F: float, xi: float, psi: float) -> float:
    """
    h(F) = max(0, (-F^2 + xi*F) * exp(-psi*F))
    """
    F = float(F)
    xi = float(xi)
    psi = float(psi)
    val = (-F * F + xi * F) * np.exp(-psi * F)
    return float(max(0.0, val))

def tau_matrix(N: int, T: int, mean_tau: float, sd_tau: float) -> np.ndarray:
    # To get the shifted and scaled distribution to be truncated at a and b
    a, b = 0.05, 0.95
    loc, scale = mean_tau, sd_tau
    a_transformed, b_transformed = (a - loc) / scale, (b - loc) / scale
    # Define the truncated normal distribution with the transformed parameters
    tau = truncnorm(a_transformed, b_transformed, loc=loc, scale=scale)
    # Generate tau matrix
    tau_mat = tau.rvs(size=(N, T))
    tau_mat = np.round(tau_mat, 2)   # approximate to two decimal places
    return tau_mat

def phi_matrix(N: int, T: int, tau: np.ndarray) -> np.ndarray:
    phi = np.zeros((N, T), dtype=float)
    for i in range(N):
        for j in range(T):
            phi[i, j] = np.random.uniform(0, 1 - tau[i, j])

    phi = np.round(phi, 2)   # approximate to two decimal places
    return phi

def phi_matrix_simple(N: int, T: int, tau: float) -> np.ndarray:
    phi = np.random.uniform(0, 1 - tau, size=(N, T))
    phi = np.round(phi, 2)   # approximate to two decimal places
    return phi

def set_initial_soil_quality(n_lands: int, S0_min: float, S0_max: float, random: bool = True) -> np.ndarray:
    if random:
        S0 = np.random.uniform(S0_min, S0_max, size=n_lands)
    else:
        S0 = np.linspace(S0_min, S0_max, n_lands)
    return S0

def compute_baseline_P_tilde(F_baseline: float, initial_soil_quality: np.ndarray, xi: float, psi: float, individual_land_size: float) -> float:
    h_F = h_yield(F_baseline, xi, psi)
    P_tilde = 0.0
    for S0 in initial_soil_quality:
        P_tilde += h_F * S0 * individual_land_size
    return P_tilde

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

def moving_average(series: np.ndarray, dt: float) -> np.ndarray:
    window_size = int(1.0 / dt)  # 1 year window
    series = np.asarray(series, dtype=float)
    moving_avg = np.zeros_like(series)
    moving_avg[0] = series[0]  # initial value remains unchanged
    for t_ind in range(1, len(series)):
        start_ind = max(0, t_ind - window_size + 1)
        moving_avg[t_ind] = np.mean(series[start_ind:t_ind + 1])
    return moving_avg

def annual_series(moving_avg_series: np.ndarray, dt: float) -> np.ndarray:
    T_max = (len(moving_avg_series) - 1) * dt
    annual_series = np.zeros(int(T_max) + 1)
    annual_series[0] = moving_avg_series[0]  # initial value
    for t_int in range(1, int(T_max)+1):
        t_ind = int(t_int / dt)
        annual_series[t_int] = moving_avg_series[t_ind]  # Use total production at the end of the year
    return annual_series

# ------------------------------------------------------------
# Core solver
# ------------------------------------------------------------

def _soil_ode_single(
    t: float,
    S: np.ndarray,
    zeta: float,
    D0: float,
    F_baseline: float,
    F_asymptotic: float,
    alpha_logistic,
    recovery_params: Dict,
    low_intervals: np.ndarray,
    high: float = 0.9,
    low: float = 0.1
) -> np.ndarray:
    S_val = float(S[0])
    alpha = float(alpha_logistic(S_val, **recovery_params))
    F_t = fertiliser_dynamics(F_baseline, F_asymptotic, t)
    g_F = float(g_fertiliser(F_t, zeta, D0))
    B_t = B_continuous_from_intervals(t, low_intervals, high=high, low=low)
    # Degradation active only during cultivated phase
    D_t = g_F * B_t
    net = alpha - D_t

    return np.array([net * S_val * (1.0 - S_val)], dtype=float)

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

def fertiliser_dynamics(F_baseline: float, F_asymptotic: float, t: float) -> float:
    # F(t) = F_a + e^{-|F_a-F_b|t} (F_b - F_a).
    F_baseline = float(F_baseline)
    F_asymptotic = float(F_asymptotic)
    fertiliser_series = F_asymptotic + np.exp(-abs(F_baseline - F_asymptotic) * t) * (F_baseline - F_asymptotic)
    return fertiliser_series

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

# ============================================================
# Public scenario API
# ============================================================

def run_scenario(
    mean_tau: float = 0.25,
    income_growth_rate: float = 0.014,
    redistribution_rate: float = -0.02,
    F_asymptotic: float = 1.0,
    F_baseline: float = 1.0,
    eta: float = 0.4,
    eta_b: float = 0.4,
    T_max: float = 80.0,
):
    """
    Run one scenario and return all outputs needed by
    scenario_runner_integrated.py.

    Parameters supplied by the runner:
        mean_tau
        income_growth_rate
        redistribution_rate
        F_asymptotic
        F_baseline
        eta
        eta_b
        T_max

    The remaining model parameters retain the values from the
    original scenario_analysis.py script.
    """

    # --------------------------------------------------------
    # Fixed model parameters
    # --------------------------------------------------------
    mean_tau = float(mean_tau)
    income_growth_rate = float(income_growth_rate)
    redistribution_rate = float(redistribution_rate)
    F_asymptotic = float(F_asymptotic)
    F_baseline = float(F_baseline)
    eta = float(eta)
    eta_b = float(eta_b)
    T_max = float(T_max)

    sd_tau = 0.02
    high = float(0.9)
    low = float(0.1)

    zeta = float(1.0)
    D0 = float(1.2)

    alpha_max = float(0.25)
    rho = float(50.0)
    S_T = float(0.2)

    xi = float(15.0)
    psi = float(0.5)

    E_H = float(1.5)
    E_S = float(1.17)

    initial_population = float(5_000_000)
    population_growth_rate = float(0.01)

    initial_income = float(36_203.15)

    initial_inflation_index = float(1.0)
    inflation_rate = float(0.0)

    initial_redistribution_factor = float(7.786169e-5)

    Total_land_area = float(550_000.0)

    calorie_per_person = float(700_000)
    calories_per_unit = float(2_100_000)

    Q_b = float(5000.0)
    theta = float(0.51)

    r_0 = float(0.3)

    U_0 = 2.55e6 / theta
    nu = eta_b * theta * U_0 * Q_b / r_0

    income_x_max = float(200000.0)
    income_nx = int(400)

    S0_min, S0_max = 0.2, 0.8

    recovery_params = {
        "alpha_max": alpha_max,
        "rho": rho,
        "S_T": S_T,
    }

    # --------------------------------------------------------
    # Time / land setup
    # --------------------------------------------------------
    n_lands = int(10)

    tau = tau_matrix(
        n_lands,
        int(T_max),
        mean_tau,
        sd_tau,
    )

    phi = phi_matrix(
        n_lands,
        int(T_max),
        tau,
    )

    dt = float(0.01)
    n_steps = int(np.ceil(T_max / dt))

    t_eval = np.linspace(
        0.0,
        T_max,
        n_steps + 1,
    )

    fertiliser_series = fertiliser_dynamics(
        F_baseline,
        F_asymptotic,
        t_eval,
    )

    random_initial_conditions_flag = False

    # --------------------------------------------------------
    # Soil dynamics
    # --------------------------------------------------------
    soils = np.zeros(
        (n_lands, t_eval.size)
    )

    initial_soil_quality = set_initial_soil_quality(
        n_lands,
        S0_min,
        S0_max,
        random=random_initial_conditions_flag,
    )

    low_intervals_collection = [
        low_intervals_from_phase_row(
            phi[i],
            tau[i],
        )
        for i in range(n_lands)
    ]

    for land_ind in range(n_lands):
        S0 = initial_soil_quality[land_ind]
        low_intervals = low_intervals_collection[land_ind]

        sol = solve_ivp(
            _soil_ode_single,
            method="RK45",
            t_span=(0.0, T_max),
            y0=[S0],
            t_eval=t_eval,
            rtol=1e-8,
            atol=1e-10,
            args=(
                zeta,
                D0,
                F_baseline,
                F_asymptotic,
                alpha_logistic,
                recovery_params,
                low_intervals,
                high,
                low,
            ),
        )

        S_i = sol.y[0]
        soils[land_ind, :] = S_i

    mean_soil_quality = np.mean(
        soils,
        axis=0,
    )

    P_tilde_baseline = compute_baseline_P_tilde(
        F_baseline,
        initial_soil_quality=initial_soil_quality,
        xi=xi,
        psi=psi,
        individual_land_size=Total_land_area / n_lands,
    )

    # --------------------------------------------------------
    # Production and emissions
    # --------------------------------------------------------
    production_series = np.zeros(
        (n_lands, n_steps + 1)
    )

    emissions_series = np.zeros(
        (n_lands, n_steps + 1)
    )

    individual_land_size = (
        Total_land_area / n_lands
    )

    for t_ind, t in enumerate(t_eval):
        low_intervals = low_intervals_collection[0]

        B_t = B_continuous_from_intervals(
            t,
            low_intervals,
            high,
            low,
        )

        S_t = soils[:, t_ind]

        h_F = h_yield(
            fertiliser_series[t_ind],
            xi,
            psi,
        )

        production_series[:, t_ind] = (
            h_F
            * B_t
            * S_t
            * individual_land_size
        )

        emissions_series[:, t_ind] = (
            E_H * B_t
            - E_S * (1.0 - B_t)
        ) * individual_land_size

    total_production = np.sum(
        production_series,
        axis=0,
    )

    total_emissions = np.sum(
        emissions_series,
        axis=0,
    )

    beta_q = (
        (1 + r_0)
        * P_tilde_baseline
        * Q_b
        * initial_inflation_index
        * calories_per_unit
        / (
            initial_population
            * calorie_per_person
        )
    )

    production_moving_avg = moving_average(
        total_production,
        dt,
    )

    emissions_moving_avg = moving_average(
        total_emissions,
        dt,
    )

    annual_production = annual_series(
        production_moving_avg,
        dt,
    )

    annual_emissions = annual_series(
        emissions_moving_avg,
        dt,
    )

    # --------------------------------------------------------
    # Macro ODE system
    # --------------------------------------------------------
    sol_all = solve_ivp(
        all_ODEs,
        method="RK45",
        t_span=(0.0, T_max),
        y0=initial_conditions(
            initial_population,
            initial_income,
            initial_inflation_index,
            initial_redistribution_factor,
        ),
        t_eval=t_eval,
        args=(
            population_growth_rate,
            income_growth_rate,
            inflation_rate,
            redistribution_rate,
        ),
        rtol=1e-8,
        atol=1e-10,
    )

    population = sol_all.y[0]
    average_real_income = sol_all.y[1]
    inflation_index = sol_all.y[2]
    lam_series = sol_all.y[3]

    food_consumption = (
        population
        * float(calorie_per_person)
    )

    consumption_tilde = (
        food_consumption
        / calories_per_unit
    )

    # --------------------------------------------------------
    # Reinvestment
    # --------------------------------------------------------
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

    J_investment_moving_avg = moving_average(
        J_investment_series,
        dt,
    )

    annual_J_investment = annual_series(
        J_investment_moving_avg,
        dt,
    )

    P_modified_moving_avg = (
        1
        + J_investment_moving_avg / nu
    ) * production_moving_avg

    P_modified_annual = (
        1
        + annual_J_investment / nu
    ) * annual_production

    # --------------------------------------------------------
    # Self-sufficiency
    # --------------------------------------------------------
    self_sufficiency_ratio_moving_avg = (
        100.0
        * (
            production_moving_avg
            / consumption_tilde
        )
    )

    ssr_annual = annual_series(
        self_sufficiency_ratio_moving_avg,
        dt,
    )

    # --------------------------------------------------------
    # Income distribution / inequality
    # --------------------------------------------------------
    income_x = np.linspace(
        0.0,
        income_x_max,
        income_nx,
    )

    income_pdf = np.zeros(
        (t_eval.size, income_x.size),
        dtype=float,
    )

    alpha_series = np.zeros(
        t_eval.size,
        dtype=float,
    )

    scale_series = np.zeros(
        t_eval.size,
        dtype=float,
    )

    for k in range(t_eval.size):
        alpha_par = (
            float(average_real_income[k])
            * float(lam_series[k])
        )

        scal_par = (
            1
            / float(lam_series[k])
        )

        alpha_series[k] = alpha_par
        scale_series[k] = scal_par

        income_pdf[k, :] = gamma.pdf(
            x=income_x,
            a=alpha_par,
            scale=scal_par,
        )

    x40 = gamma.ppf(
        0.40,
        a=alpha_series,
        scale=scale_series,
    )

    x90 = gamma.ppf(
        0.90,
        a=alpha_series,
        scale=scale_series,
    )

    share_bottom40 = gamma.cdf(
        x40,
        a=alpha_series + 1.0,
        scale=scale_series,
    )

    share_top10 = (
        1.0
        - gamma.cdf(
            x90,
            a=alpha_series + 1.0,
            scale=scale_series,
        )
    )

    palma = (
        share_top10
        / np.maximum(
            share_bottom40,
            1e-15,
        )
    )

    log_gini = (
        gammaln(
            2.0 * alpha_series + 1.0
        )
        - (2.0 * alpha_series)
        * np.log(2.0)
        - 2.0
        * gammaln(
            alpha_series + 1.0
        )
    )

    gini_retrieved = np.exp(
        log_gini
    )

    palma = np.where(
        np.isfinite(palma),
        palma,
        np.nan,
    )

    gini = np.where(
        np.isfinite(gini_retrieved),
        gini_retrieved,
        np.nan,
    )

    income_x20 = gamma.ppf(
        0.20,
        a=alpha_series,
        scale=scale_series,
    )

    # --------------------------------------------------------
    # Food price / food insecurity
    # --------------------------------------------------------
    food_price_index_moving_avg = (
        beta_q
        * consumption_tilde
        / P_modified_moving_avg
        * inflation_index
    )

    food_price_index_annual = annual_series(
        food_price_index_moving_avg,
        dt,
    )

    food_insecurity_index_moving_avg = (
        100
        * food_price_index_moving_avg
        / income_x20
    )

    food_insecurity_index_annual = annual_series(
        food_insecurity_index_moving_avg,
        dt,
    )

    # --------------------------------------------------------
    # Return API
    # --------------------------------------------------------
    return {
        "t_eval": t_eval,
        "mean_soil_quality": mean_soil_quality,
        "food_insecurity_index_annual": food_insecurity_index_annual,
        "food_price_index_annual": food_price_index_annual,
        "ssr_annual": ssr_annual,
        "palma": palma,
        "gini": gini,
        "P_modified_annual": P_modified_annual,
        "annual_J_investment": annual_J_investment,
        "average_real_income": average_real_income,
        "lam_series": lam_series,
        "food_consumption": food_consumption,
        "annual_emissions": annual_emissions,
        "income_x": income_x,
        "inflation_index": inflation_index,
        "fertiliser_series": fertiliser_series,
        "annual_production": annual_production,
    }