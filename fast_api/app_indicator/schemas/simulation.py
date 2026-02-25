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

    # macro rates
    population_growth_rate: float = 0.01
    income_growth_rate: float = 0.014
    inflation_rate: float = 0.017

    # macro initial conditions (income distribution)
    initial_population: float = Field(default=5_000_000.0, gt=0.0)
    initial_income: float = Field(default=36_203.15, gt=0.0)  # nominal mean income (£/yr)
    initial_inflation_index: float = Field(default=1.0, gt=0.0)
    initial_redistribution_factor: float = Field(default=7.786169e-5, gt=0.0)
    redistribution_rate: float = Field(default=0.0)

    # income PDF grid settings
    income_x_max_mult: float = Field(default=10.0, gt=0.0)
    income_nx: int = Field(default=400, ge=50, le=5000)

    # land area
    total_land_area: float = Field(default=560_000.0, gt=0.0, description="Total land area (hectares)")

    # global fallback emissions factors
    E_H_default: float = Field(default=1.6, ge=0.0)
    E_S_default: float = Field(default=1.28)

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

    # --- macro series exposed for plotting ---
    inflation_index: Optional[list[float]] = None
    average_nominal_income: Optional[list[float]] = None
    redistribution_lambda: Optional[list[float]] = None

    # --- inequality indices ---
    palma_ratio: Optional[list[float]] = None
    gini_coefficient: Optional[list[float]] = None

    # --- food price + food security ---
    food_price_index: Optional[list[float]] = None      # Q(t) £/yr (real)
    income_x20: Optional[list[float]] = None            # x20(t) £/yr
    food_security_index: Optional[list[float]] = None   # Z(t) = Q(t)/x20(t)

    # --- income distribution ---
    income_x: Optional[list[float]] = None
    income_pdf: Optional[list[list[float]]] = None