"""Tests de los readers y validators (M2, M3, M4)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from config.settings import (
    COLS_BASE_2026_OBLIGATORIAS,
    COLS_TRANSACCIONALES,
    ROOT_DIR,
)
from src.io.readers import read_base_2026
from src.io.validators import validate_base_2026

# Archivo real de referencia usado en los tests de M2.
PATH_BASE_2026_REF: Path = ROOT_DIR / "data" / "referencia" / "base 2026.xlsx"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _df_base_minimo_valido() -> pd.DataFrame:
    """Construye un DataFrame mínimo que pasa todas las validaciones."""
    fila = {
        "Mes RI": 3,
        "marca": "Best Day",
        "LOB": "B2B",
        "pais": "Argentina",
        "productooriginal": "Hotels",
        "viaje": "Domestic",
        "gross_bookings": 1000.0,
        "orders": 10,
    }
    for col in COLS_TRANSACCIONALES:
        fila[col] = 0.0
    return pd.DataFrame([fila, fila])


# ---------------------------------------------------------------------------
# read_base_2026
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not PATH_BASE_2026_REF.exists(), reason="Falta base 2026.xlsx de referencia")
def test_read_base_2026_columnas_obligatorias() -> None:
    df = read_base_2026(PATH_BASE_2026_REF)

    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0

    faltantes = [c for c in COLS_BASE_2026_OBLIGATORIAS if c not in df.columns]
    assert not faltantes, f"Faltan columnas obligatorias: {faltantes}"

    faltantes_trans = [c for c in COLS_TRANSACCIONALES if c not in df.columns]
    assert not faltantes_trans, f"Faltan columnas transaccionales: {faltantes_trans}"


@pytest.mark.skipif(not PATH_BASE_2026_REF.exists(), reason="Falta base 2026.xlsx de referencia")
def test_read_base_2026_archivo_real_pasa_validacion() -> None:
    df = read_base_2026(PATH_BASE_2026_REF)
    assert validate_base_2026(df) == []


# ---------------------------------------------------------------------------
# validate_base_2026
# ---------------------------------------------------------------------------
def test_validate_base_2026_df_minimo_es_valido() -> None:
    assert validate_base_2026(_df_base_minimo_valido()) == []


def test_validate_base_2026_df_vacio_devuelve_error() -> None:
    errores = validate_base_2026(pd.DataFrame())
    assert len(errores) == 1
    assert "vacía" in errores[0].lower()


def test_validate_base_2026_columna_obligatoria_faltante() -> None:
    df = _df_base_minimo_valido().drop(columns=["gross_bookings"])
    errores = validate_base_2026(df)
    assert any("gross_bookings" in e for e in errores)


def test_validate_base_2026_columna_transaccional_faltante() -> None:
    df = _df_base_minimo_valido().drop(columns=["fees"])
    errores = validate_base_2026(df)
    assert any("fees" in e for e in errores)


def test_validate_base_2026_null_en_obligatoria() -> None:
    df = _df_base_minimo_valido()
    df.loc[0, "pais"] = None
    errores = validate_base_2026(df)
    assert any("pais" in e and "nulos" in e for e in errores)


def test_validate_base_2026_mes_ri_fuera_de_rango() -> None:
    df = _df_base_minimo_valido()
    df.loc[0, "Mes RI"] = 13
    errores = validate_base_2026(df)
    assert any("Mes RI" in e and "rango" in e for e in errores)


def test_validate_base_2026_lob_invalido() -> None:
    df = _df_base_minimo_valido()
    df.loc[0, "LOB"] = "Retail"
    errores = validate_base_2026(df)
    assert any("LOB" in e and "Retail" in e for e in errores)


# TODO M3 — test_read_contable_columnas_obligatorias
# TODO M4 — test_load_macro_estructura
