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
      Bi(t)=0 if t in [k \omega, k \omega + \tau), else 1

    Notes:
      - omega and tau are in years
      - tau must be < \omega
      - phase shifts the cycle start (in years)
    """
    omega = int(omega)
    tau = int(tau)
    if omega <= 0:
        return 1.0

    if t < 0:
        return 1.0  # pre-cycle, assume cash crops  
    
    cycle_time = (t - phase) % omega

    if cycle_time < tau - eps:
        return 0.0
    else:
        return 1.0

# ------------------------------------------------------------
# Degradation functions
# ------------------------------------------------------------

def g_fertiliser(F: float, zeta: float, D0: float) -> float:
    """
    g(F) = F^2 - 2*zeta*F + D0
    """
    F = float(F)
    zeta = float(zeta)
    D0 = float(D0)
    return F*F - 2.0*zeta*F + D0


def degradation_constant(t: float, params: Dict) -> float:
    return params["D_const"]


def degradation_phaseout(t: float, params: Dict) -> float:
    return params["D_high"] if t < params["T_int"] else params["D_low"]


def degradation_natural_synthetic(t: float, params: Dict) -> float:
    """
    Natural → synthetic degradation transition.
    D(t) = a0 * exp(-alpha * t) + a1 * (1 - exp(-beta * t))
    """
    alpha = params.get("alpha", 0.5)
    beta = params.get("beta", 0.5)
    a0 = params.get("a0", 1.0)
    a1 = params.get("a1", 1.0)
    x = alpha * t
    y = beta * t
    return a0 * np.exp(-x) + a1 * (1 - np.exp(-y))

def degradation_fertiliser_parabola(t: float, params: Dict) -> float:
    """
    Returns g(F) (time-constant). B(t) is applied outside (in the ODE).
    params expects:
      - F
      - zeta
      - D0
    """
    F = params.get("F", 1.0)
    zeta = params.get("zeta", 1.0)
    D0 = params.get("D0", 1.2)
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
# Data structures
# ------------------------------------------------------------

@dataclass
class LandConfig:
    """
    Configuration for a single land / land owner.
    """
    name: str
    alpha: float              # intrinsic recovery rate alpha_i
    S0: float                 # initial soil health S_i(0)
    scenario_name: str        # key into SCENARIOS
    deg_params: Dict          # parameters for D_i(t)
    land_fraction: float      # share of total land (0–1)
    P_max: float              # maximum yield scaling for this land
    recovery_name: str = "Constant alpha"   # key into RECOVERY_MODES
    recovery_params: Dict = None            # parameters for alpha(S)

    #Farming Mode parameters
    omega: int = 1          # cycle length (years)
    tau: int = 0            # cover-crop duration (years). tau=0 => always cash
    phase: float = 0.0      # optional phase shift (years)

    # Multipliers for cash vs cover
    D_cash_scale: float = 1.0     # scale D(t) when B=1
    D_cover_scale: float = 0.6    # scale D(t) when B=0 (less degradation)
    alpha_cash_scale: float = 1.0 # scale alpha when B=1
    alpha_cover_scale: float = 1.2# scale alpha when B=0 (more recovery)

    prod_cash_scale: float = 1.0  # scale production when B=1
    prod_cover_scale: float = 0.0 # typically 0 if cover/fallow

    



@dataclass
class SimulationResult:
    """
    Output container for a multi-land simulation.
    """
    t: np.ndarray                       # (n_times,)
    soils: np.ndarray                   # (n_lands, n_times)
    degradations: np.ndarray            # (n_lands, n_times)
    productions: np.ndarray             # (n_lands, n_times)
    total_production: np.ndarray        # (n_times,)
    weighted_soil: np.ndarray           # (n_times,)
    land_names: List[str]               # list of land names
    land_fractions: np.ndarray          # (n_lands,)
    alphas: np.ndarray                  # (n_lands,)
    P_max_vec: np.ndarray               # (n_lands,)
    population: np.ndarray              # (n_times,)
    self_sufficiency_ratio: np.ndarray  # (n_times,)
    average_real_income: np.ndarray     # (n_times,)
    affordability_index: np.ndarray     # (n_times,)
    omega: int = 1                      # years per cycle
    tau: int = 0                        # years of cover crop per cycle (tau=0 => always cultivated)
    phase: float = 0.0                  # phase shift for farming mode (in years)
    harvest_per_land: Optional[np.ndarray] = None
    total_harvest: Optional[np.ndarray] = None
    price: Optional[np.ndarray] = None
    affordability: Optional[np.ndarray] = None


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
) -> float:
    S_val = float(S[0])

    # Intrinsic recovery
    a = float(alpha_fun(S_val, recovery_params))

    # Baseline degradation from scenario (e.g. g(F))
    D_base = float(D_fun(t, deg_params))

    # Two-mode cultivation signal
    B_t = B_pulse_train(t, omega=omega, tau=tau, phase=phase)
    D_t = D_base * B_t
    net = a - D_t
    if abs(net) < 1e-12:
        net = 0.0
    # print(net * S_val * (1.0 - S_val), net, S_val, t)
    return np.array([net * S_val * (1.0 - S_val)])



def _population_ODE(
    P: float,
    population_growth_rate: float,
) -> float:
    """
    Population ODE
    dP/dt = population_growth_rate * P
    """
    P_t = population_growth_rate * P
    return P_t

def _average_income_ODE(
    I: float,
    income_growth_rate: float,
) -> float:
    """
    Average income ODE
    dI/dt = income_growth_rate * I
    """
    I_t = income_growth_rate * I
    return I_t

def _inflation_index_ODE(
    F: float,
    inflation_rate: float,
) -> float:
    """
    Inflation index ODE
    dF/dt = inflation_rate * F
    """
    F_t = inflation_rate * F
    return F_t

def all_ODEs(
    t: float,
    y: np.ndarray,
    population_growth_rate: float,
    income_growth_rate: float,
    inflation_rate: float,
) -> np.ndarray:
    """
    Combined ODE system for all variables.
    """
    P = y[0]
    I = y[1]
    F = y[2]
    dP_dt = _population_ODE(P, population_growth_rate)
    dI_dt = _average_income_ODE(I, income_growth_rate)
    dF_dt = _inflation_index_ODE(F, inflation_rate)  # example inflation rate
    return np.array([dP_dt, dI_dt, dF_dt])

def initial_conditions(
    P0: float,
    I0: float, 
    F0: float, 
) -> np.ndarray:
    """
    Initial conditions for all variables.
    """
    return np.array([P0, I0, F0])   


def simulate_multi_land(
    lands: List[LandConfig],
    T_max: float,
    n_points: int = 500,
    initial_population: float = 5_000_000,
    initial_income: float = 30_000,
    initial_inflation_index: float = 1.0,
    population_growth_rate: float = 0.01,
    income_growth_rate: float = 0.014,
    inflation_rate: float = 0.017,
    # ---- NEW econ parameters with defaults ----
    harvest_fraction: float = 1.0,        # fraction of production harvested
    price_demand_scale: float = 1.0,      # A in p = (A / Q)^(1/ε)
    price_demand_elasticity: float = 0.8, # ε > 0
    income: float = 1.0,                  # representative income
    calories_per_unit: float = 1_100_000,       # kcal per tonne
    min_calories: float = 1.0, 
    calorie_per_person: float = 700_000,   # kcal per person per year
    total_land_area: float = 560_000,    # total land area in hectares
) -> SimulationResult:
    """
    Simulate soil and production dynamics for multiple lands.

    Each land is solved independently (1D ODE per land) using the same time grid.

    NEW:
    - harvest_per_land, total_harvest
    - price from constant-elasticity inverse demand
    - affordability index from income vs minimum calorie cost
    """
    if len(lands) == 0:
        raise ValueError("simulate_multi_land: need at least one LandConfig")

    n_lands = len(lands)
    t_eval = np.linspace(0.0, T_max, n_points)

    soils = np.zeros((n_lands, n_points))
    degradations = np.zeros((n_lands, n_points))
    productions = np.zeros((n_lands, n_points))

    land_names: List[str] = []
    land_fractions: List[float] = []
    alphas: List[float] = []
    P_max_vec: List[float] = []

    for i, land in enumerate(lands):
        land_names.append(land.name)
        land_fractions.append(land.land_fraction)
        alphas.append(land.alpha)
        P_max_vec.append(land.P_max)

        if land.scenario_name not in SCENARIOS:
            raise ValueError(f"Unknown scenario '{land.scenario_name}' for land {land.name}")
        if land.recovery_name not in RECOVERY_MODES:
            raise ValueError(f"Unknown recovery mode '{land.recovery_name}' for land {land.name}")
        
        alpha_fun = RECOVERY_MODES[land.recovery_name]

        # If not provided, default based on mode
        if land.recovery_name == "Logistic alpha(S)":
            rp = dict(land.recovery_params or {})
            rp.setdefault("alpha_max", 0.25)
            rp.setdefault("rho", 50.0)
            rp.setdefault("S_T", 0.2)
        else:
            # constant mode uses LandConfig.alpha
            rp = {"alpha_const": land.alpha}

        D_fun = SCENARIOS[land.scenario_name]
        min_window = max(0.1, land.omega / 10.0)  # min step for ODE solver based on farming cycle
        # Solve single-land soil ODE
        sol = solve_ivp(
            _soil_ode_single,
            method = 'RK45',
            t_span=(0.0, T_max),
            y0=[land.S0],
            t_eval=t_eval,
            max_step=min_window / 10.0,   # or /20
            rtol=1e-8,
            atol=1e-10,
            args=(D_fun, land.deg_params, alpha_fun, rp, land.omega, land.tau, land.phase),
        )


        S_i = sol.y[0]
        soils[i, :] = S_i

        # Degradation time series for this land
        B_series = np.array([B_pulse_train(tt, land.omega, land.tau, land.phase) for tt in t_eval])
        D_base_series = np.array([D_fun(tt, land.deg_params) for tt in t_eval])
        degradations[i, :] = D_base_series * B_series


        # Production: P_i(t) = P_max_i * S_i(t) * L_i
        productions[i, :] = land.P_max * S_i * land.land_fraction * B_series


    land_fractions_arr = np.array(land_fractions)
    alphas_arr = np.array(alphas)
    P_max_arr = np.array(P_max_vec)

    total_production = total_land_area *productions.sum(axis=0)

    sol_all = solve_ivp(
        all_ODEs,
        method = 'RK45',
        t_span=(0.0, T_max),
        y0=initial_conditions(initial_population, initial_income, initial_inflation_index),
        t_eval=t_eval,
        args=(population_growth_rate, income_growth_rate, inflation_rate),
        # max_step=0.1,      # try 0.1 or 0.05 years
        # rtol=1e-7,
        # atol=1e-9,
    )

    population = sol_all.y[0]
    average_income = sol_all.y[1]
    inflation_index = sol_all.y[2]
    average_real_income = average_income / inflation_index
    calorie_demand = population * calorie_per_person
    calorie_production = total_production * calories_per_unit
    self_sufficiency_ratio = 100 * (calorie_production / calorie_demand)

    # Weighted soil (using land fractions) – guard against sum = 0
    if land_fractions_arr.sum() > 0:
        weighted_soil = (
            land_fractions_arr[:, None] * soils
        ).sum(axis=0) / land_fractions_arr.sum()
    else:
        weighted_soil = soils.mean(axis=0)

    # --------------------------------------------------------
    # NEW: Harvest, price, and affordability
    # --------------------------------------------------------

    # Clamp harvest_fraction in [0, 1]
    hf = float(np.clip(harvest_fraction, 0.0, 1.0))

    # Harvest per land and total
    harvest_per_land = hf * productions
    total_harvest = harvest_per_land.sum(axis=0)

    # Constant-elasticity inverse demand: p = (A / Q)^(1/ε)
    tiny = 1e-8
    eps = float(price_demand_elasticity) if price_demand_elasticity > 0 else 0.8
    A = float(price_demand_scale)

    Q_eff = np.maximum(total_harvest, tiny)
    price = (A / Q_eff) ** (1.0 / eps)

    # Affordability index: income / (cost of minimum calories)
    # price_per_calorie = price / calories_per_unit
    # C_min = price_per_calorie * min_calories
    cal_per_unit_eff = max(calories_per_unit, tiny)
    price_per_calorie = price / cal_per_unit_eff

    C_min = price_per_calorie * float(min_calories)
    C_min_eff = np.maximum(C_min, tiny)

    affordability = float(income) / C_min_eff
    affordability_index = 0.01 * (self_sufficiency_ratio * average_real_income) / initial_income
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
        harvest_per_land=harvest_per_land,
        total_harvest=total_harvest,
        price=price,
        affordability=affordability,
        population=population,
        self_sufficiency_ratio=self_sufficiency_ratio,
        average_real_income=average_real_income,
        affordability_index=affordability_index,
    )
