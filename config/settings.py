"""
Constantes y configuración general de la app RR AI.

Centraliza paths, mapeos, listas de países / productos, y nombres de columnas
esperadas para no hardcodearlas en la lógica de negocio.
"""
from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT_DIR: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = ROOT_DIR / "data"
PRECARGADO_DIR: Path = DATA_DIR / "precargado"
EJEMPLOS_DIR: Path = DATA_DIR / "ejemplos"
REFERENCIA_DIR: Path = DATA_DIR / "referencia"

PATH_MACRO: Path = PRECARGADO_DIR / "macro.xlsx"
PATH_ESTACIONALIDAD_ORDERS: Path = PRECARGADO_DIR / "estacionalidad_orders.xlsx"
PATH_ESTACIONALIDAD_ASP: Path = PRECARGADO_DIR / "estacionalidad_asp.xlsx"
PATH_BASE_2025: Path = PRECARGADO_DIR / "base_2025.xlsx"


# ---------------------------------------------------------------------------
# Mapeos de negocio
# ---------------------------------------------------------------------------
# Toda la Base 2026 viene rotulada como B2B; en el P&L output usamos HTML.
MAPEO_LOB_CANAL: dict[str, str] = {
    "B2B": "HTML",
}

# Códigos de país usados en Macro y Contable
PAISES: list[str] = ["AR", "BR", "MX", "CL", "CO", "EC", "PE", "OT"]

# Mapeo nombre largo -> código de país.
# "Other Countries", "Uruguay" y "Paraguay" se agrupan en "OT" igual que en
# el Excel de referencia.
MAPEO_PAIS_CODIGO: dict[str, str] = {
    "Argentina": "AR",
    "Brasil": "BR",
    "Brazil": "BR",
    "Mexico": "MX",
    "México": "MX",
    "Chile": "CL",
    "Colombia": "CO",
    "Ecuador": "EC",
    "Peru": "PE",
    "Perú": "PE",
    "Other Countries": "OT",
    "Uruguay": "OT",
    "Paraguay": "OT",
}


# ---------------------------------------------------------------------------
# Columnas esperadas en Base 2026 (subset crítico)
# ---------------------------------------------------------------------------
COLS_BASE_2026_OBLIGATORIAS: list[str] = [
    "Mes RI",
    "marca",
    "LOB",
    "pais",
    "productooriginal",
    "viaje",
    "gross_bookings",
    "orders",
]

# Líneas P&L que se proyectan como ratio_MTD(linea / gross_bookings) × GB_proy,
# usando Base 2026 como fuente del ratio. En el Excel original estas líneas
# salen de "Modelo Palancas" + "upf-fees" + "Base 2026" — todas comparten el
# mismo mecanismo (ratio MTD sobre GB).
COLS_TRANSACCIONALES: list[str] = [
    "up_front_incentives",
    "fees",
    "commercial_discounts",
    "cost_of_installments",
    "credit_card_processing",
    "affiliates",
    "other_incentives",
    "errors",
    "revenue_tax",
    "other_transactional_taxes",
    "cancellations",
    "breakage_revenue",
    "customer_claims",
    "customer_service",
    "media_revenue",
    "frauds",
    "efecto_financiero",
    "dif_fx",
    "currency_hedge",
]

# Subset de líneas que SI driverean el P&L desde Base 2026
# (ratio Base 2026 line / Base 2026 gross_bookings × GB_proy).
# El Excel original llama a esto "Modelo Palancas" + "upf-fees" + "other_incentives".
LINEAS_DESDE_BASE_2026: list[str] = [
    "up_front_incentives",
    "fees",
    "cost_of_installments",
    "credit_card_processing",
    "affiliates",
    "cancellations",
    "other_incentives",
]


# ---------------------------------------------------------------------------
# Columnas esperadas en Contable
# ---------------------------------------------------------------------------
# Contable en v1 NO drivea el P&L (el Excel original tampoco lo usa para esto).
# Se mantiene en el wizard sólo como tabla de referencia opcional.
COLS_CONTABLE_OBLIGATORIAS: list[str] = [
    "FuturoNombre",
    "LoB",
    "Origen",
    "Codigopais",
    "Prod_Corregido",
    "Linea P&L",
    "P&L OK",
    "pais",
    "producto",
]


# ---------------------------------------------------------------------------
# Líneas P&L que salen de Base 2025 (histórica)
# ---------------------------------------------------------------------------
# Ratio Base_2025[linea] / Base_2025[gross_bookings] × GB_proyectado.
# En el Excel original son las 16 líneas que P&L pulla con SUMIFS a Base 2025.
LINEAS_DESDE_BASE_2025: list[str] = [
    "income_from_outsourced_services",
    "errors",
    "revenue_tax",
    "other_transactional_taxes",
    "back_end_incentives",
    "breakage_revenue",
    "customer_claims",
    "customer_service",
    "media_revenue",
    "vendor_commissions",
    "intercompany",
    "white_labels_api",
    "operations",
    "frauds",
    "efecto_financiero",
    "dif_fx",
    "currency_hedge",
]

# Líneas P&L con valor fijo en 0 (en el Excel de referencia v1).
LINEAS_EN_CERO: list[str] = [
    "commercial_discounts",
]


# ---------------------------------------------------------------------------
# Mapeo producto -> producto_agrupado (clave de Estacionalidad)
# ---------------------------------------------------------------------------
# El Excel original colapsa varios productos en "ONA" (One Non-Air) para usar
# la misma curva de estacionalidad.
MAPEO_PRODUCTO_AGRUPADO: dict[str, str] = {
    "Flights": "Flights",
    "Hotels": "Hotels",
    "Packages General": "Packages General",
    "Cars": "ONA",
    "Cruises": "ONA",
    "Dest. Serv.": "ONA",
    "Insurance": "ONA",
    "Vacation Rentals": "ONA",
    "Bundles": "Packages General",
}


# ---------------------------------------------------------------------------
# Schema del P&L output (dimensiones + métricas)
# ---------------------------------------------------------------------------
PNL_DIMENSIONES: list[str] = [
    "concatenado",
    "escenario",
    "mes_pivot",
    "pais",
    "lob_canal",
    "marca",
    "partner",
    "viaje",
    "producto",
    "numero_mes_proyectado",
    "mes_proyectado",
]

# Orden exacto de las métricas en la hoja P&L del Excel original.
PNL_METRICAS: list[str] = [
    "orders",
    "gross_bookings",
    "up_front_incentives",
    "fees",
    "cost_of_installments",
    "credit_card_processing",
    "affiliates",
    "cancellations",
    "income_from_outsourced_services",
    "other_incentives",
    "errors",
    "revenue_tax",
    "other_transactional_taxes",
    "back_end_incentives",
    "commercial_discounts",
    "breakage_revenue",
    "customer_claims",
    "customer_service",
    "media_revenue",
    "vendor_commissions",
    "intercompany",
    "white_labels_api",
    "operations",
    "frauds",
    "efecto_financiero",
    "dif_fx",
    "currency_hedge",
    "net_revenue",
    "npv",
    "bimo",
    "revenue_margin",
]

# Composición de las métricas derivadas (replica el Excel original):
#   net_revenue   = up_front_incentives + fees + cancellations + income_from_outsourced_services
#                 + other_incentives + revenue_tax + back_end_incentives + commercial_discounts
#                 + breakage_revenue + media_revenue
#   npv           = SUM(up_front_incentives..currency_hedge)
#   bimo          = dif_fx + currency_hedge   (replicado tal cual del Excel)
#   revenue_margin = up_front_incentives + fees + cancellations
COLS_NET_REVENUE: list[str] = [
    "up_front_incentives",
    "fees",
    "cancellations",
    "income_from_outsourced_services",
    "other_incentives",
    "revenue_tax",
    "back_end_incentives",
    "commercial_discounts",
    "breakage_revenue",
    "media_revenue",
]
COLS_NPV: list[str] = [
    "up_front_incentives",
    "fees",
    "cost_of_installments",
    "credit_card_processing",
    "affiliates",
    "cancellations",
    "income_from_outsourced_services",
    "other_incentives",
    "errors",
    "revenue_tax",
    "other_transactional_taxes",
    "back_end_incentives",
    "commercial_discounts",
    "breakage_revenue",
    "customer_claims",
    "customer_service",
    "media_revenue",
    "vendor_commissions",
    "intercompany",
    "white_labels_api",
    "operations",
    "frauds",
    "efecto_financiero",
    "dif_fx",
    "currency_hedge",
]
COLS_BIMO: list[str] = ["dif_fx", "currency_hedge"]
COLS_REVENUE_MARGIN: list[str] = ["up_front_incentives", "fees", "cancellations"]


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
HORIZONTE_DEFAULT: int = 12
HORIZONTE_MIN: int = 1
HORIZONTE_MAX: int = 24
