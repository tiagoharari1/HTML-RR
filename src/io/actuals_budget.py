"""
Módulo de carga de actuals y budget desde CSVs pre-cargados.

Lee `output/actuals.csv` y `output/budget.csv`, filtra por LoB=="B2B" y
Channel=="MIN", mapea líneas P&L a columnas internas de PNL_METRICAS, y
expone dos funciones cacheadas: `load_actuals()` y `load_budget()`.
"""
from __future__ import annotations

import unicodedata

import pandas as pd
import streamlit as st

from config.settings import (
    COLS_BIMO,
    COLS_NET_REVENUE,
    COLS_NPV,
    COLS_REVENUE_MARGIN,
    PNL_METRICAS,
    ROOT_DIR,
)

# ---------------------------------------------------------------------------
# Paths a los CSVs
# ---------------------------------------------------------------------------
_PATH_ACTUALS = ROOT_DIR / "output" / "actuals.csv"
_PATH_BUDGET = ROOT_DIR / "output" / "budget.csv"

# ---------------------------------------------------------------------------
# Mapeo de meses en inglés → número
# ---------------------------------------------------------------------------
_MES_NOMBRE_A_NUM: dict[str, int] = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}


def _norm(s: str) -> str:
    """Normaliza un string: elimina tildes, pasa a minúsculas y recorta espacios."""
    return "".join(
        c
        for c in unicodedata.normalize("NFD", str(s))
        if unicodedata.category(c) != "Mn"
    ).lower().strip()


# ---------------------------------------------------------------------------
# Mapeo normalizado: clave normalizada → nombre interno de PNL_METRICAS
# ---------------------------------------------------------------------------
# Las claves ya están normalizadas con _norm() para que soporten problemas
# de encoding en los CSV (p. ej. "Gross Bookings Dom�stico" → "gross bookings domestico").
_MAPEO_LINEAS: dict[str, str] = {
    "orders domestic": "orders",
    "orders international": "orders",
    "gross bookings domestico": "gross_bookings",
    "gross bookings internacional": "gross_bookings",
    "up front incentives": "up_front_incentives",
    "back end incentives": "back_end_incentives",
    "customer fees & charges": "fees",
    "o. incentives": "other_incentives",
    "breakage revenue": "breakage_revenue",
    "media & other revenue": "media_revenue",
    "income from outsourced services": "income_from_outsourced_services",
    "cancellations": "cancellations",
    "rev. taxes": "revenue_tax",
    "cost of installments": "cost_of_installments",
    "credit card processing": "credit_card_processing",
    "errors": "errors",
    "customer claims": "customer_claims",
    "fulfillment center fees": "customer_service",
    "bad debt": "frauds",
    "frauds": "frauds",
    "o. transactional taxes": "other_transactional_taxes",
    "intercomp. transactions": "intercompany",
    "third party comission": "white_labels_api",
    "marketing - direct": "affiliates",
    "cost of sales as principal": "dif_fx",
}


def _calcular_derivadas(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula net_revenue, npv, bimo y revenue_margin usando las mismas fórmulas
    que el pnl_builder de proyección."""
    # Asegura que todas las columnas requeridas existen (rellena con 0 si no)
    for col in PNL_METRICAS:
        if col not in df.columns:
            df[col] = 0.0

    df["net_revenue"] = df[[c for c in COLS_NET_REVENUE if c in df.columns]].sum(axis=1)
    df["npv"] = df[[c for c in COLS_NPV if c in df.columns]].sum(axis=1)
    df["bimo"] = df[[c for c in COLS_BIMO if c in df.columns]].sum(axis=1)
    df["revenue_margin"] = df[[c for c in COLS_REVENUE_MARGIN if c in df.columns]].sum(axis=1)
    return df


def _leer_csv(path) -> pd.DataFrame:
    """Lee un CSV con encoding utf-8-sig y separador auto-detectado."""
    return pd.read_csv(path, encoding="utf-8-sig", sep=None, engine="python")


def _procesar_csv(path) -> pd.DataFrame:
    """Carga un CSV de actuals/budget, filtra, mapea líneas y pivota a una fila por mes.

    Retorna un DataFrame con columnas: "mes" (int 1-12) + todas las PNL_METRICAS.
    """
    df = _leer_csv(path)

    # Filtrar solo B2B / MIN
    df = df[(df["LoB"] == "B2B") & (df["Channel"] == "MIN")].copy()

    # Convertir valor: el CSV usa coma como separador decimal
    df["valor"] = (
        df["Baseline scenarios"]
        .astype(str)
        .str.replace(",", ".", regex=False)
    )
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0.0)

    # Mapear mes nombre → número
    df["mes"] = df["Month"].map(_MES_NOMBRE_A_NUM)
    df = df[df["mes"].notna()].copy()
    df["mes"] = df["mes"].astype(int)

    # Normalizar nombre de línea y mapear a nombre interno
    df["linea_norm"] = df["Linea P&L - Nivel 2"].apply(_norm)
    df["linea_interna"] = df["linea_norm"].map(_MAPEO_LINEAS)

    # Descartar filas sin mapeo conocido
    df = df[df["linea_interna"].notna()].copy()

    # Agrupar por mes + linea_interna (sumar, p. ej. orders dom + int)
    agregado = (
        df.groupby(["mes", "linea_interna"], as_index=False)["valor"]
        .sum()
    )

    # Pivotar: una fila por mes, una columna por línea interna
    pivotado = agregado.pivot(index="mes", columns="linea_interna", values="valor")
    pivotado.columns.name = None
    pivotado = pivotado.reset_index()

    # Rellenar métricas faltantes con 0
    for col in PNL_METRICAS:
        if col not in pivotado.columns:
            pivotado[col] = 0.0

    # Calcular métricas derivadas
    pivotado = _calcular_derivadas(pivotado)

    # Retornar solo columnas relevantes en el orden de PNL_METRICAS
    cols_out = ["mes"] + PNL_METRICAS
    return pivotado[[c for c in cols_out if c in pivotado.columns]]


@st.cache_data
def load_actuals() -> pd.DataFrame:
    """Carga y cachea los datos de actuals.csv.

    Retorna un DataFrame con columnas: "mes" (int 1–12) + todas las PNL_METRICAS.
    Filtra LoB=="B2B" y Channel=="MIN". Los valores ya están en la moneda del CSV.
    """
    return _procesar_csv(_PATH_ACTUALS)


@st.cache_data
def load_budget() -> pd.DataFrame:
    """Carga y cachea los datos de budget.csv.

    Retorna un DataFrame con columnas: "mes" (int 1–12) + todas las PNL_METRICAS.
    Filtra LoB=="B2B" y Channel=="MIN". Los valores ya están en la moneda del CSV.
    """
    return _procesar_csv(_PATH_BUDGET)
