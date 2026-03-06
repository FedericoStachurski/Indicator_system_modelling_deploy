# Soil Model Core

This module contains the **core system dynamics model** used in the Indicator System application.

It implements a multi-land soil model based on ordinary differential equations (ODEs) and combines environmental, production, and socio-economic dynamics. The model is designed to simulate how soil quality, agricultural production, and economic indicators evolve over time under different land management scenarios.

This file contains **only the modelling and simulation logic**.  
It does **not** contain any user interface, plotting, or web application code.

---

# Main Components

## Farming Modes

The model supports cyclical farming practices through a pulse function:

- **Cash crop phase**
- **Cover crop phase**

These cycles determine when soil degradation is active and when recovery processes dominate.

---

## Degradation Scenarios

Several degradation mechanisms are available and can be selected per land type:

- **Constant degradation**
- **Phase-out degradation**
- **Natural to synthetic transition**
- **Fertiliser-dependent degradation**

Each scenario defines how soil degradation evolves over time.

---

## Soil Recovery

The model includes different soil recovery behaviours:

- **Constant recovery rate**
- **Logistic recovery depending on soil quality**

These functions represent how soil systems recover under different ecological conditions.

---

## Yield Response

Crop yield depends on fertiliser input and soil condition.  
A nonlinear yield response function determines agricultural productivity.

---

## Land Configuration

Each land type is defined using a `LandConfig` data structure containing:

- soil parameters
- degradation scenario
- recovery behaviour
- land fraction
- production capacity
- farming cycle settings

This allows the simulation to represent **multiple heterogeneous land systems simultaneously**.

---

## Simulation Engine

The core simulation function is:
- simulate_multi_land()





This function:

1. Solves the soil ODEs for each land type
2. Computes agricultural production
3. Simulates macroeconomic variables such as population and income
4. Estimates emissions and food production
5. Generates indicators related to food affordability and food security

The solver uses **SciPy's `solve_ivp`** to integrate the system over time.

---

## Model Outputs

The simulation returns a `SimulationResult` object containing time series such as:

- soil quality
- land production
- food production
- population
- income
- food prices
- emissions
- inequality indicators (Gini, Palma)
- food security indicators

These outputs are used by the FastAPI application to generate visualisations and indicators in the user interface.

---

# Design Philosophy

The modelling code is intentionally separated from the application layer to ensure:

- modularity
- testability
- easier extension of the model
- independence from UI frameworks

All visualisation and interaction is handled elsewhere in the project.