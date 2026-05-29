"""Tests de la lógica financiera (M9-M15)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from config.settings import PNL_DIMENSIONES, PNL_METRICAS, ROOT_DIR
from src.export.excel_writer import write_pnl_excel
from src.io.readers import read_base_2026
from src.logica.pnl_builder import build_pnl


PATH_BASE_2026_REF: Path = ROOT_DIR / "data" / "referencia" / "base 2026.xlsx"
PATH_EXCEL_REF: Path = ROOT_DIR / "data" / "referencia" / "HTML - Modelo Run Rate.xlsx"


# Tolerancia relativa de comparación contra el Excel original.
# La v1 hace simplificaciones aceptadas con el usuario (sin elasticidades,
# sin shift de ASP, sin override de upf-fees con mes April), así que el match
# no es bit-perfect — los totales caen dentro del 15% de las referencias.
_TOLERANCIA = 0.15


@pytest.mark.skipif(not PATH_BASE_2026_REF.exists(), reason="Falta Base 2026 de referencia")
def test_build_pnl_estructura() -> None:
    base = read_base_2026(PATH_BASE_2026_REF)
    pnl = build_pnl(base, mes_pivot=5, horizonte=12)

    # Dimensiones y métricas presentes en el orden correcto
    assert list(pnl.columns) == PNL_DIMENSIONES + PNL_METRICAS

    # 12 meses por combo
    by_combo = pnl.groupby(["pais", "marca", "viaje", "producto"]).size()
    assert (by_combo == 12).all()


@pytest.mark.skipif(not PATH_BASE_2026_REF.exists(), reason="Falta Base 2026 de referencia")
def test_build_pnl_mes1_es_mes_pivot() -> None:
    base = read_base_2026(PATH_BASE_2026_REF)
    pnl = build_pnl(base, mes_pivot=5, horizonte=12)

    mes1 = pnl[pnl["numero_mes_proyectado"] == "Mes 1"]
    assert (mes1["mes_proyectado"] == 5).all()

    mes12 = pnl[pnl["numero_mes_proyectado"] == "Mes 12"]
    assert (mes12["mes_proyectado"] == 4).all()


@pytest.mark.skipif(not PATH_BASE_2026_REF.exists(), reason="Falta Base 2026 de referencia")
def test_metricas_derivadas_consistentes() -> None:
    base = read_base_2026(PATH_BASE_2026_REF)
    pnl = build_pnl(base, mes_pivot=5, horizonte=12)

    # bimo = dif_fx + currency_hedge
    bimo_recalc = pnl["dif_fx"] + pnl["currency_hedge"]
    assert (abs(pnl["bimo"] - bimo_recalc) < 1e-6).all()

    # revenue_margin = up_front_incentives + fees + cancellations
    rm_recalc = pnl["up_front_incentives"] + pnl["fees"] + pnl["cancellations"]
    assert (abs(pnl["revenue_margin"] - rm_recalc) < 1e-6).all()


@pytest.mark.skipif(not PATH_BASE_2026_REF.exists(), reason="Falta Base 2026 de referencia")
def test_export_excel_no_lanza() -> None:
    base = read_base_2026(PATH_BASE_2026_REF)
    pnl = build_pnl(base, mes_pivot=5, horizonte=12)
    blob = write_pnl_excel(pnl)
    assert isinstance(blob, bytes) and len(blob) > 0


@pytest.mark.skipif(not PATH_EXCEL_REF.exists(), reason="Falta Excel original")
def test_comparacion_contra_excel_original() -> None:
    """Compara totales mensuales contra el P&L cacheado del Excel original.

    La Base 2026 del Excel original es MTD parcial al día 20 (mayo), así que
    se annualiza con dia_corte=20 para hacer la comparación apples-to-apples.
    Tolerancia: 15% (ver `_TOLERANCIA`).
    """
    base = read_base_2026(PATH_BASE_2026_REF)
    pnl = build_pnl(base, mes_pivot=5, horizonte=12, dia_corte=20)

    ref = pd.read_excel(PATH_EXCEL_REF, sheet_name="P&L")
    ref["mes_proyectado"] = pd.to_numeric(ref["mes_proyectado"], errors="coerce")
    ref = ref.dropna(subset=["mes_proyectado"])

    metricas = ["orders", "gross_bookings", "net_revenue", "revenue_margin"]
    mine_tot = pnl.groupby("mes_proyectado")[metricas].sum()
    ref_tot = ref.groupby("mes_proyectado")[metricas].sum()

    for mes in mine_tot.index:
        for met in metricas:
            mine = float(mine_tot.loc[mes, met])
            ref_val = float(ref_tot.loc[mes, met])
            if abs(ref_val) < 1.0:
                continue  # ignora valores ≈ 0
            ratio = mine / ref_val
            assert (1 - _TOLERANCIA) <= ratio <= (1 + _TOLERANCIA), (
                f"Mes {mes} {met}: mine={mine:,.2f} ref={ref_val:,.2f} ratio={ratio:.3f}"
            )
