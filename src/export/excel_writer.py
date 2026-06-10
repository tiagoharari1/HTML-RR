"""
Escritor de Excel para el P&L final descargable.

Genera un archivo .xlsx en memoria con la hoja `P&L` respetando el orden
de columnas del Excel original, y una hoja `P&L Evolution` con las líneas
del P&L como filas y los meses proyectados como columnas.
"""
from __future__ import annotations

import io

import pandas as pd

from config.settings import PNL_DIMENSIONES, PNL_METRICAS


NOMBRE_HOJA_PNL: str = "P&L"
NOMBRE_HOJA_EVOLUTION: str = "P&L Evolution"

_MESES_ES: dict[int, str] = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}

# Nombres de display para cada línea del P&L (orden idéntico a PNL_METRICAS)
_NOMBRES_DISPLAY: dict[str, str] = {
    "orders": "Orders",
    "gross_bookings": "Gross Bookings",
    "up_front_incentives": "Up Front Incentives",
    "fees": "Customer Fees & Charges",
    "cost_of_installments": "Cost of Installments",
    "credit_card_processing": "Credit Card Processing",
    "affiliates": "Affiliates",
    "cancellations": "Cancellations",
    "income_from_outsourced_services": "Income from Outsourced Services",
    "other_incentives": "O. Incentives",
    "errors": "Errors",
    "revenue_tax": "Rev. Taxes",
    "other_transactional_taxes": "O. Transactional Taxes",
    "back_end_incentives": "Back End Incentives",
    "commercial_discounts": "Commercial Discounts",
    "breakage_revenue": "Breakage Revenue",
    "customer_claims": "Customer Claims",
    "customer_service": "Fulfillment Center Fees",
    "media_revenue": "Media & Other Revenue",
    "vendor_commissions": "Vendor Commissions",
    "intercompany": "Intercomp. Transactions",
    "white_labels_api": "Third Party Commission",
    "operations": "Operations",
    "frauds": "Bad Debt / Frauds",
    "efecto_financiero": "Efecto Financiero",
    "dif_fx": "Dif FX",
    "currency_hedge": "Currency Hedge",
    "net_revenue": "Net Revenue",
    "npv": "NPV",
    "bimo": "BIMO",
    "revenue_margin": "Revenue Margin",
}

# Líneas que actúan como subtotales/separadores visuales
_LINEAS_SUBTOTAL: set[str] = {"net_revenue", "npv", "bimo", "revenue_margin"}


def write_pnl_excel(df_pnl: pd.DataFrame) -> bytes:
    """Devuelve los bytes de un Excel con la hoja P&L."""
    cols = [c for c in (PNL_DIMENSIONES + PNL_METRICAS) if c in df_pnl.columns]
    df = df_pnl[cols].copy()

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name=NOMBRE_HOJA_PNL, index=False)
        ws = writer.sheets[NOMBRE_HOJA_PNL]
        ws.set_column(0, len(PNL_DIMENSIONES) - 1, 18)
        ws.set_column(len(PNL_DIMENSIONES), len(cols) - 1, 14)
    buffer.seek(0)
    return buffer.read()


def write_evolution_excel(df_pnl: pd.DataFrame) -> bytes:
    """Devuelve los bytes de un Excel con la hoja P&L Evolution.

    Filas = líneas del P&L; columnas = meses proyectados en orden (Mes 1 …
    Mes N), con el nombre del mes calendario en español como encabezado.
    Los valores son la suma de todos los combos de dimensiones.
    """
    metricas = [m for m in PNL_METRICAS if m in df_pnl.columns]

    # Ordenar meses por numero_mes_proyectado ("Mes 1", "Mes 2", …)
    orden_meses = (
        df_pnl[["numero_mes_proyectado", "mes_proyectado"]]
        .drop_duplicates()
        .assign(
            _n=lambda d: d["numero_mes_proyectado"]
            .str.extract(r"(\d+)")[0]
            .astype(int)
        )
        .sort_values("_n")
    )

    col_headers = [
        _MESES_ES.get(int(row["mes_proyectado"]), str(row["mes_proyectado"]))
        for _, row in orden_meses.iterrows()
    ]
    meses_ordenados = orden_meses["mes_proyectado"].tolist()

    # Sumar todas las dimensiones → totales por mes proyectado
    totales = (
        df_pnl.groupby("mes_proyectado")[metricas]
        .sum()
        .reindex(meses_ordenados)
    )

    # Construir tabla evolution: una fila por línea P&L
    filas = []
    for linea in metricas:
        nombre = _NOMBRES_DISPLAY.get(linea, linea)
        valores = totales[linea].tolist()
        filas.append([nombre] + valores)

    df_evo = pd.DataFrame(filas, columns=["Línea P&L"] + col_headers)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_evo.to_excel(
            writer, sheet_name=NOMBRE_HOJA_EVOLUTION, index=False, startrow=1
        )
        wb = writer.book
        ws = writer.sheets[NOMBRE_HOJA_EVOLUTION]

        # --- Formatos ---
        fmt_header = wb.add_format({
            "bold": True, "bg_color": "#2E5BFF", "font_color": "#FFFFFF",
            "border": 1, "align": "center", "valign": "vcenter",
        })
        fmt_subtotal = wb.add_format({
            "bold": True, "bg_color": "#E8EDFF", "border": 1,
            "num_format": "#,##0", "align": "right",
        })
        fmt_subtotal_label = wb.add_format({
            "bold": True, "bg_color": "#E8EDFF", "border": 1,
        })
        fmt_number = wb.add_format({
            "num_format": "#,##0", "border": 1, "align": "right",
        })
        fmt_label = wb.add_format({"border": 1})

        n_meses = len(col_headers)

        # Título en fila 0
        ws.merge_range(
            0, 0, 0, n_meses,
            "P&L Evolution — Run Rate HTML B2B",
            wb.add_format({
                "bold": True, "font_size": 13, "align": "center",
                "valign": "vcenter", "bg_color": "#0F172A",
                "font_color": "#FFFFFF",
            }),
        )
        ws.set_row(0, 22)

        # Encabezados de columna (fila 1, ya escrita por to_excel)
        ws.write(1, 0, "Línea P&L", fmt_header)
        for j, h in enumerate(col_headers):
            ws.write(1, j + 1, h, fmt_header)
        ws.set_row(1, 18)

        # Datos (filas desde fila 2)
        subtotales_keys = list(_LINEAS_SUBTOTAL)
        subtotales_nombres = {_NOMBRES_DISPLAY.get(k, k) for k in subtotales_keys}

        for i, linea in enumerate(metricas):
            nombre = _NOMBRES_DISPLAY.get(linea, linea)
            es_subtotal = linea in _LINEAS_SUBTOTAL
            f_label = fmt_subtotal_label if es_subtotal else fmt_label
            f_val = fmt_subtotal if es_subtotal else fmt_number
            ws.write(i + 2, 0, nombre, f_label)
            for j, mes in enumerate(meses_ordenados):
                ws.write(i + 2, j + 1, totales.at[mes, linea], f_val)

        # Anchos de columna
        ws.set_column(0, 0, 30)
        ws.set_column(1, n_meses, 14)

    buffer.seek(0)
    return buffer.read()
