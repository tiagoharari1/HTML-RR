"""
Proyección de líneas transaccionales como ratio MTD sobre gross_bookings.

Aplica para las líneas listadas en `LINEAS_DESDE_BASE_2026` (Modelo Palancas
+ upf-fees + other_incentives en el Excel original):
    up_front_incentives, fees, cost_of_installments, credit_card_processing,
    affiliates, cancellations, other_incentives.

Fórmula:
    ratio[combo, linea] = Base2026[linea, combo, mes_pivot]
                        / Base2026[gross_bookings, combo, mes_pivot]
    linea_proy[combo, m] = ratio[combo, linea] × GB_proy[combo, m]
"""
from __future__ import annotations

import pandas as pd

from config.settings import LINEAS_DESDE_BASE_2026

_KEY_COLS = ["pais", "marca", "viaje", "producto"]


def calcular_ratios_base_2026(
    base_2026: pd.DataFrame,
    mes_pivot: int,
) -> pd.DataFrame:
    """Calcula ratio = linea / gross_bookings para cada combo en mes_pivot.

    Returns:
        DataFrame con _KEY_COLS + una columna `ratio_<linea>` por cada línea.
    """
    df = base_2026.loc[base_2026["Mes RI"] == mes_pivot].copy()
    df = df.rename(columns={"productooriginal": "producto"})

    cols_existentes = [c for c in LINEAS_DESDE_BASE_2026 if c in df.columns]
    agg = (
        df.groupby(_KEY_COLS, dropna=False)[["gross_bookings", *cols_existentes]]
        .sum()
        .reset_index()
    )

    for linea in LINEAS_DESDE_BASE_2026:
        if linea in cols_existentes:
            agg[f"ratio_{linea}"] = agg.apply(
                lambda r: (r[linea] / r["gross_bookings"]) if r["gross_bookings"] else 0.0,
                axis=1,
            )
        else:
            agg[f"ratio_{linea}"] = 0.0

    keep = _KEY_COLS + [f"ratio_{l}" for l in LINEAS_DESDE_BASE_2026]
    return agg[keep]


def proyectar_lineas_base_2026(
    gb_proy: pd.DataFrame,
    ratios_b2026: pd.DataFrame,
) -> pd.DataFrame:
    """Aplica los ratios de Base 2026 al gross_bookings proyectado.

    Returns:
        DataFrame con las mismas dimensiones que `gb_proy` y una columna por
        cada línea proyectada.
    """
    merged = gb_proy.merge(ratios_b2026, on=_KEY_COLS, how="left")
    for linea in LINEAS_DESDE_BASE_2026:
        col_ratio = f"ratio_{linea}"
        merged[col_ratio] = merged[col_ratio].fillna(0.0)
        merged[linea] = merged[col_ratio] * merged["gross_bookings"]
        merged.drop(columns=[col_ratio], inplace=True)

    return merged
