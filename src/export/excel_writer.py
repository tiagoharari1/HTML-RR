"""
Escritor de Excel para el P&L final descargable.

Genera un archivo .xlsx en memoria con la hoja `P&L` respetando el orden
de columnas del Excel original.
"""
from __future__ import annotations

import io

import pandas as pd

from config.settings import PNL_DIMENSIONES, PNL_METRICAS


NOMBRE_HOJA_PNL: str = "P&L"


def write_pnl_excel(df_pnl: pd.DataFrame) -> bytes:
    """Devuelve los bytes de un Excel con la hoja P&L."""
    cols = [c for c in (PNL_DIMENSIONES + PNL_METRICAS) if c in df_pnl.columns]
    df = df_pnl[cols].copy()

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name=NOMBRE_HOJA_PNL, index=False)
        ws = writer.sheets[NOMBRE_HOJA_PNL]
        # Ancho cómodo en las primeras columnas dimensionales
        ws.set_column(0, len(PNL_DIMENSIONES) - 1, 18)
        ws.set_column(len(PNL_DIMENSIONES), len(cols) - 1, 14)
    buffer.seek(0)
    return buffer.read()
