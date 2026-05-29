"""
Validación de esquema y tipos de los inputs del usuario.

Devuelven listas de mensajes de error en español. Lista vacía = válido.
"""
from __future__ import annotations

import pandas as pd
from pandas.api.types import is_numeric_dtype

from config.settings import (
    COLS_BASE_2026_OBLIGATORIAS,
    COLS_CONTABLE_OBLIGATORIAS,
    COLS_TRANSACCIONALES,
    MAPEO_LOB_CANAL,
)

_MES_MIN: int = 1
_MES_MAX: int = 12


def validate_base_2026(df: pd.DataFrame) -> list[str]:
    """Valida que un DataFrame cargado desde Base 2026 sea utilizable."""
    errores: list[str] = []

    if df is None or len(df) == 0:
        errores.append("La Base 2026 está vacía.")
        return errores

    faltantes_obligatorias = [c for c in COLS_BASE_2026_OBLIGATORIAS if c not in df.columns]
    if faltantes_obligatorias:
        errores.append(
            "Faltan columnas obligatorias en Base 2026: "
            + ", ".join(faltantes_obligatorias)
        )

    faltantes_trans = [c for c in COLS_TRANSACCIONALES if c not in df.columns]
    if faltantes_trans:
        errores.append(
            "Faltan columnas transaccionales en Base 2026: "
            + ", ".join(faltantes_trans)
        )

    if faltantes_obligatorias:
        return errores

    for col in COLS_BASE_2026_OBLIGATORIAS:
        n_nulos = int(df[col].isna().sum())
        if n_nulos > 0:
            errores.append(
                f"La columna obligatoria '{col}' tiene {n_nulos} valores nulos."
            )

    if not is_numeric_dtype(df["Mes RI"]):
        errores.append("'Mes RI' debe ser numérico (1 a 12).")
    else:
        fuera_rango = df[(df["Mes RI"] < _MES_MIN) | (df["Mes RI"] > _MES_MAX)]
        if len(fuera_rango) > 0:
            errores.append(
                f"'Mes RI' tiene {len(fuera_rango)} valores fuera del rango "
                f"{_MES_MIN}..{_MES_MAX}."
            )

    for col in ("gross_bookings", "orders"):
        if not is_numeric_dtype(df[col]):
            errores.append(f"La columna '{col}' debe ser numérica.")

    lobs_validos = set(MAPEO_LOB_CANAL.keys())
    lobs_invalidos = sorted(
        v for v in df["LOB"].dropna().unique() if v not in lobs_validos
    )
    if lobs_invalidos:
        errores.append(
            "Valores de 'LOB' no reconocidos: "
            + ", ".join(map(str, lobs_invalidos))
            + f". Esperados: {sorted(lobs_validos)}."
        )

    return errores


def validate_contable(df: pd.DataFrame) -> list[str]:
    """Valida la hoja Contable del usuario.

    En v1 Contable se carga como referencia (no drivea el P&L), así que las
    validaciones son livianas: cabecera y al menos un set de columnas
    obligatorias presentes.
    """
    errores: list[str] = []

    if df is None or len(df) == 0:
        errores.append("La hoja Contable está vacía.")
        return errores

    faltantes = [c for c in COLS_CONTABLE_OBLIGATORIAS if c not in df.columns]
    if faltantes:
        errores.append(
            "Faltan columnas obligatorias en Contable: " + ", ".join(faltantes)
        )

    return errores
