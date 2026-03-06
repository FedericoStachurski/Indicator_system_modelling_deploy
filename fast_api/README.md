# FastAPI Application Structure

This directory contains the backend API and web interface for the Indicator System application.  
The FastAPI app is organised in a modular way so that simulation logic, API endpoints, and UI resources remain clearly separated.

## Folder Overview

### core

The `core` module contains foundational configuration and shared application utilities.

Typical responsibilities include:
- global configuration settings
- environment variables
- application constants
- shared helper functions used across the API

This layer provides the base configuration used by the rest of the application.

### routers

The `routers` directory defines the **API endpoints** of the application.

Each router corresponds to a group of related routes and handles incoming HTTP requests.

Examples:
- `health.py` – simple health check endpoint used to verify the API is running
- `pages.py` – routes responsible for serving HTML pages
- `simulate.py` – endpoints that trigger model simulations

Routers keep the API organised and allow FastAPI to mount different endpoint groups cleanly.


### schemas

The `schemas` module defines the **data structures used for requests and responses**.

These are typically implemented using **Pydantic models** and are used to:

- validate incoming request data
- structure simulation inputs
- format API responses
- ensure type safety across the application

Schemas provide a clear contract between the frontend and the backend.

### services

The `services` layer contains the **application logic** and simulation execution.

Responsibilities include:
- running simulations
- processing model inputs
- connecting API endpoints to the core model code
- handling data transformations

Separating services from routers keeps the API endpoints lightweight and ensures that business logic remains reusable and testable.

### static

The `static` folder contains **static assets** served directly by the web application.

Examples include:
- images
- logos
- CSS files
- JavaScript files

These files are used by the frontend interface but do not change dynamically.

### templates

The `templates` directory contains **HTML templates** used to render the web interface.

FastAPI serves these templates using a templating engine (typically **Jinja2**).

Templates define the layout and structure of the user interface, such as:
- the main application page
- visualisation dashboards
- documentation or supporting pages

They often interact with the API endpoints to display simulation results dynamically.


## Summary

The architecture follows a common FastAPI pattern: Request → Router → Service → Model / Simulation


This structure helps keep the codebase modular, maintainable, and easier to extend as the system evolves.
