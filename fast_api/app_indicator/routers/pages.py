from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..core.config import TEMPLATES_DIR


router = APIRouter(tags=["pages"])

templates = Jinja2Templates(
    directory=str(TEMPLATES_DIR)
)


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


@router.get("/paper", response_class=HTMLResponse)
def paper(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="paper.html",
        context={},
    )