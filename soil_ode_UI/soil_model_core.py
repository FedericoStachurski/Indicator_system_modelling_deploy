#!/usr/bin/env python3
"""
soil_model_core.py

Core ODE + analysis for the multi-land soil model.
No Streamlit or plotting here.
"""

from dataclasses import dataclass
from typing import Dict, List
import numpy as np
from scipy.integrate import solve_ivp


# ------------------------------------------------------------
# Degradation functions
# ------------------------------------------------------------

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


SCENARIOS = {
    "Constant degradation D": degradation_constant,
    "Phase-out at T_int": degradation_phaseout,
    "Natural to synthetic": degradation_natural_synthetic,
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
    alpha: float              # intrinsic recovery rate α_i
    S0: float                 # initial soil health S_i(0)
    scenario_name: str        # key into SCENARIOS
    deg_params: Dict          # parameters for D_i(t)
    land_fraction: float      # share of total land (0–1)
    P_max: float              # maximum yield scaling for this land


@dataclass
class SimulationResult:
    """
    Output container for a multi-land simulation.
    """
    t: np.ndarray                    # (n_times,)
    soils: np.ndarray                # (n_lands, n_times)
    degradations: np.ndarray         # (n_lands, n_times)
    productions: np.ndarray          # (n_lands, n_times)
    total_production: np.ndarray     # (n_times,)
    weighted_soil: np.ndarray        # (n_times,)
    land_names: List[str]            # list of land names
    land_fractions: np.ndarray       # (n_lands,)
    alphas: np.ndarray               # (n_lands,)
    P_max_vec: np.ndarray            # (n_lands,)

    # NEW: harvest, prices, affordability
    harvest_per_land: np.ndarray     # (n_lands, n_times)
    total_harvest: np.ndarray        # (n_times,)
    price: np.ndarray                # (n_times,)
    affordability: np.ndarray        # (n_times,)


# ------------------------------------------------------------
# Core solver
# ------------------------------------------------------------

def _soil_ode_single(
    t: float,
    S: np.ndarray,
    alpha: float,
    D_fun,
    deg_params: Dict
) -> float:
    """
    Single-land soil ODE:
    dS/dt = (alpha - D(t)) * S * (1 - S)
    """
    D_t = D_fun(t, deg_params)
    return (alpha - D_t) * S * (1.0 - S)


def simulate_multi_land(
    lands: List[LandConfig],
    T_max: float,
    n_points: int = 500,
    # ---- NEW econ parameters with defaults ----
    harvest_fraction: float = 1.0,
    price_demand_scale: float = 1.0,      # A in p = (A / Q)^(1/ε)
    price_demand_elasticity: float = 0.8, # ε > 0
    income: float = 1.0,                  # representative income
    calories_per_unit: float = 1.0,       # calories per unit harvest
    min_calories: float = 1.0,            # minimum calories per period
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

        D_fun = SCENARIOS[land.scenario_name]

        # Solve single-land soil ODE
        sol = solve_ivp(
            _soil_ode_single,
            t_span=(0.0, T_max),
            y0=[land.S0],
            t_eval=t_eval,
            args=(land.alpha, D_fun, land.deg_params),
        )

        S_i = sol.y[0]
        soils[i, :] = S_i

        # Degradation time series for this land
        degradations[i, :] = np.array([D_fun(tt, land.deg_params) for tt in t_eval])

        # Production: P_i(t) = P_max_i * S_i(t) * L_i
        productions[i, :] = land.P_max * S_i * land.land_fraction

    land_fractions_arr = np.array(land_fractions)
    alphas_arr = np.array(alphas)
    P_max_arr = np.array(P_max_vec)

    total_production = productions.sum(axis=0)

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
    )
