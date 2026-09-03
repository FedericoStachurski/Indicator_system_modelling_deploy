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

        # Farming mode: tau = fraction of year under regenerative farming
        tau = float(d.get("tau", 0.25) or 0.25)
        tau = min(max(tau, 0.05), 0.95)

        d["tau"] = tau

        # Remove old farming-mode parameters if still sent by frontend/schema
        d.pop("omega", None)
        d.pop("phase", None)

        # Ensure deg_params exists
        d["deg_params"] = d.get("deg_params") or {}

        lands.append(LandConfig(**d))

    # ---- Macro initial conditions + income PDF grid params ----
    initial_population = getattr(req, "initial_population", 5_000_000.0)
    initial_income = getattr(req, "initial_income", 36_203.15)
    initial_inflation_index = getattr(req, "initial_inflation_index", 1.0)
    initial_redistribution_factor = getattr(
        req,
        "initial_redistribution_factor",
        7.786169e-5,
    )
    redistribution_rate = getattr(req, "redistribution_rate", 0.0)

    income_x_max_mult = getattr(req, "income_x_max_mult", 10.0)
    income_nx = getattr(req, "income_nx", 400)

    # ---- Reinvestment parameters ----
    theta = getattr(req, "theta", 0.51)
    eta = getattr(req, "eta", 0.05)
    nu = getattr(req, "nu", 6.375e8)

    res = simulate_multi_land(
        lands=lands,
        T_max=req.T_max,
        n_points=req.n_points,

        # macro rates
        population_growth_rate=req.population_growth_rate,
        income_growth_rate=req.income_growth_rate,
        inflation_rate=req.inflation_rate,

        # macro initials
        initial_population=initial_population,
        initial_income=initial_income,
        initial_inflation_index=initial_inflation_index,
        initial_redistribution_factor=initial_redistribution_factor,
        redistribution_rate=redistribution_rate,

        # income pdf grid
        income_x_max_mult=income_x_max_mult,
        income_nx=income_nx,

        # production / demand conversion
        harvest_fraction=req.harvest_fraction,
        calories_per_unit=req.calories_per_unit,
        calorie_per_person=req.calorie_per_person,

        # land area
        total_land_area=req.total_land_area,

        # emissions defaults
        E_H_default=req.E_H_default,
        E_S_default=req.E_S_default,

        # reinvestment feedback parameters
        theta=theta,
        eta=eta,
        nu=nu,
    )

    return SimResponse(
        t=res.t.tolist(),

        # ---- soil state ----
        weighted_soil=res.weighted_soil.tolist(),
        soils=res.soils.tolist(),
        land_names=res.land_names,
        alphas=res.alphas.tolist(),
        degradations=res.degradations.tolist(),

        # ---- production ----
        # total_production is baseline soil-based production P~
        total_production=res.total_production.tolist(),
        production_by_land=res.productions.tolist(),

        # total_production_real is boosted production P after reinvestment
        J_investment=(
            res.J_investment.tolist()
            if res.J_investment is not None
            else None
        ),
        total_production_real=(
            res.total_production_real.tolist()
            if res.total_production_real is not None
            else None
        ),

        # ---- macro variables ----
        population=res.population.tolist(),
        food_consumption=res.food_consumption.tolist(),
        self_sufficiency_ratio=res.self_sufficiency_ratio.tolist(),
        average_real_income=res.average_real_income.tolist(),

        # ---- harvest ----
        total_harvest=(
            res.total_harvest.tolist()
            if res.total_harvest is not None
            else None
        ),
        harvest_per_land=(
            res.harvest_per_land.tolist()
            if res.harvest_per_land is not None
            else None
        ),

        # ---- emissions ----
        total_emissions=(
            res.total_emissions.tolist()
            if res.total_emissions is not None
            else None
        ),
        emissions_by_land=(
            res.emissions_by_land.tolist()
            if res.emissions_by_land is not None
            else None
        ),

        # ---- macro series exposed for plotting ----
        inflation_index=(
            res.inflation_index.tolist()
            if res.inflation_index is not None
            else None
        ),
        redistribution_lambda=(
            res.redistribution_lambda.tolist()
            if res.redistribution_lambda is not None
            else None
        ),

        # ---- inequality indices ----
        palma_ratio=(
            res.palma_ratio.tolist()
            if res.palma_ratio is not None
            else None
        ),
        gini_coefficient=(
            res.gini_coefficient.tolist()
            if res.gini_coefficient is not None
            else None
        ),
        income_x20=(
            res.income_x20.tolist()
            if res.income_x20 is not None
            else None
        ),

        # ---- income distribution ----
        income_x=(
            res.income_x.tolist()
            if res.income_x is not None
            else None
        ),
        income_pdf=(
            res.income_pdf.tolist()
            if res.income_pdf is not None
            else None
        ),

        # ---- food indicators ----
        food_price_index=(
            res.food_price_index.tolist()
            if res.food_price_index is not None
            else None
        ),
        food_insecurity_index=(
            res.food_insecurity_index.tolist()
            if res.food_insecurity_index is not None
            else None
        ),
    )