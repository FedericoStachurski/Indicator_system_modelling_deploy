from __future__ import annotations

from fastapi import APIRouter
from ..schemas.simulation import SimRequest, SimResponse
from ..services.simulation import run_simulation


router = APIRouter(prefix="/api", tags=["simulation"])

@router.post("/simulate", response_model=SimResponse)
def simulate(req: SimRequest):
    return run_simulation(req)
