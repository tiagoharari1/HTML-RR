"""
Ruta de configuración del wizard: mes pivot, horizonte, día de corte, escenario.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.models import ConfigRequest, ConfigResponse
from api.session import ensure_session, save_config

router = APIRouter()


@router.post("/config", response_model=ConfigResponse)
async def set_config(req: ConfigRequest) -> ConfigResponse:
    ensure_session(req.session_id)
    save_config(req.session_id, {
        "mes_pivot": req.mes_pivot,
        "horizonte": req.horizonte,
        "dia_corte": req.dia_corte,
        "escenario": req.escenario,
    })
    return ConfigResponse(ok=True)
