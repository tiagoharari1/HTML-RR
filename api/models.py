"""
Pydantic schemas de request/response para todos los endpoints de la API.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, field_validator


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

class UploadBase2026Response(BaseModel):
    ok: bool
    rows: int = 0
    meses: list[int] = []
    errors: list[str] = []


class UploadContableResponse(BaseModel):
    ok: bool
    rows: int = 0
    errors: list[str] = []


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

class ConfigRequest(BaseModel):
    session_id: str
    mes_pivot: int
    horizonte: int = 12
    dia_corte: int | None = None
    escenario: str | None = None

    @field_validator("mes_pivot")
    @classmethod
    def mes_pivot_valido(cls, v: int) -> int:
        if not 1 <= v <= 12:
            raise ValueError("mes_pivot debe estar entre 1 y 12")
        return v

    @field_validator("horizonte")
    @classmethod
    def horizonte_valido(cls, v: int) -> int:
        if not 1 <= v <= 24:
            raise ValueError("horizonte debe estar entre 1 y 24")
        return v


class ConfigResponse(BaseModel):
    ok: bool


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

class BuildRequest(BaseModel):
    session_id: str


class Totales(BaseModel):
    net_revenue: float
    npv: float
    bimo: float
    revenue_margin: float


class BuildResponse(BaseModel):
    ok: bool
    pnl: list[dict[str, Any]]
    info_calibracion: list[str]
    warnings_continuidad: list[str]
    totales: Totales


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

class ActualsResponse(BaseModel):
    rows: list[dict[str, Any]]


class BudgetResponse(BaseModel):
    rows: list[dict[str, Any]]


class PrecargadosStatus(BaseModel):
    macro: bool
    est_orders: bool
    est_asp: bool
    base_2025: bool


class StatusResponse(BaseModel):
    precargados: PrecargadosStatus
