from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LandIn(BaseModel):
    name: str
    alpha: float
    S0: float
    scenario_name: str
    deg_params: Dict[str, Any] = Field(default_factory=dict)
    land_fraction: float
    P_max: float

    recovery_name: Optional[str] = "Constant alpha"
    recovery_params: Dict[str, Any] = Field(default_factory=dict)

    omega: int = 1
    tau: int = 0
    phase: float = 0.0

    E_H: Optional[float] = None
    E_S: Optional[float] = None


class SimRequest(BaseModel):
    lands: List[LandIn]

    T_max: float = 50.0
    n_points: int = 500

    # macro rates
    population_growth_rate: float = 0.01
    income_growth_rate: float = 0.005
    inflation_rate: float = 0.027

    # macro initial conditions
    initial_population: float = 5_000_000.0
    initial_income: float = 36_203.15
    initial_inflation_index: float = 1.0
    initial_redistribution_factor: float = 7.786169e-5
    redistribution_rate: float = -0.001

    # income pdf grid
    income_x_max_mult: float = 10.0
    income_nx: int = 400

    # land area
    total_land_area: float = 560_000.0

    # emissions defaults
    E_H_default: float = 1.5
    E_S_default: float = 1.17


class SimResponse(BaseModel):
    t: List[float]
    weighted_soil: List[float]
    soils: List[List[float]]
    land_names: List[str]
    alphas: List[float]

    total_production: List[float]
    production_by_land: List[List[float]]

    population: List[float]
    food_consumption: List[float]
    self_sufficiency_ratio: List[float]
    average_real_income: List[float]

    degradations: List[List[float]]

    total_harvest: Optional[List[float]] = None
    harvest_per_land: Optional[List[List[float]]] = None

    total_emissions: Optional[List[float]] = None
    emissions_by_land: Optional[List[List[float]]] = None

    inflation_index: Optional[List[float]] = None
    redistribution_lambda: Optional[List[float]] = None

    palma_ratio: Optional[List[float]] = None
    gini_coefficient: Optional[List[float]] = None

    income_x20: Optional[List[float]] = None

    income_x: Optional[List[float]] = None
    income_pdf: Optional[List[List[float]]] = None
    food_price_index: Optional[List[float]] = None
    food_security_index: Optional[List[float]] = None