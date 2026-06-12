"""
Ruta de construcción del P&L proyectado.
"""
from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from api.models import BuildRequest, BuildResponse, Totales
from api.session import (
    config_exists,
    df_exists,
    load_config,
    load_df,
    save_df,
    save_json,
    session_exists,
)
from src.io.precargado import load_base_2025
from src.logica.pnl_builder import build_pnl

router = APIRouter()


@router.post("/build", response_model=BuildResponse)
async def build(req: BuildRequest) -> BuildResponse:
    if not session_exists(req.session_id):
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    if not df_exists(req.session_id, "base_2026"):
        raise HTTPException(status_code=400, detail="Base 2026 no cargada en esta sesión")

    if not config_exists(req.session_id):
        raise HTTPException(status_code=400, detail="Configuración no guardada en esta sesión")

    base_2026 = load_df(req.session_id, "base_2026")
    cfg = load_config(req.session_id)

    try:
        base_2025 = load_base_2025()
    except Exception:
        base_2025 = None

    try:
        pnl = build_pnl(
            base_2026=base_2026,
            mes_pivot=cfg["mes_pivot"],
            horizonte=cfg["horizonte"],
            base_2025=base_2025,
            escenario=cfg.get("escenario"),
            dia_corte=cfg.get("dia_corte"),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al construir el P&L: {exc}")

    # Extraer attrs ANTES de guardar en parquet (no se preservan)
    info_calibracion: list[str] = pnl.attrs.get("info_calibracion", [])
    warnings_continuidad: list[str] = pnl.attrs.get("warnings_continuidad", [])

    # Guardar pnl y attrs para export posterior
    save_df(req.session_id, "pnl", pnl)
    save_json(req.session_id, "pnl_attrs", {
        "info_calibracion": info_calibracion,
        "warnings_continuidad": warnings_continuidad,
    })

    # Totales: suma sobre todos los meses proyectados
    def _sum(col: str) -> float:
        return float(pnl[col].sum()) if col in pnl.columns else 0.0

    totales = Totales(
        net_revenue=_sum("net_revenue"),
        npv=_sum("npv"),
        bimo=_sum("bimo"),
        revenue_margin=_sum("revenue_margin"),
    )

    # Serializar a JSON-safe usando to_json para convertir tipos numpy
    pnl_rows: list[dict] = json.loads(pnl.to_json(orient="records", double_precision=2))

    return BuildResponse(
        ok=True,
        pnl=pnl_rows,
        info_calibracion=info_calibracion,
        warnings_continuidad=warnings_continuidad,
        totales=totales,
    )
