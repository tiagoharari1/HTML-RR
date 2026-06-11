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
    usar_mediana: bool = True,
) -> pd.DataFrame:
    """Calcula ratio = linea / gross_bookings para cada combo.

    Si `usar_mediana` (default), el ratio es la **mediana** de los ratios
    mensuales de todos los meses disponibles hasta el pivot (más robusto a
    outliers de un mes atípico). Si no, replica la v1 usando sólo el mes pivot.

    Returns:
        DataFrame con _KEY_COLS + una columna `ratio_<linea>` por cada línea.
    """
    df = base_2026.rename(columns={"productooriginal": "producto"}).copy()
    cols_existentes = [c for c in LINEAS_DESDE_BASE_2026 if c in df.columns]

    if usar_mediana:
        ratios = _ratio_mediana_por_combo(
            df, "Mes RI", mes_pivot, cols_existentes, LINEAS_DESDE_BASE_2026
        )
    else:
        ratios = _ratio_pivot_por_combo(
            df.loc[df["Mes RI"] == mes_pivot],
            cols_existentes,
            LINEAS_DESDE_BASE_2026,
        )

    keep = _KEY_COLS + [f"ratio_{l}" for l in LINEAS_DESDE_BASE_2026]
    return ratios[keep]


def _ratio_pivot_por_combo(
    df: pd.DataFrame,
    cols_existentes: list[str],
    lineas: list[str],
) -> pd.DataFrame:
    """Ratio línea/GB por combo agregando un único mes (comportamiento v1)."""
    agg = (
        df.groupby(_KEY_COLS, dropna=False)[["gross_bookings", *cols_existentes]]
        .sum()
        .reset_index()
    )
    for linea in lineas:
        if linea in cols_existentes:
            agg[f"ratio_{linea}"] = agg.apply(
                lambda r: (r[linea] / r["gross_bookings"]) if r["gross_bookings"] else 0.0,
                axis=1,
            )
        else:
            agg[f"ratio_{linea}"] = 0.0
    return agg


def _ratio_mediana_por_combo(
    df: pd.DataFrame,
    col_mes: str,
    mes_pivot: int,
    cols_existentes: list[str],
    lineas: list[str],
) -> pd.DataFrame:
    """Ratio línea/GB por combo como mediana de los ratios mensuales.

    Considera los meses disponibles con `col_mes <= mes_pivot`. Para cada combo
    y mes calcula linea/GB (ignorando meses con GB=0), y toma la mediana entre
    meses. Si el combo sólo tiene un mes, la mediana es ese ratio.
    """
    sub = df.loc[df[col_mes] <= mes_pivot].copy()
    if sub.empty:  # sin meses previos: cae al pivot exacto
        sub = df.loc[df[col_mes] == mes_pivot].copy()

    por_mes = (
        sub.groupby([*_KEY_COLS, col_mes], dropna=False)[
            ["gross_bookings", *cols_existentes]
        ]
        .sum()
        .reset_index()
    )

    combos = por_mes[_KEY_COLS].drop_duplicates().reset_index(drop=True)
    for linea in lineas:
        if linea in cols_existentes:
            gb = por_mes["gross_bookings"]
            ratio_mes = (por_mes[linea] / gb).where(gb != 0)
            tmp = por_mes[_KEY_COLS].assign(_r=ratio_mes)
            mediana = (
                tmp.groupby(_KEY_COLS, dropna=False)["_r"].median().reset_index()
            )
            combos = combos.merge(mediana, on=_KEY_COLS, how="left")
            combos = combos.rename(columns={"_r": f"ratio_{linea}"})
            combos[f"ratio_{linea}"] = combos[f"ratio_{linea}"].fillna(0.0)
        else:
            combos[f"ratio_{linea}"] = 0.0
    return combos


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
