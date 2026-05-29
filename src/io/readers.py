"""
Lectores de los archivos que sube el usuario.

  - read_base_2026: input transaccional MTD
  - read_contable: tabla contable (en v1 sólo como referencia, no drivea P&L)
"""
from __future__ import annotations

from pathlib import Path
from typing import IO, Union

import pandas as pd

FileLike = Union[str, Path, IO[bytes]]

NOMBRE_HOJA_BASE_2026: str = "Base 2026"
NOMBRE_HOJA_CONTABLE: str = "Contable"


def _read_with_fallback(file: FileLike, sheet_name: str) -> pd.DataFrame:
    """Lee `sheet_name` y se cae a la primera hoja si no existe."""
    try:
        return pd.read_excel(file, sheet_name=sheet_name)
    except ValueError:
        if hasattr(file, "seek"):
            file.seek(0)  # type: ignore[union-attr]
        return pd.read_excel(file, sheet_name=0)


def read_base_2026(
    file: FileLike,
    sheet_name: str | int | None = None,
) -> pd.DataFrame:
    """Lee la hoja Base 2026 del Excel cargado por el usuario."""
    if sheet_name is not None:
        return pd.read_excel(file, sheet_name=sheet_name)
    return _read_with_fallback(file, NOMBRE_HOJA_BASE_2026)


def read_contable(
    file: FileLike,
    sheet_name: str | int | None = None,
) -> pd.DataFrame:
    """Lee la hoja Contable del Excel cargado por el usuario."""
    if sheet_name is not None:
        return pd.read_excel(file, sheet_name=sheet_name)
    return _read_with_fallback(file, NOMBRE_HOJA_CONTABLE)
