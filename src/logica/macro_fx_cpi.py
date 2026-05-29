"""
Aplicación de FX y CPI desde la hoja Macro sobre el P&L proyectado.

v1: pass-through. El Excel de referencia NO aplica Macro a las líneas del P&L
(Base 2026 ya viene en USD). Se mantiene este módulo como hook para v2.
"""
from __future__ import annotations

import pandas as pd


def aplicar_fx_cpi(pnl_df: pd.DataFrame) -> pd.DataFrame:
    """v1: no-op. Devuelve el DataFrame sin modificar."""
    return pnl_df
