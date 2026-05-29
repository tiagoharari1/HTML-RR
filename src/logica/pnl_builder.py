"""
Ensamblado final del P&L dimensional.

Pipeline:
  1. Aggregate Base 2026 al mes pivot → pivot_por_combo
  2. Proyectar orders, asp, gross_bookings
  3. Proyectar líneas de Base 2026 (ratio × GB_proy)
  4. Proyectar líneas de Base 2025 (ratio histórico × GB_proy)
  5. Aplicar ajustes especiales (commercial_discounts=0, efecto_financiero Brasil, etc.)
  6. Calcular métricas derivadas (net_revenue, npv, bimo, revenue_margin)
  7. Construir DataFrame con dimensiones + métricas en el orden de PNL_METRICAS

Devuelve un DataFrame con las dimensiones de PNL_DIMENSIONES y las métricas
de PNL_METRICAS en ese orden exacto.
"""
from __future__ import annotations

import pandas as pd

from config.settings import (
    COLS_BIMO,
    COLS_NET_REVENUE,
    COLS_NPV,
    COLS_REVENUE_MARGIN,
    LINEAS_DESDE_BASE_2025,
    LINEAS_DESDE_BASE_2026,
    LINEAS_EN_CERO,
    PNL_DIMENSIONES,
    PNL_METRICAS,
)
from src.io.precargado import load_base_2025
from src.logica.lineas_contables import (
    calcular_ratios_base_2025,
    proyectar_lineas_base_2025,
)
from src.logica.lineas_transaccionales import (
    calcular_ratios_base_2026,
    proyectar_lineas_base_2026,
)
from src.logica.mapeo_canal import mapear_canal
from src.logica.proyeccion_asp import proyectar_asp
from src.logica.proyeccion_gb import proyectar_gb
from src.logica.proyeccion_orders import proyectar_orders


_KEY_COLS = ["pais", "marca", "viaje", "producto"]


_DIAS_DEL_MES: dict[int, int] = {
    1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
    7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31,
}


def _agregar_pivot(
    base_2026: pd.DataFrame,
    mes_pivot: int,
    dia_corte: int | None = None,
) -> pd.DataFrame:
    """Agrega Base 2026 al nivel de combo para el mes pivot.

    Si `dia_corte` está dado, los valores se annualizan al mes completo
    multiplicando por `dias_del_mes / dia_corte` (equivale al MTD cierre
    del Excel original).
    """
    df = base_2026.loc[base_2026["Mes RI"] == mes_pivot].copy()
    df = df.rename(columns={"productooriginal": "producto"})

    numeric_cols = ["gross_bookings", "orders"]
    agg = (
        df.groupby(_KEY_COLS, dropna=False)[numeric_cols]
        .sum()
        .reset_index()
    )
    if dia_corte:
        factor = _DIAS_DEL_MES.get(mes_pivot, 30) / dia_corte
        agg["orders"] = agg["orders"] * factor
        agg["gross_bookings"] = agg["gross_bookings"] * factor
    return agg


def build_pnl(
    base_2026: pd.DataFrame,
    mes_pivot: int,
    horizonte: int = 12,
    base_2025: pd.DataFrame | None = None,
    escenario: str | None = None,
    dia_corte: int | None = None,
) -> pd.DataFrame:
    """Construye el P&L proyectado a partir de Base 2026 y Base 2025.

    Args:
        dia_corte: si está dado, indica que Base 2026 del mes pivot es MTD
            parcial al día N. Annualiza orders / GB por dias_del_mes / N.
            Default None = se asume mes completo.
    """
    if base_2025 is None:
        base_2025 = load_base_2025()

    # 1) Pivot por combo
    pivot = _agregar_pivot(base_2026, mes_pivot, dia_corte=dia_corte)

    # 2) Proyección de orders, asp, gb
    orders_proy = proyectar_orders(pivot, mes_pivot, horizonte)
    asp_proy = proyectar_asp(pivot, mes_pivot, horizonte)
    gb_proy = proyectar_gb(orders_proy, asp_proy)

    # 3) Líneas de Base 2026
    ratios_b2026 = calcular_ratios_base_2026(base_2026, mes_pivot)
    pnl = proyectar_lineas_base_2026(gb_proy, ratios_b2026)

    # 4) Líneas de Base 2025
    ratios_b2025 = calcular_ratios_base_2025(base_2025, mes_pivot)
    pnl = proyectar_lineas_base_2025(pnl, ratios_b2025)

    # 5) Ajustes especiales
    for linea in LINEAS_EN_CERO:
        pnl[linea] = 0.0

    # Asegurar que todas las líneas P&L existan como columna numérica.
    todas = (
        set(LINEAS_DESDE_BASE_2026)
        | set(LINEAS_DESDE_BASE_2025)
        | set(LINEAS_EN_CERO)
        | set(PNL_METRICAS)
    )
    for linea in todas:
        if linea not in pnl.columns:
            pnl[linea] = 0.0

    # efecto_financiero en Brasil neto de cost_of_installments
    mask_brasil = pnl["pais"].astype(str).str.casefold().eq("brasil") | pnl[
        "pais"
    ].astype(str).str.casefold().eq("brazil")
    pnl.loc[mask_brasil, "efecto_financiero"] = (
        pnl.loc[mask_brasil, "efecto_financiero"]
        - pnl.loc[mask_brasil, "cost_of_installments"]
    )

    # 6) Métricas derivadas
    pnl["net_revenue"] = pnl[COLS_NET_REVENUE].sum(axis=1)
    pnl["npv"] = pnl[COLS_NPV].sum(axis=1)
    pnl["bimo"] = pnl[COLS_BIMO].sum(axis=1)
    pnl["revenue_margin"] = pnl[COLS_REVENUE_MARGIN].sum(axis=1)

    # 7) Construcción de dimensiones
    pnl["lob_canal"] = "HTML"
    if "marca" in pnl.columns:
        pass  # ya está
    pnl["partner"] = pd.NA
    pnl["escenario"] = escenario if escenario is not None else pd.NA
    pnl["mes_pivot"] = mes_pivot

    # concatenado = pais & lob_canal & marca & viaje & producto
    pnl["concatenado"] = (
        pnl["pais"].astype(str)
        + pnl["lob_canal"].astype(str)
        + pnl["marca"].astype(str)
        + pnl["viaje"].astype(str)
        + pnl["producto"].astype(str)
    )

    pnl = pnl[PNL_DIMENSIONES + PNL_METRICAS].copy()
    pnl = pnl.sort_values(
        ["pais", "marca", "viaje", "producto", "mes_proyectado"]
    ).reset_index(drop=True)

    return pnl
