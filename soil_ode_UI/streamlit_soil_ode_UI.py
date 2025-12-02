#!/usr/bin/env python3
"""
app_soil_streamlit.py

Streamlit UI for the multi-land soil model.
"""

import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

from soil_model_core import (
    LandConfig,
    simulate_multi_land,
    SCENARIOS,
)


# ------------------------------------------------------------
# Streamlit page setup
# ------------------------------------------------------------

st.set_page_config(page_title="Soil Health Multi-Land Tool", layout="wide")
st.title("Soil Health & Production Across Multiple Lands")

# st.markdown(
#     """
# This app simulates soil health and production for multiple land parcels.
# Each land can have its **own** degradation model and parameters.

# - Top-left: soil and production trajectories  
# - Top-right: a **doughnut environmental chart** (placeholder)  
# - Bottom: controls for each land (up to 10)
# """
# )

st.markdown("---")

# We’ll use containers to control layout order: plots on top, controls below.
plots_container = st.container()
controls_container = st.container()


# ------------------------------------------------------------
# Global / simulation controls (sidebar)
# ------------------------------------------------------------

st.sidebar.header("Global simulation settings")

T_max = st.sidebar.slider("Simulation horizon T_max", 10.0, 250.0, 100.0, 10.0)
n_points = 500  # fixed for now; you can expose this if needed

st.sidebar.markdown("---")
st.sidebar.header("Default values for new lands")
default_alpha = st.sidebar.slider("Default α", 0.01, 0.5, 0.20, 0.01)
default_S0 = st.sidebar.slider("Default S₀", 0.01, 1.0, 0.8, 0.01)
default_P_max = st.sidebar.slider("Default P_max", 0.0, 10.0, 1.0, 0.1)


# ------------------------------------------------------------
# Bottom controls: land editor
# ------------------------------------------------------------

with controls_container:
    st.subheader("Land configuration")

    # Manage number of lands via session_state so the 'Add land' button works nicely.
    if "n_lands" not in st.session_state:
        st.session_state.n_lands = 1

    cols_buttons = st.columns([1, 1, 6])
    with cols_buttons[0]:
        if st.button("➕ Add land"):
            if st.session_state.n_lands < 10:
                st.session_state.n_lands += 1
    with cols_buttons[1]:
        if st.button("➖ Remove last land"):
            if st.session_state.n_lands > 1:
                st.session_state.n_lands -= 1

    n_lands = st.session_state.n_lands
    st.markdown(f"**Number of lands:** {n_lands}")

    st.markdown(
        "For each land, set its name, land share, soil parameters, and degradation model."
    )

    land_percentages = []
    land_configs_raw = []

    # One "card" per land
    for i in range(n_lands):
        with st.expander(f"Land {i+1} settings", expanded=(i == 0)):
            name = st.text_input(
                "Land name",
                value=f"Land {i+1}",
                key=f"name_{i}",
            )

            # Land area share
            land_pct = st.number_input(
                "Land share (%)",
                min_value=0.0,
                max_value=100.0,
                value=100.0 / n_lands,
                step=1.0,
                key=f"land_pct_{i}",
            )
            land_percentages.append(land_pct)

            st.markdown("**Soil dynamics**")

            alpha_i = st.slider(
                "Intrinsic recovery rate α",
                0.0,
                1.0,
                default_alpha,
                0.01,
                key=f"alpha_{i}",
            )

            S0_i = st.slider(
                "Initial soil health S₀",
                0.0,
                1.0,
                default_S0,
                0.01,
                key=f"S0_{i}",
            )

            P_max_i = st.slider(
                "Maximum yield P_max",
                0.0,
                10.0,
                default_P_max,
                0.1,
                key=f"Pmax_{i}",
            )

            st.markdown("**Degradation model**")
            scenario_options = list(SCENARIOS.keys())
            scenario_name = st.selectbox(
                "Degradation scenario",
                scenario_options,
                key=f"scenario_{i}",
            )

            # Scenario-specific parameters
            deg_params = {}
            if scenario_name == "Constant degradation D":
                D_const = st.slider(
                    "D_const",
                    0.0,
                    1.0,
                    0.1,
                    0.01,
                    key=f"D_const_{i}",
                )
                deg_params["D_const"] = D_const

            elif scenario_name == "Phase-out at T_int":
                D_high = st.slider(
                    "D_high (pre-intervention)",
                    0.0,
                    1.0,
                    0.4,
                    0.01,
                    key=f"D_high_{i}",
                )
                D_low = st.slider(
                    "D_low (post-intervention)",
                    0.0,
                    1.0,
                    0.05,
                    0.01,
                    key=f"D_low_{i}",
                )
                T_int = st.slider(
                    "Intervention time T_int",
                    0.0,
                    T_max,
                    min(T_max / 3, 30.0),
                    1.0,
                    key=f"T_int_{i}",
                )
                deg_params["D_high"] = D_high
                deg_params["D_low"] = D_low
                deg_params["T_int"] = T_int

            elif scenario_name == "Natural to synthetic":
                a0 = st.slider(
                    "a0 (natural degradation)",
                    0.0,
                    1.0,
                    0.5,
                    0.01,
                    key=f"a0_{i}",
                )
                a1 = st.slider(
                    "a1 (synthetic degradation)",
                    0.0,
                    1.0,
                    0.5,
                    0.01,
                    key=f"a1_{i}",
                )
                alpha_deg = st.slider(
                    "alpha (natural decay rate)",
                    0.0,
                    1.0,
                    0.5,
                    0.01,
                    key=f"alpha_deg_{i}",
                )
                beta_deg = st.slider(
                    "beta (synthetic onset rate)",
                    0.0,
                    1.0,
                    0.5,
                    0.01,
                    key=f"beta_deg_{i}",
                )
                deg_params["a0"] = a0
                deg_params["a1"] = a1
                deg_params["alpha"] = alpha_deg
                deg_params["beta"] = beta_deg

            # Store raw info; we'll normalise land_pct later
            land_configs_raw.append(
                dict(
                    name=name,
                    alpha=alpha_i,
                    S0=S0_i,
                    scenario_name=scenario_name,
                    deg_params=deg_params,
                    land_pct=land_pct,
                    P_max=P_max_i,
                )
            )

    # Normalise land percentages to fractions
    total_pct = sum(land_percentages)
    if total_pct > 0:
        land_fractions = [p / total_pct for p in land_percentages]
    else:
        land_fractions = [1.0 / n_lands] * n_lands

    st.markdown(
        f"**Normalised total land = {sum(land_fractions):.2f} (should be 1.00)**"
    )

    # Build LandConfig objects
    lands = []
    for i, cfg in enumerate(land_configs_raw):
        lands.append(
            LandConfig(
                name=cfg["name"],
                alpha=cfg["alpha"],
                S0=cfg["S0"],
                scenario_name=cfg["scenario_name"],
                deg_params=cfg["deg_params"],
                land_fraction=land_fractions[i],
                P_max=cfg["P_max"],
            )
        )


# ------------------------------------------------------------
# Run simulation & plot (top)
# ------------------------------------------------------------

results = simulate_multi_land(lands, T_max=T_max, n_points=n_points)

t = results.t
soils = results.soils
productions = results.productions
total_production = results.total_production
weighted_soil = results.weighted_soil
land_names = results.land_names
land_fractions_arr = results.land_fractions

# Some simple metrics (weighted soil + total production)
S_final = float(weighted_soil[-1])
S_min = float(np.min(weighted_soil))
S_target = 0.8
reach_target = np.where(weighted_soil >= S_target)[0]
if len(reach_target) > 0:
    t_reach = t[reach_target[0]]
    recovery_note = f"t ≈ {t_reach:.1f}"
else:
    recovery_note = "Not reached"

P_final = float(total_production[-1])
P_min = float(np.min(total_production))
total_yield = float(np.trapezoid(total_production, t))


with plots_container:
    col_main, col_donut = st.columns([3, 2])

    # ---------------- Main plots (top-left) ---------------- #
    with col_main:
        st.subheader("Soil and production trajectories")

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 6), sharex=True)

        # (1) Soil trajectories per land + weighted average
        for i, name in enumerate(land_names):
            ax1.plot(t, soils[i], linewidth=1.5, label=name)
        ax1.plot(
            t,
            weighted_soil,
            linewidth=2.5,
            linestyle="--",
            label="Weighted avg soil",
        )
        ax1.axhline(0.1, linestyle="--", color="gray")
        ax1.axhline(0.8, linestyle="--", color="gray")
        ax1.set_ylabel("Soil S_i(t)")
        ax1.set_ylim(-0.05, 1.05)
        ax1.grid(True)
        ax1.legend(fontsize="small")

        # (2) Production per land + total
        for i, name in enumerate(land_names):
            ax2.plot(t, productions[i], linewidth=1.5, label=f"P {name}")
        ax2.plot(
            t,
            total_production,
            linewidth=2.5,
            linestyle="--",
            label="Total P(t)",
        )
        ax2.set_xlabel("Time")
        ax2.set_ylabel("Yield P_i(t)")
        ax2.grid(True)
        ax2.legend(fontsize="small")

        fig.tight_layout()
        st.pyplot(fig)

        # Text summary under the plots
        st.markdown("**Summary (weighted over lands):**")
        st.write(
            {
                "Final avg soil S̄(T_max)": f"{S_final:.3f}",
                "Minimum avg soil S̄(t)": f"{S_min:.3f}",
                "Time to S̄ ≥ 0.8": recovery_note,
                "Final total yield P_tot(T_max)": f"{P_final:.3f}",
                "Minimum total yield P_tot(t)": f"{P_min:.3f}",
                "Cumulative total yield ∫ P_tot(t) dt": f"{total_yield:.3f}",
            }
        )

    # ---------------- Doughnut chart (top-right) ---------------- #
    with col_donut:
        st.subheader("Environmental doughnut (placeholder)")

        # For now, just use land fractions as a simple breakdown.
        if land_fractions_arr.sum() > 0:
            labels = [f"{name}" for name in land_names]
            sizes = land_fractions_arr

            fig_d, axd = plt.subplots(figsize=(4, 4))
            wedges, _ = axd.pie(
                sizes,
                labels=labels,
                startangle=90,
                wedgeprops=dict(width=0.4, edgecolor="white"),
            )
            axd.set_title("Land share by owner")
            st.pyplot(fig_d)
        else:
            st.info("No land fractions defined yet.")

        st.markdown(
            """
            This doughnut chart is a placeholder.
            You can later replace it with a proper
            environmental / sustainability dashboard (e.g. soil, biodiversity, emissions).
            """
        )
