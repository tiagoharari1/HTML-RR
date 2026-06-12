"""
Rutas de exportación de Excel: P&L y P&L Evolution.
"""
from __future__ import annotations

from io import BytesIO

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from api.session import df_exists, load_df, session_exists
from src.export.excel_writer import write_evolution_excel, write_pnl_excel

router = APIRouter()

_XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _pnl_or_404(session_id: str):
    if not session_exists(session_id):
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    if not df_exists(session_id, "pnl"):
        raise HTTPException(status_code=400, detail="P&L no calculado — ejecute /api/build primero")
    return load_df(session_id, "pnl")


@router.get("/export/pnl")
async def export_pnl(session_id: str) -> StreamingResponse:
    pnl = _pnl_or_404(session_id)
    xlsx_bytes = write_pnl_excel(pnl)
    return StreamingResponse(
        BytesIO(xlsx_bytes),
        media_type=_XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": "attachment; filename=pnl.xlsx"},
    )


@router.get("/export/evolution")
async def export_evolution(session_id: str) -> StreamingResponse:
    pnl = _pnl_or_404(session_id)
    xlsx_bytes = write_evolution_excel(pnl)
    return StreamingResponse(
        BytesIO(xlsx_bytes),
        media_type=_XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": "attachment; filename=pnl_evolution.xlsx"},
    )
