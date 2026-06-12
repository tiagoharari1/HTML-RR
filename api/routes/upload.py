"""
Rutas de carga de archivos: Base 2026 y Contable.
"""
from __future__ import annotations

from io import BytesIO

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from api.models import UploadBase2026Response, UploadContableResponse
from api.session import ensure_session, save_df
from src.io.readers import read_base_2026, read_contable
from src.io.validators import validate_base_2026, validate_contable

router = APIRouter()


@router.post("/upload/base2026", response_model=UploadBase2026Response)
async def upload_base2026(
    file: UploadFile = File(...),
    session_id: str = Form(...),
) -> UploadBase2026Response:
    content = await file.read()
    try:
        df = read_base_2026(BytesIO(content))
    except Exception as exc:
        return UploadBase2026Response(ok=False, errors=[f"Error al leer el archivo: {exc}"])

    errors = validate_base_2026(df)
    if errors:
        return UploadBase2026Response(ok=False, errors=errors)

    ensure_session(session_id)
    save_df(session_id, "base_2026", df)

    meses = sorted(int(m) for m in df["Mes RI"].dropna().unique())
    return UploadBase2026Response(ok=True, rows=len(df), meses=meses)


@router.post("/upload/contable", response_model=UploadContableResponse)
async def upload_contable(
    file: UploadFile = File(...),
    session_id: str = Form(...),
) -> UploadContableResponse:
    content = await file.read()
    try:
        df = read_contable(BytesIO(content))
    except Exception as exc:
        return UploadContableResponse(ok=False, errors=[f"Error al leer el archivo: {exc}"])

    errors = validate_contable(df)
    if errors:
        return UploadContableResponse(ok=False, errors=errors)

    ensure_session(session_id)
    save_df(session_id, "contable", df)

    return UploadContableResponse(ok=True, rows=len(df))
