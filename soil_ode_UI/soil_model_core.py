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
) -> SimulationResult:
    """
    Simulate soil and production dynamics for multiple lands.

    Each land is solved independently (1D ODE per land) using the same time grid.
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
    )

