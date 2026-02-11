from __future__ import annotations

from soil_ode_UI.soil_model_core import LandConfig, simulate_multi_land
from ..schemas.simulation import SimRequest, SimResponse


def run_simulation(req: SimRequest) -> SimResponse:
    lands: list[LandConfig] = []

    for l in req.lands:
        d = l.model_dump()
        # print("LAND IN:", d.keys(), d.get("recovery_name"), d.get("recovery_params"))

        # Ensure recovery fields exist
        d["recovery_name"] = d.get("recovery_name") or "Constant alpha"
        d["recovery_params"] = d.get("recovery_params") or {}

        # Ensure B(t) params exist + are sensible
        # (schema should already provide defaults, but keep this defensive)
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

        # (Optional) Ensure deg_params exists
        d["deg_params"] = d.get("deg_params") or {}

        lands.append(LandConfig(**d))

    res = simulate_multi_land(
        lands=lands,
        T_max=req.T_max,
        n_points=req.n_points,
        population_growth_rate=req.population_growth_rate,
        income_growth_rate=req.income_growth_rate,
        inflation_rate=req.inflation_rate,
    )

    return SimResponse(
        t=res.t.tolist(),
        weighted_soil=res.weighted_soil.tolist(),
        soils=res.soils.tolist(),
        land_names=res.land_names,
        alphas=res.alphas.tolist(),

        total_production=res.total_production.tolist(),
        production_by_land=(res.productions * 560_000).tolist(),  # tonnes

        population=res.population.tolist(),
        self_sufficiency_ratio=res.self_sufficiency_ratio.tolist(),
        average_real_income=res.average_real_income.tolist(),
        affordability_index=res.affordability_index.tolist(),

        #Make sure these fields exist in SimResponse schema too
        degradations=res.degradations.tolist(),
        total_harvest=(res.total_harvest * 560_000).tolist(),  # tonnes
        price=res.price.tolist(),
        affordability=res.affordability.tolist(),
    )

