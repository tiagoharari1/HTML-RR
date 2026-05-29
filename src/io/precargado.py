"""
Loaders de las hojas pre-cargadas que vienen con la app:
  - Macro (FX y CPI por país y mes) — se carga pero v1 no la aplica al P&L.
  - Estacionalidad orders B2B
  - Estacionalidad B2B ASP
  - Base 2025 (histórica, drivea ~16 líneas del P&L vía ratios)

Todos los loaders cachean en memoria con functools.lru_cache para evitar
re-leer los archivos en cada rerun de Streamlit.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

from config.settings import (
    PATH_BASE_2025,
    PATH_ESTACIONALIDAD_ASP,
    PATH_ESTACIONALIDAD_ORDERS,
    PATH_MACRO,
)

# Fila en la que arrancan los headers en las hojas de Estacionalidad
# (heredada del Excel original — las primeras 4 filas están vacías).
_FILA_HEADER_ESTACIONALIDAD: int = 4  # 0-indexed

# Columnas de las estacionalidades que representan los meses calendario 1..12.
# En el Excel original son las columnas I..T (índices 8..19 0-indexed).
_COLS_MES_CAL: list[int] = list(range(8, 20))


def _read_estacionalidad(path: Path) -> pd.DataFrame:
    """Lee una hoja de estacionalidad y devuelve un DataFrame normalizado.

    Output:
      columnas = ['concatenado', 'pais', 'lob_canal', 'marca', 'viaje',
                  'producto_agrupado', 'mes_pivot', 1, 2, ..., 12]

    `concatenado` es la clave de lookup usada por Modelo Orders / ASP:
    `pais & viaje & producto_agrupado` (no incluye marca ni canal).
    """
    raw = pd.read_excel(path, header=None)
    body = raw.iloc[_FILA_HEADER_ESTACIONALIDAD + 1:].reset_index(drop=True)

    out = pd.DataFrame({
        "concatenado": body.iloc[:, 0],
        "pais": body.iloc[:, 1],
        "lob_canal": body.iloc[:, 2],
        "marca": body.iloc[:, 3],
        "viaje": body.iloc[:, 4],
        "producto_agrupado": body.iloc[:, 5],
        "mes_pivot": body.iloc[:, 6],
    })
    for i, src_col in enumerate(_COLS_MES_CAL, start=1):
        out[i] = pd.to_numeric(body.iloc[:, src_col], errors="coerce").fillna(1.0)

    out = out.dropna(subset=["concatenado"]).reset_index(drop=True)
    return out


@lru_cache(maxsize=1)
def load_estacionalidad_orders() -> pd.DataFrame:
    """Carga la hoja Estacionalidad orders B2B normalizada."""
    return _read_estacionalidad(PATH_ESTACIONALIDAD_ORDERS)


@lru_cache(maxsize=1)
def load_estacionalidad_asp() -> pd.DataFrame:
    """Carga la hoja Estacionalidad B2B ASP normalizada."""
    return _read_estacionalidad(PATH_ESTACIONALIDAD_ASP)


@lru_cache(maxsize=1)
def load_macro() -> pd.DataFrame:
    """Carga Macro (FX y CPI). v1 no la usa para el cálculo del P&L."""
    df = pd.read_excel(PATH_MACRO, header=None)
    return df


@lru_cache(maxsize=1)
def load_base_2025() -> pd.DataFrame:
    """Carga Base 2025 (histórica)."""
    df = pd.read_excel(PATH_BASE_2025, header=0)
    return df


def precargados_disponibles() -> dict[str, bool]:
    """Verifica si los archivos pre-cargados existen en disco."""
    return {
        "macro": PATH_MACRO.exists(),
        "estacionalidad_orders": PATH_ESTACIONALIDAD_ORDERS.exists(),
        "estacionalidad_asp": PATH_ESTACIONALIDAD_ASP.exists(),
        "base_2025": PATH_BASE_2025.exists(),
    }
