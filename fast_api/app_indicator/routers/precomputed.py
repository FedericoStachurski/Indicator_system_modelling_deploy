from functools import lru_cache
from pathlib import Path

import numpy as np
from fastapi import APIRouter, HTTPException


router = APIRouter(
    prefix="/api",
    tags=["precomputed scenarios"],
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]

SCENARIOS_DIR = (
    PROJECT_ROOT
    / "static_scenario_runs"
    / "scenarios"
)


SCENARIO_FILES = {
    "bau": "baseline_scenario.npz",
    "sustainable": "sustainable_scenario.npz",
    "equitable": "equitable_scenario.npz",
    "industrial": "industrial_scenario.npz",
    "integrated": "integrated_scenario.npz",
}


def array_to_jsonable(value):
    arr = np.asarray(value)

    if arr.ndim == 0:
        value = arr.item()

        if isinstance(value, float) and not np.isfinite(value):
            return None

        return value

    # Convert NaN / inf to null for JSON
    if np.issubdtype(arr.dtype, np.floating):
        obj = arr.astype(object)
        obj[~np.isfinite(arr)] = None
        return obj.tolist()

    return arr.tolist()


@lru_cache(maxsize=5)
def load_precomputed_scenario(scenario_id: str):
    if scenario_id not in SCENARIO_FILES:
        raise KeyError(scenario_id)

    path = SCENARIOS_DIR / SCENARIO_FILES[scenario_id]

    if not path.exists():
        raise FileNotFoundError(path)

    with np.load(path, allow_pickle=False) as data:
        return {
            key: array_to_jsonable(data[key])
            for key in data.files
        }


@router.get("/precomputed-scenarios")
def get_precomputed_scenarios():

    try:

        return {
            scenario_id:
                load_precomputed_scenario(
                    scenario_id
                )

            for scenario_id
            in SCENARIO_FILES
        }

    except FileNotFoundError as exc:

        print(
            "PRECOMPUTED FILE ERROR:",
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Precomputed scenario "
                f"file not found: {exc}"
            ),
        )

    except Exception as exc:

        # Temporary debugging so we can see
        # the real NPZ/JSON error.
        print(
            "PRECOMPUTED SCENARIO ERROR:",
            type(exc).__name__,
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                f"{type(exc).__name__}: {exc}"
            ),
        )