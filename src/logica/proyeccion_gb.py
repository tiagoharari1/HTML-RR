"""
Cálculo de gross_bookings proyectado: orders_proyectado × ASP_proyectado.
"""
from __future__ import annotations

import pandas as pd


_KEY_COLS = [
    "pais",
    "marca",
    "viaje",
    "producto",
    "numero_mes_proyectado",
    "mes_proyectado",
]


def proyectar_gb(orders_proy: pd.DataFrame, asp_proy: pd.DataFrame) -> pd.DataFrame:
    """Combina orders y ASP proyectados y calcula GB = orders × ASP.

    Returns:
        DataFrame con _KEY_COLS + orders + asp + gross_bookings.
    """
    merged = orders_proy.merge(asp_proy, on=_KEY_COLS, how="outer")
    merged["orders"] = merged["orders"].fillna(0.0)
    merged["asp"] = merged["asp"].fillna(0.0)
    merged["gross_bookings"] = merged["orders"] * merged["asp"]
    return merged
