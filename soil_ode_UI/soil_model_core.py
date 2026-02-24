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
# Yield response (paper-aligned)
# ------------------------------------------------------------

def h_yield(F: float, xi: float, psi: float) -> float:
    """
    h(F) = max(0, (-F^2 + xi*F) * exp(-psi*F))
    """
    F = float(F)
    xi = float(xi)
    psi = float(psi)
    val = (-F*F + xi*F) * np.exp(-psi * F)
    return float(max(0.0, val))

# ------------------------------------------------------------
# Data structures
# ------------------------------------------------------------

@dataclass
class LandConfig:
    """
    Configuration for a single land / land owner.
    """
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

    # NEW: per-land emissions factors (tCO2eq/(ha*yr))
    # If None, the simulator falls back to global defaults.
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

    harvest_per_land: Optional[np.ndarray] = None
    total_harvest: Optional[np.ndarray] = None
    price: Optional[np.ndarray] = None
    affordability: Optional[np.ndarray] = None

    emissions_by_land: Optional[np.ndarray] = None   # (n_lands, n_times) tCO2eq/yr
    total_emissions: Optional[np.ndarray] = None     # (n_times,) tCO2eq/yr


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

    # paper-aligned: degradation off during cover
    D_t = D_base * B_t

    net = a - D_t
    if abs(net) < 1e-12:
        net = 0.0

    return np.array([net * S_val * (1.0 - S_val)])


def _population_ODE(P: float, population_growth_rate: float) -> float:
    return population_growth_rate * P

def _average_income_ODE(I: float, income_growth_rate: float) -> float:
    return income_growth_rate * I

def _inflation_index_ODE(F: float, inflation_rate: float) -> float:
    return inflation_rate * F

def all_ODEs(
    t: float,
    y: np.ndarray,
    population_growth_rate: float,
    income_growth_rate: float,
    inflation_rate: float,
) -> np.ndarray:
    P, I, F = y
    return np.array([
        _population_ODE(P, population_growth_rate),
        _average_income_ODE(I, income_growth_rate),
        _inflation_index_ODE(F, inflation_rate),
    ])

def initial_conditions(P0: float, I0: float, F0: float) -> np.ndarray:
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

    # economics
    harvest_fraction: float = 1.0,
    price_demand_scale: float = 1.0,
    price_demand_elasticity: float = 0.8,

    # affordability
    income: float = 1.0,
    calories_per_unit: float = 1_100_000,
    min_calories: float = 1.0,
    calorie_per_person: float = 700_000,

    # land area
    total_land_area: float = 560_000,  # hectares

    # GLOBAL defaults (used only if land.E_H/E_S not provided)
    E_H_default: float = 1.6,
    E_S_default: float = 1.28,
) -> SimulationResult:

    if len(lands) == 0:
        raise ValueError("simulate_multi_land: need at least one LandConfig")

    n_lands = len(lands)
    t_eval = np.linspace(0.0, T_max, n_points)

    soils = np.zeros((n_lands, n_points))
    degradations = np.zeros((n_lands, n_points))
    productions = np.zeros((n_lands, n_points))  # tonnes/yr
    emissions = np.zeros((n_lands, n_points))    # tCO2eq/yr

    land_names: List[str] = []
    land_fractions: List[float] = []
    alphas: List[float] = []
    P_max_vec: List[float] = []

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

        B_series = np.array([B_pulse_train(tt, land.omega, land.tau, land.phase) for tt in t_eval])
        D_base_series = np.array([D_fun(tt, land.deg_params) for tt in t_eval])
        degradations[i, :] = D_base_series * B_series

        # ---------- production (paper-aligned) ----------
        L_i = float(total_land_area) * float(land.land_fraction)  # hectares

        F_i = float(land.deg_params.get("F", 1.0))
        xi = float(land.deg_params.get("xi", 10.0))
        psi = float(land.deg_params.get("psi", 0.5))
        hF = h_yield(F_i, xi, psi)

        Y_rate = float(land.P_max) * hF * B_series * S_i  # tonne/(ha*yr)
        productions[i, :] = Y_rate * L_i                  # tonne/yr

        # ---------- emissions (per land factors) ----------
        E_H = float(land.E_H) if land.E_H is not None else float(E_H_default)
        E_S = float(land.E_S) if land.E_S is not None else float(E_S_default)

        emissions[i, :] = (E_H * B_series + E_S * (1.0 - B_series)) * L_i

    land_fractions_arr = np.array(land_fractions, dtype=float)
    alphas_arr = np.array(alphas, dtype=float)
    P_max_arr = np.array(P_max_vec, dtype=float)

    total_production = productions.sum(axis=0)

    sol_all = solve_ivp(
        all_ODEs,
        method="RK45",
        t_span=(0.0, T_max),
        y0=initial_conditions(initial_population, initial_income, initial_inflation_index),
        t_eval=t_eval,
        args=(population_growth_rate, income_growth_rate, inflation_rate),
    )

    population = sol_all.y[0]
    average_income = sol_all.y[1]
    inflation_index = sol_all.y[2]
    average_real_income = average_income / np.maximum(inflation_index, 1e-12)

    calorie_demand = population * float(calorie_per_person)
    calorie_production = total_production * float(calories_per_unit)
    self_sufficiency_ratio = 100.0 * (calorie_production / np.maximum(calorie_demand, 1e-12))

    if land_fractions_arr.sum() > 0:
        weighted_soil = (land_fractions_arr[:, None] * soils).sum(axis=0) / land_fractions_arr.sum()
    else:
        weighted_soil = soils.mean(axis=0)

    hf = float(np.clip(harvest_fraction, 0.0, 1.0))
    harvest_per_land = hf * productions
    total_harvest = harvest_per_land.sum(axis=0)

    tiny = 1e-8
    eps = float(price_demand_elasticity) if price_demand_elasticity > 0 else 0.8
    A = float(price_demand_scale)
    Q_eff = np.maximum(total_harvest, tiny)
    price = (A / Q_eff) ** (1.0 / eps)

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
        harvest_per_land=harvest_per_land,
        total_harvest=total_harvest,
        price=price,
        affordability=affordability,
        emissions_by_land=emissions,
        total_emissions=total_emissions,
        population=population,
        self_sufficiency_ratio=self_sufficiency_ratio,
        average_real_income=average_real_income,
        affordability_index=affordability_index,
    )