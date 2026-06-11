"""
Líneas proyectadas a partir de los ratios históricos de Base 2025.

En el diseño original (CLAUDE.md) estas líneas salían de la hoja Contable,
pero el Excel de referencia en realidad pulla los ratios desde Base 2025
(histórica) y los aplica al gross_bookings proyectado.

Aplica a las líneas listadas en `LINEAS_DESDE_BASE_2025`:
    income_from_outsourced_services, errors, revenue_tax,
    other_transactional_taxes, back_end_incentives, breakage_revenue,
    customer_claims, customer_service, media_revenue, vendor_commissions,
    intercompany, white_labels_api, operations, frauds, efecto_financiero,
    dif_fx, currency_hedge.

Fórmula:
    ratio_25[combo, linea] = Base2025[linea, combo, mes_pivot]
                           / Base2025[gross_bookings, combo, mes_pivot]
    linea_proy[combo, m]   = ratio_25[combo, linea] × GB_proy[combo, m]

Nota: si la columna `linea` no existe en Base 2025 (por ejemplo
`back_end_incentives` o `media_revenue` que ahí se llama `media_other_revenue`)
el ratio queda en 0 — mismo comportamiento que el IFERROR del Excel.
"""
from __future__ import annotations

import pandas as pd

from config.settings import LINEAS_DESDE_BASE_2025
from src.logica.lineas_transaccionales import (
    _ratio_mediana_por_combo,
    _ratio_pivot_por_combo,
)

_KEY_COLS = ["pais", "marca", "viaje", "producto"]


def calcular_ratios_base_2025(
    base_2025: pd.DataFrame,
    mes_pivot: int,
    usar_mediana: bool = True,
) -> pd.DataFrame:
    """Calcula ratio = linea / gross_bookings por combo desde Base 2025.

    Si `usar_mediana` (default), usa la **mediana** de los ratios mensuales de
    todos los 12 meses de Base 2025 (histórico completo, más robusto). Si no,
    replica la v1 tomando sólo el mes pivot.

    Returns:
        DataFrame con _KEY_COLS + una columna `ratio_<linea>` por línea.
    """
    df = base_2025.rename(columns={"productooriginal": "producto"}).copy()
    cols_existentes = [c for c in LINEAS_DESDE_BASE_2025 if c in df.columns]

    if usar_mediana:
        # Base 2025 es histórico completo: usamos los 12 meses como muestra
        # (pivot=12 incluye todos los meses disponibles).
        ratios = _ratio_mediana_por_combo(
            df, "Mes", 12, cols_existentes, LINEAS_DESDE_BASE_2025
        )
    else:
        ratios = _ratio_pivot_por_combo(
            df.loc[df["Mes"] == mes_pivot],
            cols_existentes,
            LINEAS_DESDE_BASE_2025,
        )

    keep = _KEY_COLS + [f"ratio_{l}" for l in LINEAS_DESDE_BASE_2025]
    return ratios[keep]


def proyectar_lineas_base_2025(
    gb_proy: pd.DataFrame,
    ratios_b2025: pd.DataFrame,
) -> pd.DataFrame:
    """Aplica los ratios de Base 2025 al gross_bookings proyectado.

    Returns:
        DataFrame con las mismas dimensiones que `gb_proy` y una columna por
        cada línea proyectada de LINEAS_DESDE_BASE_2025.
    """
    merged = gb_proy.merge(ratios_b2025, on=_KEY_COLS, how="left")
    for linea in LINEAS_DESDE_BASE_2025:
        col_ratio = f"ratio_{linea}"
        merged[col_ratio] = merged[col_ratio].fillna(0.0)
        merged[linea] = merged[col_ratio] * merged["gross_bookings"]
        merged.drop(columns=[col_ratio], inplace=True)

    return merged
