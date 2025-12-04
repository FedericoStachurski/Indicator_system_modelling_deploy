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

# Smaller heading so it doesn’t get cut
st.markdown("### Soil Health & Production Across Multiple Lands")

# ---------- Custom background + layout tightening ----------
st.markdown(
    """
    <style>
    /* App background: green at bottom -> white at top */
    .stApp {
        background: linear-gradient(to top, #bdecb6 0%, #ffffff 70%);
    }

    /* Reduce padding of the main container */
    .block-container {
        padding-top: 0.6rem;
        padding-bottom: 0.2rem;
        padding-left: 0.6rem;
        padding-right: 0.6rem;
    }

    /* No page scroll: keep everything in viewport */
    html, body, [data-testid="stAppViewContainer"] {
        height: 100%;
        overflow-y: hidden;
    }

    /* Smaller global fonts and force dark text */
    body, p, div, span, label, input, textarea {
        font-size: 0.75rem;
        color: #000000;
    }

    h1, h2, h3, h4 {
        color: #000000;
        margin-top: 0.1rem;
        margin-bottom: 0.1rem;
        font-size: 1.0rem;
    }

    /* Buttons: dark background, WHITE font */
    .stButton > button {
        background-color: #222222 !important;
        color: #ffffff !important;
        border: 1px solid #000000 !important;
        padding: 0.15rem 0.5rem !important;
        font-size: 0.75rem !important;
    }

    /* Make sliders a bit more compact */
    .stSlider > div {
        padding-top: 0.05rem;
        padding-bottom: 0.05rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# ------------------------------------------------------------
# LAYOUT CONTAINERS (TOP plots, BOTTOM controls)
# ------------------------------------------------------------

plots_container = st.container()
controls_container = st.container()

# ------------------------------------------------------------
# BOTTOM: controls (lands + global params)
# ------------------------------------------------------------

with controls_container:
    st.subheader("Land configuration")

    # Manage number of lands via session_state
    if "n_lands" not in st.session_state:
        st.session_state.n_lands = 2  # start with 2 so columns make sense

    # Buttons row
    cols_buttons = st.columns([1, 1, 3])
    with cols_buttons[0]:
        if st.button("+ Add land", key="add_land", help="Add a new land configuration"):
            if st.session_state.n_lands < 10:
                st.session_state.n_lands += 1
    with cols_buttons[1]:
        if st.button("- Remove land", key="remove_land", help="Remove the last land configuration"):
            if st.session_state.n_lands > 1:
                st.session_state.n_lands -= 1

    n_lands = st.session_state.n_lands
    st.markdown(f"**Number of lands:** {n_lands}")

    st.markdown("Each column is a land (side-by-side parameters).")

    land_percentages = []
    land_configs_raw = []

    # ---- LAND COLUMNS SIDE BY SIDE ----
    land_cols = st.columns(n_lands)

    for i in range(n_lands):
        with land_cols[i]:
            st.markdown(f"**Land {i+1}**")
            name = st.text_input(
                "Name",
                value=f"Land {i+1}",
                key=f"name_{i}",
            )

            land_pct = st.number_input(
                "Share (%)",
                min_value=0.0,
                max_value=100.0,
                value=100.0 / n_lands,
                step=1.0,
                key=f"land_pct_{i}",
            )
            land_percentages.append(land_pct)

            st.markdown("Soil dynamics")
            alpha_i = st.slider(
                "α (recovery)",
                0.0,
                1.0,
                0.20,
                0.01,
                key=f"alpha_{i}",
            )

            S0_i = st.slider(
                "S₀ (initial soil)",
                0.0,
                1.0,
                0.8,
                0.01,
                key=f"S0_{i}",
            )

            P_max_i = st.slider(
                "P_max (max yield)",
                0.0,
                10.0,
                1.0,
                0.1,
                key=f"Pmax_{i}",
            )

            st.markdown("Degradation model")
            scenario_options = list(SCENARIOS.keys())
            scenario_name = st.selectbox(
                "Scenario",
                scenario_options,
                key=f"scenario_{i}",
            )

            # Scenario-specific parameters in a compact expander
            deg_params = {}
            with st.expander("Degradation parameters", expanded=False):
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
                        "D_high",
                        0.0,
                        1.0,
                        0.4,
                        0.01,
                        key=f"D_high_{i}",
                    )
                    D_low = st.slider(
                        "D_low",
                        0.0,
                        1.0,
                        0.05,
                        0.01,
                        key=f"D_low_{i}",
                    )
                    T_int = st.slider(
                        "T_int (intervention time)",
                        0.0,
                        100.0,
                        30.0,
                        1.0,
                        key=f"T_int_{i}",
                    )
                    deg_params["D_high"] = D_high
                    deg_params["D_low"] = D_low
                    deg_params["T_int"] = T_int

                elif scenario_name == "Natural to synthetic":
                    a0 = st.slider(
                        "a0 (natural)",
                        0.0,
                        1.0,
                        0.5,
                        0.01,
                        key=f"a0_{i}",
                    )
                    a1 = st.slider(
                        "a1 (synthetic)",
                        0.0,
                        1.0,
                        0.5,
                        0.01,
                        key=f"a1_{i}",
                    )
                    alpha_deg = st.slider(
                        "alpha (decay)",
                        0.0,
                        1.0,
                        0.5,
                        0.01,
                        key=f"alpha_deg_{i}",
                    )
                    beta_deg = st.slider(
                        "beta (onset)",
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

    st.markdown("---")
    st.subheader("Global settings")

    T_max = st.slider("Simulation horizon T_max", 10.0, 250.0, 100.0, 10.0)
    n_points = 500  # fixed

# ------------------------------------------------------------
# After controls are defined, run simulation
# ------------------------------------------------------------

results = simulate_multi_land(lands, T_max=T_max, n_points=n_points)

t = results.t
soils = results.soils                    # (n_lands, n_times)
productions = results.productions        # (n_lands, n_times)
total_production = results.total_production
weighted_soil = results.weighted_soil
land_names = results.land_names
land_fractions_arr = results.land_fractions

# From econ extension
harvest_per_land = results.harvest_per_land   # (n_lands, n_times)
total_harvest = results.total_harvest         # (n_times,)
affordability = results.affordability         # (n_times,)

# ------------------------------------------------------------
# TOP: row of 4 plots (Soil, Harvest, Production, Affordability)
# with slightly higher resolution + black figure borders
# ------------------------------------------------------------

with plots_container:
    st.subheader("Key trajectories (compact view)")

    col_soil, col_harvest, col_prod, col_aff = st.columns(4)

    # Soil plot
    with col_soil:
        fig_s, ax_s = plt.subplots(figsize=(2.4, 1.6))
        fig_s.patch.set_edgecolor("black")
        fig_s.patch.set_linewidth(1.5)
        for i, name in enumerate(land_names):
            ax_s.plot(t, soils[i], linewidth=0.7)
        ax_s.plot(t, weighted_soil, linewidth=0.9, linestyle="--")
        ax_s.set_title("Soil", fontsize=7)
        ax_s.set_ylim(-0.05, 1.05)
        ax_s.tick_params(labelsize=6)
        ax_s.grid(True, linewidth=0.3)
        st.pyplot(fig_s)

    # Harvest plot
    with col_harvest:
        fig_hv, ax_hv = plt.subplots(figsize=(2.4, 1.6))
        fig_hv.patch.set_edgecolor("black")
        fig_hv.patch.set_linewidth(1.5)
        ax_hv.plot(t, total_harvest, linewidth=0.9)
        ax_hv.set_title("Harvest", fontsize=7)
        ax_hv.tick_params(labelsize=6)
        ax_hv.grid(True, linewidth=0.3)
        st.pyplot(fig_hv)

    # Production plot
    with col_prod:
        fig_p, ax_p = plt.subplots(figsize=(2.4, 1.6))
        fig_p.patch.set_edgecolor("black")
        fig_p.patch.set_linewidth(1.5)
        ax_p.plot(t, total_production, linewidth=0.9)
        ax_p.set_title("Production", fontsize=7)
        ax_p.tick_params(labelsize=6)
        ax_p.grid(True, linewidth=0.3)
        st.pyplot(fig_p)

    # Affordability plot
    with col_aff:
        fig_a, ax_a = plt.subplots(figsize=(2.4, 1.6))
        fig_a.patch.set_edgecolor("black")
        fig_a.patch.set_linewidth(1.5)
        ax_a.plot(t, affordability, linewidth=0.9)
        ax_a.axhline(1.0, linestyle="--", color="gray", linewidth=0.6)
        ax_a.set_title("Affordability", fontsize=7)
        ax_a.tick_params(labelsize=6)
        ax_a.grid(True, linewidth=0.3)
        st.pyplot(fig_a)
