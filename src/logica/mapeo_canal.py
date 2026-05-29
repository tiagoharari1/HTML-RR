"""
Mapeo del canal LOB="B2B" (Base 2026) a lob_canal="HTML" (P&L output).
"""
from __future__ import annotations

import pandas as pd

from config.settings import MAPEO_LOB_CANAL


def mapear_canal(lob: str | float | None) -> str:
    """Devuelve el lob_canal correspondiente al LOB de Base 2026.

    Si el LOB no está mapeado devuelve el valor original como string.
    """
    if lob is None or (isinstance(lob, float) and pd.isna(lob)):
        return ""
    lob_str = str(lob)
    return MAPEO_LOB_CANAL.get(lob_str, lob_str)
