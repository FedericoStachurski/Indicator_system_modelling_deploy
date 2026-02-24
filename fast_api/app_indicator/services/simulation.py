from __future__ import annotations

from soil_ode_UI.soil_model_core import LandConfig, simulate_multi_land
from ..schemas.simulation import SimRequest, SimResponse


def run_simulation(req: SimRequest) -> SimResponse:
    lands: list[LandConfig] = []

    for l in req.lands:
        d = l.model_dump()

        # Ensure recovery fields exist
        d["recovery_name"] = d.get("recovery_name") or "Constant alpha"
        d["recovery_params"] = d.get("recovery_params") or {}

        # Ensure B(t) params exist + are sensible
        omega = int(d.get("omega", 1) or 1)
        tau = int(d.get("tau", 0) or 0)
        phase = float(d.get("phase", 0.0) or 0.0)

        if omega < 1:
            omega = 1
        if tau < 0:
            tau = 0
        if tau > omega:
            tau = omega
        if phase < 0:
            phase = 0.0

        d["omega"] = omega
        d["tau"] = tau
        d["phase"] = phase

        # Ensure deg_params exists
        d["deg_params"] = d.get("deg_params") or {}

        lands.append(LandConfig(**d))

    res = simulate_multi_land(
        lands=lands,
        T_max=req.T_max,
        n_points=req.n_points,
        population_growth_rate=req.population_growth_rate,
        income_growth_rate=req.income_growth_rate,
        inflation_rate=req.inflation_rate,

        # land area
        total_land_area=req.total_land_area,

        # IMPORTANT: names must match soil_model_core.simulate_multi_land signature
        E_H_default=req.E_H_default,
        E_S_default=req.E_S_default,
    )

    return SimResponse(
        t=res.t.tolist(),
        weighted_soil=res.weighted_soil.tolist(),
        soils=res.soils.tolist(),
        land_names=res.land_names,
        alphas=res.alphas.tolist(),

        total_production=res.total_production.tolist(),
        production_by_land=res.productions.tolist(),

        population=res.population.tolist(),
        self_sufficiency_ratio=res.self_sufficiency_ratio.tolist(),
        average_real_income=res.average_real_income.tolist(),
        affordability_index=res.affordability_index.tolist(),

        degradations=res.degradations.tolist(),

        total_harvest=res.total_harvest.tolist() if res.total_harvest is not None else None,
        harvest_per_land=res.harvest_per_land.tolist() if res.harvest_per_land is not None else None,

        price=res.price.tolist() if res.price is not None else None,
        affordability=res.affordability.tolist() if res.affordability is not None else None,

        total_emissions=res.total_emissions.tolist() if res.total_emissions is not None else None,
        emissions_by_land=res.emissions_by_land.tolist() if res.emissions_by_land is not None else None,
    )