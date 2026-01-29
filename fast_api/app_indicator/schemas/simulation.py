from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LandIn(BaseModel):
    name: str
    alpha: float
    S0: float
    scenario_name: str
    deg_params: Dict
    land_fraction: float
    P_max: float
    recovery_name: str = Field(default="Constant alpha")
    recovery_params: Dict[str, Any] = Field(default_factory=dict)
    model_config = {"extra": "ignore"}  # ok to keep, but these fields MUST exist


class SimRequest(BaseModel):
    T_max: float
    n_points: int
    population_growth_rate: float = 0.01
    income_growth_rate: float = 0.014
    inflation_rate: float = 0.017
    lands: list[LandIn]


class SimResponse(BaseModel):
    t: list[float]
    weighted_soil: list[float]
    soils: list[list[float]]
    land_names: list[str]

    total_production: list[float]
    production_by_land: list[list[float]]

    population: list[float]
    self_sufficiency_ratio: list[float]
    average_real_income: list[float]
    affordability_index: list[float]
