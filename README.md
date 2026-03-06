# Indicator Modelling

<p align="center">
  <img src="fast_api/static/logos/Media_986283_smxx.png" alt="Indicator Modelling logo" width="300">
</p>

System dynamics modelling framework for exploring interactions between Glasgow Thriving Place indicators.

This project combines:
- a soil and indicator simulation core
- a FastAPI backend
- an interactive front end for visualising scenarios and indicator behaviour over time

## Project overview

The model is designed to examine how different social, environmental, and system-level indicators interact dynamically under different scenarios. It supports exploratory simulation and visual analysis through a browser-based interface.

## Run locally

First install the required dependencies:

```bash
pip install -r requirements.txt

PYTHONPATH=. uvicorn fast_api.app_indicator.main:app --reload --host 0.0.0.0 --port 8000

```

## Project Structure 
    fast_api/
    ├── app_indicator/
    │   ├── core/
    │   ├── routers/
    │   ├── schemas/
    │   └── services/
    ├── static/
    │   └── logos/
    ├── templates/
    └── main_v1.py

    soil_ode_UI/
    └── soil_model_core.py

    

## Main components

-- FastAPI app
Serves the web interface and API endpoints for simulation.

-- Simulation services
Handle scenario execution and communication between the API and the model core.

-- Soil / indicator model core
Contains the main system dynamics logic used to generate outputs.

-- Templates and static assets
Provide the HTML layout, styling, and project visuals.

## Development notes

The app is currently run through uvicorn with the project root added to PYTHONPATH, so imports resolve correctly across the FastAPI and model components.

## Version
Current tagged release:
-- v1.0_indicator_system