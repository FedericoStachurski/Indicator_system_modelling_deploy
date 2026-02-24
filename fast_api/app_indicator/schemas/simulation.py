from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, model_validator


class LandIn(BaseModel):
    name: str
    alpha: float
    S0: float
    scenario_name: str
    deg_params: Dict[str, Any]
    land_fraction: float
    P_max: float

    # per-land emissions factors (tCO2eq/(ha*yr))
    E_H: float = Field(
        default=1.68,
        ge=0.0,
        description="Intensive farming emission factor (tCO₂eq/(ha·yr))"
    )
    # allow negative if you want “net removal” under cover crops
    E_S: float = Field(
        default=1.28,
        description="Cover crop / fallow emission factor (tCO₂eq/(ha·yr))"
    )

    # cultivation pulse B(t)
    omega: int = Field(default=1, ge=1, description="Cycle length (years)")
    tau: int = Field(default=0, ge=0, description="Cover-crop duration (years), must be <= omega")
    phase: float = Field(default=0.0, ge=0.0, description="Phase shift (years)")

    recovery_name: str = Field(default="Constant alpha")
    recovery_params: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "ignore"}

    @model_validator(mode="after")
    def _check_tau_le_omega(self):
        if self.tau > self.omega:
            raise ValueError(f"tau ({self.tau}) must be <= omega ({self.omega})")
        return self


class SimRequest(BaseModel):
    T_max: float
    n_points: int

    population_growth_rate: float = 0.01
    income_growth_rate: float = 0.014
    inflation_rate: float = 0.017

    # NEW: total land area used to convert per-ha rates -> totals
    total_land_area: float = Field(default=560_000.0, gt=0.0, description="Total land area (hectares)")

    # Optional: global fallback emissions factors (used only if land E_H/E_S missing)
    E_H_default: float = Field(default=1.6, ge=0.0, description="Default cultivation emission factor (tCO₂eq/(ha·yr))")
    E_S_default: float = Field(default=1.28, description="Default cover emission factor (tCO₂eq/(ha·yr))")

    lands: list[LandIn]


class SimResponse(BaseModel):
    t: list[float]
    weighted_soil: list[float]
    soils: list[list[float]]
    alphas: list[float]
    land_names: list[str]

    # tonnes/yr
    total_production: list[float]
    production_by_land: list[list[float]]

    population: list[float]
    self_sufficiency_ratio: list[float]
    average_real_income: list[float]
    affordability_index: list[float]

    degradations: list[list[float]]

    # tonnes/yr
    total_harvest: Optional[list[float]] = None
    harvest_per_land: Optional[list[list[float]]] = None

    # optional econ outputs
    price: Optional[list[float]] = None
    affordability: Optional[list[float]] = None

    # emissions outputs (tCO2eq/yr)
    total_emissions: Optional[list[float]] = None
    emissions_by_land: Optional[list[list[float]]] = None