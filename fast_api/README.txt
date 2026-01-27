FastAPI Soil & Food System App

This app runs a FastAPI server that:

serves an interactive dashboard for soil, production, and food indicators

exposes a simulation API

displays an embedded academic paper (PDF)

How to run

From the project root:

python3 -m venv soil_env
source soil_env/bin/activate
pip install -r requirements.txt
uvicorn fast_api.main:app --reload


Open in your browser:

Dashboard: http://127.0.0.1:8000/

Paper (PDF): http://127.0.0.1:8000/paper

What main.py does

Starts a FastAPI server

Serves the dashboard UI at /

Runs the soil/food simulation via /api/simulate

Serves a compiled PDF paper at /paper

Exposes a simple health check at /health

Updating the paper

Replace the PDF file at:

fast_api/static/paper/food_system_model.pdf