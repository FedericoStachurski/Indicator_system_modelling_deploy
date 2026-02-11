from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class LandIn(BaseModel):
    name: str
    alpha: float
    S0: float
    scenario_name: str
    deg_params: Dict
    land_fraction: float
    P_max: float
    omega: int = Field(default=1, ge=1, description="Cycle length (years)")
    tau: int = Field(default=0, ge=0, description="Cover-crop duration (years), must be <= omega")
    phase: float = Field(default=0.0, ge=0.0, description="Phase shift (years)")

    recovery_name: str = Field(default="Constant alpha")
    recovery_params: Dict[str, Any] = Field(default_factory=dict)
    model_config = {"extra": "ignore"}  # ok to keep, but these fields MUST exist
    @model_validator(mode="after")
    def _check_tau_le_omega(self):
        if self.tau > self.omega:
            raise ValueError(f"tau ({self.tau}) must be <= omega ({self.omega})")
        return self



class SimRequest(BaseModel):
    T_max: float
    n_points: int
    population_growth_rate: float = 0.01 #TODO: make this a parameter of the model, with different growth rates for different scenarios (maybe?)
    income_growth_rate: float = 0.014 #TODO: make this a parameter of the model, with different growth rates for different scenarios (maybe?)
    inflation_rate: float = 0.017 #TODO: make this a parameter of the model, with different growth rates for different scenarios (maybe?)
    lands: list[LandIn]


class SimResponse(BaseModel):
    t: list[float]
    weighted_soil: list[float]
    soils: list[list[float]]
    alphas: list[float]
    land_names: list[str]

    total_production: list[float]
    production_by_land: list[list[float]]

    population: list[float]
    self_sufficiency_ratio: list[float]
    average_real_income: list[float]
    affordability_index: list[float]

    degradations: list[list[float]]
    total_harvest: list[float]
    price: list[float]
    affordability: list[float]
