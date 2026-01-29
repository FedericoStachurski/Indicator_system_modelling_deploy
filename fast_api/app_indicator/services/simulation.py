from __future__ import annotations

from soil_ode_UI.soil_model_core import LandConfig, simulate_multi_land
from ..schemas.simulation import SimRequest, SimResponse



def run_simulation(req: SimRequest) -> SimResponse:
    lands = []
    for l in req.lands:
        d = l.model_dump()
        print("LAND IN:", d.keys(), d.get("recovery_name"), d.get("recovery_params"))


        # ensure recovery fields exist
        recovery_name = d.get("recovery_name", "Constant alpha")
        recovery_params = d.get("recovery_params") or {}

        d["recovery_name"] = recovery_name
        d["recovery_params"] = recovery_params

        lands.append(LandConfig(**d))


    res = simulate_multi_land(
        lands=lands,
        T_max=req.T_max,
        n_points=req.n_points,
        population_growth_rate=req.population_growth_rate,
        income_growth_rate=req.income_growth_rate,
        inflation_rate=req.inflation_rate,
    )

    # NOTE: you had duplicates in your return dict (population/SSR/income/aff repeated).
    # This returns each field once.
    return SimResponse(
        t=res.t.tolist(),
        weighted_soil=res.weighted_soil.tolist(),
        soils=res.soils.tolist(),
        land_names=res.land_names,

        total_production=res.total_production.tolist(),
        production_by_land=(res.productions * 560_000).tolist(),  # scale back to tonnes

        population=res.population.tolist(),
        self_sufficiency_ratio=res.self_sufficiency_ratio.tolist(),
        average_real_income=res.average_real_income.tolist(),
        affordability_index=res.affordability_index.tolist(),

        degradations=res.degradations.tolist(),
        total_harvest=(res.total_harvest * 560_000).tolist(),   # optional scaling if you want “tonnes”
        price=res.price.tolist(),
        affordability=res.affordability.tolist(),
    )
