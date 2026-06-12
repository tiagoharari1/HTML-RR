"""
Rutas de datos pre-cargados: actuals, budget y estado de archivos.
"""
from __future__ import annotations

import json

from fastapi import APIRouter

from api.models import ActualsResponse, BudgetResponse, PrecargadosStatus, StatusResponse
from src.io.precargado import precargados_disponibles

router = APIRouter()


def _df_to_rows(df) -> list[dict]:
    return json.loads(df.to_json(orient="records", double_precision=2))


@router.get("/actuals", response_model=ActualsResponse)
async def get_actuals() -> ActualsResponse:
    try:
        from src.io.actuals_budget import load_actuals
        df = load_actuals()
        return ActualsResponse(rows=_df_to_rows(df))
    except Exception as exc:
        return ActualsResponse(rows=[])


@router.get("/budget", response_model=BudgetResponse)
async def get_budget() -> BudgetResponse:
    try:
        from src.io.actuals_budget import load_budget
        df = load_budget()
        return BudgetResponse(rows=_df_to_rows(df))
    except Exception as exc:
        return BudgetResponse(rows=[])


@router.get("/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    disp = precargados_disponibles()
    return StatusResponse(
        precargados=PrecargadosStatus(
            macro=disp.get("macro", False),
            est_orders=disp.get("estacionalidad_orders", False),
            est_asp=disp.get("estacionalidad_asp", False),
            base_2025=disp.get("base_2025", False),
        )
    )
