## User Interface ODE Soil Model
#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
import streamlit as st


# ------------------------------------------------------------
# ODE system and helper functions
# ------------------------------------------------------------

def degradation_constant(t, params):
    return params["D_const"]


def degradation_phaseout(t, params):
    return params["D_high"] if t < params["T_int"] else params["D_low"]

def degredation_natural_synthetic(t, params):
    """Example of more complex degradation function (not used in UI)."""
    alpha, beta = params.get("alpha", 0.5), params.get("beta", 0.5)
    a0 , a1 = params.get("a0", 1.0), params.get("a1", 1)
    x = alpha * t
    y = beta * t
    return a0 * np.exp(-x) + a1 * (1 - np.exp(-y))


SCENARIOS = {
    "Constant degradation D": degradation_constant,
    "Phase-out at T_int": degradation_phaseout,
    "Natural to synthetic": degredation_natural_synthetic,
}


def soil_ode(t, S, alpha, D_fun, D_params):
    """Soil dynamics: dS/dt = (alpha - D(t)) * S * (1 - S)"""
    D_t = D_fun(t, D_params)
    return (alpha - D_t) * S * (1.0 - S)


def compute_solution(alpha, S0, T_max, scenario_name, params, n_points=500):
    """Solve the ODE and return arrays for plotting."""
    D_fun = SCENARIOS[scenario_name]
    t_eval = np.linspace(0.0, T_max, n_points)

    sol = solve_ivp(
        soil_ode,
        t_span=(0.0, T_max),
        y0=[S0],
        t_eval=t_eval,
        args=(alpha, D_fun, params),
    )

    t = sol.t
    S = sol.y[0]
    D_vals = np.array([D_fun(tt, params) for tt in t])

    return t, S, D_vals





# ---------------- Sidebar Controls ---------------- #

st.sidebar.header("Model parameters")

scenario_name = st.sidebar.selectbox(
    "Degradation scenario:",
    list(SCENARIOS.keys()),
    index=1,
)

alpha = st.sidebar.slider("Intrinsic recovery rate α", 0.01, 0.5, 0.20, 0.01)
S0 = st.sidebar.slider("Initial soil health S₀", 0.01, 1.0, 0.8, 0.01)
T_max = st.sidebar.slider("Simulation horizon T_max", 20.0, 250.0, 100.0, 10.0)

st.sidebar.markdown("---")

params = {}

if scenario_name == "Constant degradation D":
    params["D_const"] = st.sidebar.slider("D (constant)", 0.0, 1.0, 0.1, 0.01)

elif scenario_name == "Phase-out at T_int":  # phase-out
    params["D_high"] = st.sidebar.slider("D_high (pre-intervention)", 0.0, 1.0, 0.4, 0.01)
    params["D_low"] = st.sidebar.slider("D_low (post-intervention)", 0.0, 1.0, 0.05, 0.01)
    params["T_int"] = st.sidebar.slider("Intervention time T_int", 0.0, T_max, 30.0, 1.0)

elif scenario_name == "Natural to synthetic":
    params["a0"] = st.sidebar.slider("a0 (natural degradation)", 0.0, 1.0, 0.5, 0.01)
    params["a1"] = st.sidebar.slider("a1 (synthetic degradation)", 0.0, 1.0, 0.5, 0.01) 
    params["alpha"] = st.sidebar.slider("alpha, natural rate of degradation", 0.0, 1.0, 0.5, 0.01)
    params["beta"] = st.sidebar.slider("beta, synthetic rate of degredation factor", 0.0, 1.0, 0.5, 0.01) 

# ------------------------------------------------------------
# Streamlit UI
# ------------------------------------------------------------

def math_model_Dt_scenario(scenario_name):
    if scenario_name == "Constant degradation D":
        return r"D(t) = D_{const}"
    elif scenario_name == "Phase-out at T_int":
        return r"""
        D(t) = \begin{cases} 
        D_{high}, & t < T_{int} \\ 
        D_{low}, & t \geq T_{int} 
        \end{cases}
        """
    elif scenario_name == "Natural to synthetic":
        return r"D(t) = a_0 e^{-\alpha t} + a_1 (1 - e^{-\beta t})"
    else:
        return ""


st.set_page_config(page_title="Soil Health ODE Tool", layout="wide")
st.title("Soil Health Feedback Mechanisms (Interactive ODE Tool)")

st.markdown(
    """
This tool simulates a simplified soil health system.
The soil health index \\( S(t) $\in$ [0, 1] \\) evolves according to:
"""
)

st.latex(r"\frac{dS}{dt} = (\alpha(S) - D(t))\,S(t)(1 - S(t))")

st.markdown(
    """
where:

- **S(t)** is soil health (0 = poorest, 1 = best)  
- **α** is the intrinsic soil recovery rate  
- **D(t)** is the degradation rate (e.g. synthetic fertilisers, intensive use)

The functional form of \\(D(t)\\) is chosen via the scenario selector in the sidebar.
"""
)

st.markdown(f"**Current scenario:** `{scenario_name}`")

st.markdown("The corresponding model for \\(D(t)\\) is:")

st.latex(math_model_Dt_scenario(scenario_name))

st.markdown(
    """
Use the sliders in the sidebar to explore how different parameter choices
affect the soil trajectory and whether it recovers or tips into a degraded state.
---
"""
)



# ---------------- Run the simulation ---------------- #

t, S, D_vals = compute_solution(alpha, S0, T_max, scenario_name, params)

# Metrics
S_final = S[-1]
S_min = float(np.min(S))
S_target = 0.8
reach_target = np.where(S >= S_target)[0]
if len(reach_target) > 0:
    t_reach = t[reach_target[0]]
    recovery_note = f"t ≈ {t_reach:.1f}"
else:
    recovery_note = "Not reached"


# ---------------- Layout: metrics + plots ---------------- #

col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("Summary")
    st.metric("Final S(T_max)", f"{S_final:.3f}")
    st.metric("Minimum S(t)", f"{S_min:.3f}")
    st.metric(f"Time to S ≥ {S_target}", recovery_note)

    st.markdown("**Scenario parameters:**")
    st.write(params)

with col2:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 5), sharex=True)

    # Soil health plot
    ax1.plot(t, S, linewidth=2)
    ax1.axhline(0.1, linestyle="--", color="gray")
    ax1.axhline(0.8, linestyle="--", color="gray")
    ax1.set_ylabel("Soil health S(t)")
    ax1.set_ylim(-0.05, 1.05)
    ax1.grid(True)

    # Degradation plot
    ax2.plot(t, D_vals, linewidth=2)
    ax2.set_xlabel("Time")
    ax2.set_ylabel("Degradation D(t)")
    ax2.grid(True)

    fig.tight_layout()
    st.pyplot(fig)
