from pathlib import Path

import matplotlib
import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import gamma

from static_scenario_runs import scenario_analysis


# ============================================================
# Plot configuration
# ============================================================

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = [
    "Helvetica",
    "Arial",
    "DejaVu Sans",
]

# Do not require an external LaTeX installation
plt.rcParams["text.usetex"] = False

plt.rcParams["font.size"] = 9
plt.rcParams["axes.titlesize"] = 9
plt.rcParams["axes.labelsize"] = 9
plt.rcParams["xtick.labelsize"] = 7
plt.rcParams["ytick.labelsize"] = 7

BASELINE_LINEWIDTH = 1.7


# ============================================================
# Paths
# ============================================================
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCENARIOS_DIR = ROOT / "scenarios"

SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Scenario definitions
# ============================================================

F_BASELINE = 0.9
ETA_B = 0.4
T_MAX = 200.0


SCENARIOS = {
    "baseline_scenario": {
        "mean_tau": 0.3,
        "income_growth_rate": 0.002,
        "redistribution_rate": -0.005,
        "F_asymptotic": F_BASELINE,
        "F_baseline": F_BASELINE,
        "eta": 0.4,
        "eta_b": ETA_B,
        "T_max": T_MAX,
    },

    "sustainable_scenario": {
        "mean_tau": 0.5,
        "income_growth_rate": 0.001,
        "redistribution_rate": 0.005,
        "F_asymptotic": 0.8,
        "F_baseline": F_BASELINE,
        "eta": 0.4,
        "eta_b": ETA_B,
        "T_max": T_MAX,
    },

    "equitable_scenario": {
        "mean_tau": 0.3,
        "income_growth_rate": 0.001,
        "redistribution_rate": 0.020,
        "F_asymptotic": 0.8,
        "F_baseline": F_BASELINE,
        "eta": 0.4,
        "eta_b": ETA_B,
        "T_max": T_MAX,
    },

    "industrial_scenario": {
        "mean_tau": 0.25,
        "income_growth_rate": 0.005,
        "redistribution_rate": -0.020,
        "F_asymptotic": 1.25,
        "F_baseline": F_BASELINE,
        "eta": 0.4,
        "eta_b": ETA_B,
        "T_max": T_MAX,
    },

    "integrated_scenario": {
        "mean_tau": 0.4,
        "income_growth_rate": 0.002,
        "redistribution_rate": 0.010,
        "F_asymptotic": 1.2,
        "F_baseline": F_BASELINE,
        "eta": 0.5,
        "eta_b": ETA_B,
        "T_max": T_MAX,
    },
}


OUTPUT_VARIABLES = [
    "t_eval",
    "mean_soil_quality",
    "food_insecurity_index_annual",
    "food_price_index_annual",
    "ssr_annual",
    "palma",
    "gini",
    "P_modified_annual",
    "annual_J_investment",
    "average_real_income",
    "lam_series",
    "food_consumption",
    "annual_emissions",
    "income_x",
    "inflation_index",
    "fertiliser_series",
    "annual_production",
]


# ============================================================
# Scenario execution
# ============================================================

def run_scenario(params):
    return scenario_analysis.run_scenario(**params)


def run_named_scenario(name):
    if name not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {name}")

    print(f"Running scenario: {name}")

    results = scenario_analysis.run_scenario(
    **SCENARIOS[name]
    )

    results = add_annual_income_distributions(
        results
    )

    save_scenario_data(
        name,
        results,
    )

    return results


def save_dashboard_scenario(name, result, scenario_dir):
    output_path = scenario_dir / f"{name}.npz"

    payload = {
        # Common time axis
        "t": result.t,

        # Soil / degradation
        "soils": result.soils,
        "degradations": result.degradations,
        "weighted_soil": result.weighted_soil,

        # Production
        "production_by_land": result.productions,
        "total_production": result.total_production,
        "total_production_real": result.total_production_real,
        "J_investment": result.J_investment,

        # Land metadata
        "land_names": np.asarray(result.land_names, dtype=str),
        "land_fractions": result.land_fractions,

        # Macro variables
        "population": result.population,
        "food_consumption": result.food_consumption,
        "self_sufficiency_ratio": result.self_sufficiency_ratio,
        "average_real_income": result.average_real_income,
        "inflation_index": result.inflation_index,
        "redistribution_lambda": result.redistribution_lambda,

        # Inequality
        "palma_ratio": result.palma_ratio,
        "gini_coefficient": result.gini_coefficient,

        # Emissions
        "emissions_by_land": result.emissions_by_land,
        "total_emissions": result.total_emissions,

        # Income distribution
        "income_x": result.income_x,
        "income_pdf": result.income_pdf,

        # Affordability
        "food_price_index": result.food_price_index,
        "food_insecurity_index": result.food_insecurity_index,

        # Optional
        "total_harvest": result.total_harvest,
    }

    np.savez_compressed(
        output_path,
        **payload,
    )

    print(f"Saved official scenario: {output_path}")

# ============================================================
# Plot helpers
# ============================================================

def series_max(*series):
    """
    Return the largest finite value across multiple arrays.
    """
    return max(
        np.nanmax(np.asarray(values, dtype=float))
        for values in series
    )


def save_plot(filename):
    path = SCENARIOS_DIR / filename

    plt.tight_layout()
    plt.savefig(
        path,
        bbox_inches="tight",
    )

    print(f"Saved plot: {path}")

    plt.show()


def annual_time():
    return np.arange(int(T_MAX) + 1)


def save_scenario_data(name, results):
    """
    Save numerical scenario results as a compressed NumPy file.
    """

    output_path = SCENARIOS_DIR / f"{name}.npz"

    arrays = {}

    for key, value in results.items():
        try:
            arrays[key] = np.asarray(value)
        except Exception:
            pass

    np.savez_compressed(
        output_path,
        **arrays,
    )

    print(f"Saved scenario data: {output_path}")


def add_annual_income_distributions(results):
    """
    Precompute the income distribution once per year.

    Adds:
        income_pdf_time       shape (n_years,)
        income_pdf            shape (n_years, n_income_bins)
        income_alpha_annual   shape (n_years,)
        income_scale_annual   shape (n_years,)
    """

    t = np.asarray(
        results["t_eval"],
        dtype=float,
    )

    income_x = np.asarray(
        results["income_x"],
        dtype=float,
    )

    average_income = np.asarray(
        results["average_real_income"],
        dtype=float,
    )

    lam = np.asarray(
        results["lam_series"],
        dtype=float,
    )


    # --------------------------------------------------------
    # Annual time points:
    # 0, 1, 2, ..., T_max
    # --------------------------------------------------------

    years = np.arange(
        0,
        int(np.floor(t[-1])) + 1,
        dtype=float,
    )


    # Find the closest model timestep corresponding
    # to each whole year
    indices = np.searchsorted(
        t,
        years,
    )

    indices = np.clip(
        indices,
        0,
        len(t) - 1,
    )


    annual_income = average_income[indices]

    annual_lambda = lam[indices]


    # Avoid division by zero
    annual_lambda = np.maximum(
        annual_lambda,
        1e-15,
    )


    # Gamma distribution parameters
    alpha = (
        annual_income
        *
        annual_lambda
    )

    scale = (
        1.0
        /
        annual_lambda
    )


    # --------------------------------------------------------
    # Build PDF tensor
    #
    # alpha[:, None]  -> (years, 1)
    # income_x[None,:] -> (1, income bins)
    #
    # result -> (years, income bins)
    # --------------------------------------------------------

    income_pdf = gamma.pdf(
        x=income_x[None, :],
        a=alpha[:, None],
        scale=scale[:, None],
    )


    results["income_pdf_time"] = years

    results["income_pdf"] = income_pdf

    # These are useful to keep as well:
    results["income_alpha_annual"] = alpha
    results["income_scale_annual"] = scale


    return results


# ============================================================
# Main
# ============================================================

def main():

    # --------------------------------------------------------
    # Run scenarios
    # --------------------------------------------------------

    baseline_results = run_named_scenario("baseline_scenario")
    sustainable_results = run_named_scenario("sustainable_scenario")
    industrial_results = run_named_scenario("industrial_scenario")
    equitable_results = run_named_scenario("equitable_scenario")
    integrated_results = run_named_scenario("integrated_scenario")

    time_array = baseline_results["t_eval"]
    yearly = annual_time()

    # ========================================================
    # Mean soil quality
    # ========================================================

    plt.figure(figsize=(2.8, 2.0), dpi=150)

    plt.plot(
        time_array,
        baseline_results["mean_soil_quality"],
        linewidth=BASELINE_LINEWIDTH,
        color="gray",
        label="Baseline Scenario",
    )

    plt.plot(
        time_array,
        sustainable_results["mean_soil_quality"],
        linewidth=BASELINE_LINEWIDTH,
        color="green",
        label="Sustainable Scenario",
    )

    plt.plot(
        time_array,
        industrial_results["mean_soil_quality"],
        linewidth=BASELINE_LINEWIDTH,
        color="red",
        label="Industrial Scenario",
    )

    plt.plot(
        time_array,
        equitable_results["mean_soil_quality"],
        linewidth=BASELINE_LINEWIDTH,
        color="blue",
        label="Equitable Scenario",
    )

    plt.plot(
        time_array,
        integrated_results["mean_soil_quality"],
        linewidth=BASELINE_LINEWIDTH,
        color="orange",
        linestyle="--",
        label="Strategic Scenario",
    )

    plt.xlabel("Time [yr]")
    plt.ylabel("Mean Soil Quality Index")

    plt.xlim(1, T_MAX)

    plt.ylim(
        0,
        1.1
        * series_max(
            baseline_results["mean_soil_quality"],
            sustainable_results["mean_soil_quality"],
            industrial_results["mean_soil_quality"],
            equitable_results["mean_soil_quality"],
            integrated_results["mean_soil_quality"],
        ),
    )

    save_plot("mean_soil_quality_plot_integrated.png")

    # ========================================================
    # Legend
    # ========================================================

    legend_handles = [
        mlines.Line2D([], [], color="gray", lw=1.7, label="Baseline"),
        mlines.Line2D([], [], color="green", lw=1.7, label="Sustainable"),
        mlines.Line2D([], [], color="red", lw=1.7, label="Industrial"),
        mlines.Line2D([], [], color="blue", lw=1.7, label="Equitable"),
        mlines.Line2D([], [], color="orange", lw=1.7, label="Integrated"),
    ]

    fig, ax = plt.subplots(figsize=(5.3, 0.2), dpi=150)

    ax.axis("off")

    ax.legend(
        handles=legend_handles,
        loc="center",
        ncol=5,
        frameon=False,
        fontsize=8,
    )

    save_plot("legend_plot_integrated.png")

    # ========================================================
    # Fertiliser
    # ========================================================

    plt.figure(figsize=(2.8, 2.0), dpi=150)

    plt.plot(
        time_array,
        baseline_results["fertiliser_series"],
        linewidth=BASELINE_LINEWIDTH,
        color="gray",
    )

    plt.plot(
        time_array,
        sustainable_results["fertiliser_series"],
        linewidth=BASELINE_LINEWIDTH,
        color="green",
    )

    plt.plot(
        time_array,
        industrial_results["fertiliser_series"],
        linewidth=BASELINE_LINEWIDTH,
        color="red",
    )

    plt.plot(
        time_array,
        equitable_results["fertiliser_series"],
        linewidth=BASELINE_LINEWIDTH,
        color="blue",
    )

    plt.plot(
        time_array,
        integrated_results["fertiliser_series"],
        linewidth=BASELINE_LINEWIDTH,
        color="orange",
        linestyle="--",
    )

    plt.xlabel("Time [yr]")
    plt.ylabel(r"Fertiliser Application Rate [M/ha]")
    plt.xlim(1, T_MAX)

    plt.tight_layout()
    plt.show()

    # ========================================================
    # Annual production
    # ========================================================

    plt.figure(figsize=(2.8, 2.0), dpi=150)

    plt.plot(
        yearly,
        baseline_results["annual_production"] / 1e6,
        linewidth=BASELINE_LINEWIDTH,
        color="gray",
    )

    plt.plot(
        yearly,
        sustainable_results["annual_production"] / 1e6,
        linewidth=BASELINE_LINEWIDTH,
        color="green",
    )

    plt.plot(
        yearly,
        industrial_results["annual_production"] / 1e6,
        linewidth=BASELINE_LINEWIDTH,
        color="red",
    )

    plt.plot(
        yearly,
        equitable_results["annual_production"] / 1e6,
        linewidth=BASELINE_LINEWIDTH,
        color="blue",
    )

    plt.plot(
        yearly,
        integrated_results["annual_production"] / 1e6,
        linewidth=BASELINE_LINEWIDTH,
        color="orange",
    )

    plt.xlabel("Time [yr]")
    plt.ylabel(r"Domestic Production [Mt]")
    plt.xlim(1, T_MAX)

    plt.ylim(
        0,
        1.1
        * series_max(
            baseline_results["annual_production"][1:] / 1e6,
            sustainable_results["annual_production"][1:] / 1e6,
            industrial_results["annual_production"][1:] / 1e6,
            equitable_results["annual_production"][1:] / 1e6,
            integrated_results["annual_production"][1:] / 1e6,
        ),
    )

    save_plot("annual_production_plot_integrated.png")

    # ========================================================
    # Food supply
    # ========================================================

    plt.figure(figsize=(2.8, 2.0), dpi=150)

    for results, colour in [
        (baseline_results, "gray"),
        (sustainable_results, "green"),
        (industrial_results, "red"),
        (equitable_results, "blue"),
        (integrated_results, "orange"),
    ]:
        plt.plot(
            yearly,
            results["P_modified_annual"] / 1e6,
            linewidth=BASELINE_LINEWIDTH,
            color=colour,
        )

    plt.xlabel("Time [yr]")
    plt.ylabel(r"Food Supply [Mt]")
    plt.xlim(1, T_MAX)

    plt.ylim(
        0,
        1.1
        * series_max(
            baseline_results["P_modified_annual"][1:] / 1e6,
            sustainable_results["P_modified_annual"][1:] / 1e6,
            industrial_results["P_modified_annual"][1:] / 1e6,
            equitable_results["P_modified_annual"][1:] / 1e6,
            integrated_results["P_modified_annual"][1:] / 1e6,
        ),
    )

    save_plot("food_supply_plot_integrated.png")

    # ========================================================
    # Annual emissions
    # ========================================================

    plt.figure(figsize=(2.8, 2.0), dpi=150)

    for results, colour in [
        (baseline_results, "gray"),
        (sustainable_results, "green"),
        (industrial_results, "red"),
        (equitable_results, "blue"),
        (integrated_results, "orange"),
    ]:
        plt.plot(
            yearly,
            results["annual_emissions"] / 1e6,
            linewidth=BASELINE_LINEWIDTH,
            color=colour,
        )

    plt.xlabel("Time [yr]")
    plt.ylabel(r"Annual Emissions [Mt CO$_2$]")
    plt.xlim(1, T_MAX)

    plt.ylim(
        0,
        1.1
        * series_max(
            baseline_results["annual_emissions"][1:] / 1e6,
            sustainable_results["annual_emissions"][1:] / 1e6,
            industrial_results["annual_emissions"][1:] / 1e6,
            equitable_results["annual_emissions"][1:] / 1e6,
            integrated_results["annual_emissions"][1:] / 1e6,
        ),
    )

    save_plot("annual_emissions_plot_integrated.png")

    # ========================================================
    # Investment
    # ========================================================

    plt.figure(figsize=(2.8, 2.0), dpi=150)

    for results, colour in [
        (baseline_results, "gray"),
        (sustainable_results, "green"),
        (industrial_results, "red"),
        (equitable_results, "blue"),
        (integrated_results, "orange"),
    ]:
        plt.plot(
            yearly,
            results["annual_J_investment"] / 1e9,
            linewidth=BASELINE_LINEWIDTH,
            color=colour,
        )

    plt.xlabel("Time [yr]")
    plt.ylabel(r"Import investments [£bn]")
    plt.xlim(1, T_MAX)

    plt.ylim(
        0,
        1.1
        * series_max(
            baseline_results["annual_J_investment"][1:] / 1e9,
            sustainable_results["annual_J_investment"][1:] / 1e9,
            industrial_results["annual_J_investment"][1:] / 1e9,
            equitable_results["annual_J_investment"][1:] / 1e9,
            integrated_results["annual_J_investment"][1:] / 1e9,
        ),
    )

    save_plot("annual_J_investment_plot_integrated.png")

    # ========================================================
    # Self-sufficiency ratio
    # ========================================================

    plt.figure(figsize=(2.8, 2.0), dpi=150)

    for results, colour in [
        (baseline_results, "gray"),
        (sustainable_results, "green"),
        (industrial_results, "red"),
        (equitable_results, "blue"),
        (integrated_results, "orange"),
    ]:
        plt.plot(
            yearly,
            results["ssr_annual"],
            linewidth=BASELINE_LINEWIDTH,
            color=colour,
        )

    plt.xlabel("Time [yr]")
    plt.ylabel(r"Self-Sufficiency Ratio [\%]")
    plt.xlim(1, T_MAX)

    plt.ylim(
        0,
        1.1
        * series_max(
            baseline_results["ssr_annual"],
            sustainable_results["ssr_annual"],
            industrial_results["ssr_annual"],
            equitable_results["ssr_annual"],
            integrated_results["ssr_annual"],
        ),
    )

    save_plot("self_sufficiency_ratio_plot_integrated.png")

    # ========================================================
    # Food price
    # ========================================================

    plt.figure(figsize=(2.8, 2.0), dpi=150)

    for results, colour in [
        (baseline_results, "gray"),
        (sustainable_results, "green"),
        (industrial_results, "red"),
        (equitable_results, "blue"),
        (integrated_results, "orange"),
    ]:
        plt.plot(
            yearly,
            results["food_price_index_annual"] / 1e3,
            linewidth=BASELINE_LINEWIDTH,
            color=colour,
        )

    plt.xlabel("Time [yr]")
    plt.ylabel(r"Food Price Index [£k/yr]")
    plt.xlim(1, T_MAX)

    plt.ylim(
        0,
        1.1
        * series_max(
            baseline_results["food_price_index_annual"] / 1e3,
            sustainable_results["food_price_index_annual"] / 1e3,
            industrial_results["food_price_index_annual"] / 1e3,
            equitable_results["food_price_index_annual"] / 1e3,
            integrated_results["food_price_index_annual"] / 1e3,
        ),
    )

    save_plot("food_price_index_plot_integrated.png")

    # ========================================================
    # Food insecurity
    # ========================================================

    plt.figure(figsize=(2.8, 2.0), dpi=150)

    for results, colour in [
        (baseline_results, "gray"),
        (sustainable_results, "green"),
        (industrial_results, "red"),
        (equitable_results, "blue"),
        (integrated_results, "orange"),
    ]:
        plt.plot(
            yearly,
            results["food_insecurity_index_annual"],
            linewidth=BASELINE_LINEWIDTH,
            color=colour,
        )

    plt.xlabel("Time [yr]")
    plt.ylabel(r"Food Insecurity Index [\%]")
    plt.xlim(1, T_MAX)
    plt.ylim(0, 40)

    save_plot("food_insecurity_index_plot_integrated.png")

    # ========================================================
    # Gini
    # ========================================================

    plt.figure(figsize=(2.8, 2.0), dpi=150)

    plt.plot(
        time_array,
        baseline_results["gini"],
        linewidth=BASELINE_LINEWIDTH,
        color="gray",
    )

    plt.plot(
        time_array,
        sustainable_results["gini"],
        linewidth=BASELINE_LINEWIDTH,
        color="green",
        linestyle="--",
    )

    plt.plot(
        time_array,
        industrial_results["gini"],
        linewidth=BASELINE_LINEWIDTH,
        color="red",
        linestyle="-.",
    )

    plt.plot(
        time_array,
        equitable_results["gini"],
        linewidth=BASELINE_LINEWIDTH,
        color="blue",
        linestyle=":",
    )

    plt.plot(
        time_array,
        integrated_results["gini"],
        linewidth=BASELINE_LINEWIDTH,
        color="orange",
    )

    plt.xlabel("Time [yr]")
    plt.ylabel("Gini Index")
    plt.xlim(1, T_MAX)

    plt.ylim(
        0,
        1.1
        * series_max(
            baseline_results["gini"],
            sustainable_results["gini"],
            industrial_results["gini"],
            equitable_results["gini"],
            integrated_results["gini"],
        ),
    )

    save_plot("gini_index_plot_integrated.png")

    # ========================================================
    # Palma
    # ========================================================

    plt.figure(figsize=(2.8, 2.0), dpi=150)

    plt.plot(
        time_array,
        baseline_results["palma"],
        linewidth=BASELINE_LINEWIDTH,
        color="gray",
    )

    plt.plot(
        time_array,
        sustainable_results["palma"],
        linewidth=BASELINE_LINEWIDTH,
        color="green",
        linestyle="--",
    )

    plt.plot(
        time_array,
        industrial_results["palma"],
        linewidth=BASELINE_LINEWIDTH,
        color="red",
        linestyle="-.",
    )

    plt.plot(
        time_array,
        equitable_results["palma"],
        linewidth=BASELINE_LINEWIDTH,
        color="blue",
        linestyle=":",
    )

    plt.plot(
        time_array,
        integrated_results["palma"],
        linewidth=BASELINE_LINEWIDTH,
        color="orange",
    )

    plt.xlabel("Time [yr]")
    plt.ylabel("Palma Ratio")
    plt.xlim(1, T_MAX)

    plt.ylim(
        0,
        1.1
        * series_max(
            baseline_results["palma"],
            sustainable_results["palma"],
            industrial_results["palma"],
            equitable_results["palma"],
            integrated_results["palma"],
        ),
    )

    save_plot("palma_ratio_plot_integrated.png")

    # ========================================================
    # Income distributions
    # ========================================================

    baseline_alpha_0 = (
        baseline_results["average_real_income"][0]
        * baseline_results["lam_series"][0]
    )

    baseline_scale_0 = 1 / baseline_results["lam_series"][0]

    baseline_income_pdf_0 = gamma.pdf(
        x=baseline_results["income_x"],
        a=baseline_alpha_0,
        scale=baseline_scale_0,
    )

    def final_income_pdf(results):
        alpha = (
            results["average_real_income"][-1]
            * results["lam_series"][-1]
        )

        scale = 1 / results["lam_series"][-1]

        return gamma.pdf(
            x=results["income_x"],
            a=alpha,
            scale=scale,
        )

    baseline_income_pdf_T = final_income_pdf(baseline_results)
    sustainable_income_pdf_T = final_income_pdf(sustainable_results)
    industrial_income_pdf_T = final_income_pdf(industrial_results)
    equitable_income_pdf_T = final_income_pdf(equitable_results)
    integrated_income_pdf_T = final_income_pdf(integrated_results)

    plt.figure(figsize=(2.8, 2.0), dpi=150)

    plt.plot(
        baseline_results["income_x"],
        baseline_income_pdf_0,
        linewidth=BASELINE_LINEWIDTH,
        color="black",
        linestyle="-",
        label="Baseline Scenario (t=0)",
    )

    plt.plot(
        baseline_results["income_x"],
        baseline_income_pdf_T,
        linewidth=BASELINE_LINEWIDTH,
        color="gray",
        linestyle="--",
    )

    plt.plot(
        sustainable_results["income_x"],
        sustainable_income_pdf_T,
        linewidth=BASELINE_LINEWIDTH,
        color="green",
        linestyle="--",
    )

    plt.plot(
        industrial_results["income_x"],
        industrial_income_pdf_T,
        linewidth=BASELINE_LINEWIDTH,
        color="red",
        linestyle="--",
    )

    plt.plot(
        equitable_results["income_x"],
        equitable_income_pdf_T,
        linewidth=BASELINE_LINEWIDTH,
        color="blue",
        linestyle="--",
    )

    plt.plot(
        integrated_results["income_x"],
        integrated_income_pdf_T,
        linewidth=BASELINE_LINEWIDTH,
        color="orange",
        linestyle="--",
    )

    plt.xlabel("Real Income [£k/yr]")
    plt.ylabel("Income PDF")

    plt.xlim(
        1,
        baseline_results["income_x"][-1],
    )

    plt.ylim(
        0,
        1.1
        * series_max(
            baseline_income_pdf_0,
            baseline_income_pdf_T,
            sustainable_income_pdf_T,
            industrial_income_pdf_T,
            equitable_income_pdf_T,
            integrated_income_pdf_T,
        ),
    )

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()