"""Step 4 — ejecutar la proyección y mostrar resultados."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from config.settings import COLS_OPERATING_CONTRIBUTION, PNL_METRICAS
from src.export.excel_writer import write_evolution_excel, write_pnl_excel
from src.io.actuals_budget import load_actuals, load_budget
from src.logica.pnl_builder import build_pnl

# ---------------------------------------------------------------------------
# Constantes de presentación
# ---------------------------------------------------------------------------

# Colores de fondo por grupo de columna (muy claros para no cansar la vista)
_BG_GRUPO: dict[str, str] = {
    "Real":     "#DBEAFE",   # azul cielo claro   — datos históricos cerrados
    "Run Rate": "#FEF3C7",   # ámbar muy claro     — proyección run rate
    "Budget":   "#EDE9FE",   # violeta muy claro   — objetivo presupuestal
}
# Fondo para filas subtotal dentro de cada grupo (un tono más intenso)
_BG_SUBTOTAL: dict[str, str] = {
    "Real":     "#BFDBFE",
    "Run Rate": "#FDE68A",
    "Budget":   "#DDD6FE",
}
# Borde izquierdo en la primera columna de cada grupo (actúa como separador)
_BORDE_INICIO: dict[str, str] = {
    "Real":     "3px solid #3B82F6",   # azul-500
    "Run Rate": "3px solid #F59E0B",   # ámbar-500
    "Budget":   "3px solid #8B5CF6",   # violeta-500
}
# Filas que son subtotales: van en negrita + fondo más intenso + borde superior
_SUBTOTALES_DISPLAY: frozenset[str] = frozenset(
    {"Net Revenue", "NPV", "BIMO", "Revenue Margin", "Cost of Revenue", "Sales & Marketing"}
)
_OC_LABEL: str = "Operating Contribution"
# Fondo para la fila OC — más saturado que los subtotales normales
_BG_OC: dict[str, str] = {
    "Real":     "#93C5FD",   # azul-300
    "Run Rate": "#FCD34D",   # ámbar-300
    "Budget":   "#C4B5FD",   # violeta-300
}


def _estilizar_tabla(df_evo: pd.DataFrame) -> pd.io.formats.style.Styler:
    """Aplica colores, separadores y negritas a la tabla de evolución P&L."""
    # Primera columna de cada grupo → recibe el borde-separador
    primeras_cols: set = set()
    grupos_vistos: set[str] = set()
    for col in df_evo.columns:
        grupo = col[0] if isinstance(col, tuple) else ""
        if grupo not in grupos_vistos:
            primeras_cols.add(col)
            grupos_vistos.add(grupo)

    def _style_col(serie: pd.Series) -> list[str]:
        col = serie.name
        grupo = col[0] if isinstance(col, tuple) else ""
        bg_normal = _BG_GRUPO.get(grupo, "")
        bg_sub = _BG_SUBTOTAL.get(grupo, bg_normal)
        bg_oc = _BG_OC.get(grupo, bg_sub)
        borde = _BORDE_INICIO.get(grupo, "") if col in primeras_cols else ""

        result = []
        for label in serie.index:
            es_oc = label == _OC_LABEL
            es_sub = label in _SUBTOTALES_DISPLAY
            bg = bg_oc if es_oc else (bg_sub if es_sub else bg_normal)
            s = f"background-color: {bg};" if bg else ""
            if borde:
                s += f" border-left: {borde};"
            if es_sub:
                s += " font-weight: bold; border-top: 2px solid rgba(0,0,0,0.15);"
            if es_oc:
                s += " font-weight: bold; border-top: 3px solid rgba(0,0,0,0.3); font-size: 13px;"
            result.append(s)
        return result

    return (
        df_evo.style
        .apply(_style_col, axis=0)
        .format("{:,.0f}", na_rep="—")
        .set_table_styles([
            # Índice (primera columna, labels de filas) en negrita
            {"selector": "th.row_heading",
             "props": "font-weight: bold; font-size: 12px; text-align: left;"},
        ])
    )


_MESES_CORTOS: dict[int, str] = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic",
}

_NOMBRES_LINEAS: dict[str, str] = {
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


def _ejecutar() -> pd.DataFrame:
    base = st.session_state["base_2026"]
    mes_pivot = st.session_state["mes_pivot"]
    horizonte = st.session_state["horizonte"]
    escenario = st.session_state.get("escenario")
    dia_corte = st.session_state.get("dia_corte")

    return build_pnl(
        base,
        mes_pivot=mes_pivot,
        horizonte=horizonte,
        escenario=escenario,
        dia_corte=dia_corte,
    )


def _aplicar_filtros(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    """Renderiza los selectboxes de filtro y retorna (df_filtrado, sel_dict)."""
    cols = st.columns(4)
    sel: dict[str, str] = {}
    for col, dim in zip(cols, ["pais", "marca", "viaje", "producto"]):
        opciones = ["(todos)"] + sorted(df[dim].dropna().unique().tolist())
        with col:
            elegido = st.selectbox(f"Filtrar por {dim}", opciones, key=f"flt_{dim}")
        if elegido != "(todos)":
            sel[dim] = elegido

    out = df
    for k, v in sel.items():
        out = out[out[k] == v]
    return out, sel


# Paleta categórica de marca "Despegar Blue" — arranca en el azul de marca y
# mantiene buena distinción entre series (net_revenue / bimo / revenue_margin).
_COLORWAY_NEUTRAL = ["#2E5BFF", "#00B8A9", "#FF6B4A", "#7C3AED", "#F59E0B"]


def _grafico_rr_vs_budget(pnl_filt: pd.DataFrame) -> None:
    """Gráfico de comparación Run Rate vs Budget para los meses proyectados.

    Muestra Net Revenue y Operating Contribution de ambas fuentes en el mismo
    eje, con líneas sólidas para Run Rate y punteadas para Budget.
    """
    # --- Run Rate: agregar por mes proyectado ---
    oc_cols_rr = [c for c in COLS_OPERATING_CONTRIBUTION if c in pnl_filt.columns]
    rr = (
        pnl_filt.groupby("mes_proyectado")[oc_cols_rr + ["net_revenue"]]
        .sum()
        .reset_index()
    )
    rr["oc"] = rr[oc_cols_rr].sum(axis=1)

    # Ordenar meses según numero_mes_proyectado
    orden = (
        pnl_filt[["mes_proyectado", "numero_mes_proyectado"]]
        .drop_duplicates()
        .assign(_n=lambda d: d["numero_mes_proyectado"].str.extract(r"(\d+)")[0].astype(int))
        .sort_values("_n")["mes_proyectado"]
        .tolist()
    )
    rr = rr.set_index("mes_proyectado").reindex(orden).reset_index()
    rr["mes_label"] = rr["mes_proyectado"].map(lambda m: _MESES_CORTOS.get(int(m), str(m)))

    # --- Budget: mismos meses calendario ---
    try:
        bud_df = load_budget().set_index("mes")
    except Exception:
        bud_df = pd.DataFrame()

    filas_bud = []
    for mes_cal in orden:
        mes_cal_int = int(mes_cal)
        lbl = _MESES_CORTOS.get(mes_cal_int, str(mes_cal_int))
        if not bud_df.empty and mes_cal_int in bud_df.index:
            fila = bud_df.loc[mes_cal_int]
            oc_cols_bud = [c for c in COLS_OPERATING_CONTRIBUTION if c in bud_df.columns]
            nr = float(fila["net_revenue"]) if "net_revenue" in bud_df.columns else 0.0
            oc = float(fila[oc_cols_bud].sum()) if oc_cols_bud else 0.0
        else:
            nr, oc = 0.0, 0.0
        filas_bud.append({"mes_label": lbl, "net_revenue": nr, "oc": oc})
    bud = pd.DataFrame(filas_bud)

    # --- Construir DataFrame largo para plotly ---
    registros = []
    for _, row in rr.iterrows():
        registros.append({"Mes": row["mes_label"], "Valor": row["net_revenue"],
                          "Serie": "RR — Net Revenue"})
        registros.append({"Mes": row["mes_label"], "Valor": row["oc"],
                          "Serie": "RR — Op. Contribution"})
    for _, row in bud.iterrows():
        registros.append({"Mes": row["mes_label"], "Valor": row["net_revenue"],
                          "Serie": "Budget — Net Revenue"})
        registros.append({"Mes": row["mes_label"], "Valor": row["oc"],
                          "Serie": "Budget — Op. Contribution"})

    df_plot = pd.DataFrame(registros)
    # Mantener el orden de los meses en el eje X
    orden_labels = rr["mes_label"].tolist()

    colores = {
        "RR — Net Revenue":          "#2E5BFF",
        "RR — Op. Contribution":     "#00B8A9",
        "Budget — Net Revenue":      "#93C5FD",
        "Budget — Op. Contribution": "#6EE7B7",
    }
    dash_map = {
        "RR — Net Revenue":          "solid",
        "RR — Op. Contribution":     "solid",
        "Budget — Net Revenue":      "dash",
        "Budget — Op. Contribution": "dash",
    }

    fig = px.line(
        df_plot,
        x="Mes",
        y="Valor",
        color="Serie",
        markers=True,
        title="Proyección Run Rate vs Budget",
        color_discrete_map=colores,
        category_orders={"Mes": orden_labels},
    )
    for trace in fig.data:
        trace.line.dash = dash_map.get(trace.name, "solid")

    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>%{y:,.0f}<extra></extra>",
        line=dict(width=2.5),
        marker=dict(size=6),
    )
    fig.update_layout(
        xaxis=dict(
            gridcolor="rgba(46,91,255,0.07)",
            linecolor="rgba(46,91,255,0.12)",
            tickfont=dict(size=12, color="#64748B"),
            title=None,
        ),
        yaxis=dict(
            gridcolor="rgba(46,91,255,0.07)",
            linecolor="rgba(46,91,255,0.12)",
            tickformat=",.0f",
            tickfont=dict(size=12, color="#64748B"),
            title=None,
        ),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(
            family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, sans-serif",
            color="#0F172A",
            size=13,
        ),
        title=dict(
            text="Run Rate vs Budget",
            font=dict(size=15, weight=600, color="#0F172A"),
            x=0,
            xanchor="left",
            pad=dict(l=0, t=0),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.04,
            xanchor="right",
            x=1,
            font=dict(size=12),
            bgcolor="rgba(255,255,255,0)",
            borderwidth=0,
        ),
        margin=dict(l=0, r=0, t=48, b=0),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor="#E2E8F0",
            font=dict(size=12, color="#0F172A"),
        ),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_metric_cards(df: pd.DataFrame) -> None:
    """Cards custom de métricas — display number 32/700, label small-caps 11.

    Reemplaza st.metric default por un layout con jerarquía tipográfica fuerte
    (estilo emil): número grande en tabular-nums, label en uppercase tracking-wide.
    """
    metricas: list[tuple[str, float]] = [
        ("Net Revenue total", float(df["net_revenue"].sum())),
        ("NPV total", float(df["npv"].sum())),
        ("BIMO total", float(df["bimo"].sum())),
        ("Revenue Margin total", float(df["revenue_margin"].sum())),
    ]
    cols = st.columns(4)
    for col, (label, value) in zip(cols, metricas):
        with col:
            st.markdown(
                f"""
                <div class="rrai-metric">
                    <div class="rrai-metric__label">{label}</div>
                    <div class="rrai-metric__value">{value:,.0f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_avisos_calidad(pnl: pd.DataFrame) -> None:
    """Muestra info de calibración y warnings de continuidad de la proyección.

    Lee `pnl.attrs["info_calibracion"]` (mensajes informativos del ancla a
    actuals) y `pnl.attrs["warnings_continuidad"]` (quiebres anómalos detectados
    y/o corregidos por el piso). No renderiza nada si no hay mensajes.
    """
    info = pnl.attrs.get("info_calibracion") or []
    warns = pnl.attrs.get("warnings_continuidad") or []

    if info:
        with st.expander(f":material/tune: Calibración aplicada ({len(info)})", expanded=False):
            for m in info:
                st.caption(f"• {m}")

    if warns:
        with st.expander(
            f":material/warning: Avisos de continuidad ({len(warns)})", expanded=False
        ):
            st.caption(
                "Meses proyectados que caían muy por debajo del nivel observado "
                "del combo. Se elevaron a un piso para mantener la serie continua."
            )
            for w in warns[:200]:
                st.caption(f"• {w}")
            if len(warns) > 200:
                st.caption(f"… y {len(warns) - 200} más.")


def _render_section(title: str) -> None:
    """Pill label + hairline — separador visual de sección."""
    st.markdown(
        f'<div class="rrai-section">'
        f'<span class="rrai-section__pill">{title}</span>'
        f'<div class="rrai-section__line"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _render_action_row(pnl: pd.DataFrame | None) -> None:
    """Action row con jerarquía visual según el estado del flujo.

    Pre-ejecución: Ejecutar = primary (col más ancha), descargas = disabled.
    Post-ejecución: Ejecutar degrada a ghost ("Re-ejecutar"), descargas = primary.
    """
    ya_ejecutado = pnl is not None
    col_run, col_dl, col_evo = st.columns([2, 1.5, 1.5])

    with col_run:
        if ya_ejecutado:
            run_clicked = st.button(
                ":material/refresh: Re-ejecutar",
                use_container_width=True,
                key="btn_run",
            )
        else:
            run_clicked = st.button(
                ":material/play_arrow: Ejecutar proyección",
                type="primary",
                use_container_width=True,
                key="btn_run",
            )
        if run_clicked:
            with st.spinner("Calculando P&L proyectado..."):
                try:
                    st.session_state["pnl_resultado"] = _ejecutar()
                except Exception as e:
                    st.error(f"Error al ejecutar: {e}")
                    raise
            st.rerun()

    with col_dl:
        if ya_ejecutado:
            excel_bytes = write_pnl_excel(pnl)
            st.download_button(
                ":material/download: Descargar P&L completo (Excel)",
                data=excel_bytes,
                file_name=f"pnl_rr_html_mes{st.session_state['mes_pivot']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
                key="btn_dl",
            )
        else:
            st.button(
                ":material/download: Descargar P&L completo (Excel)",
                disabled=True,
                use_container_width=True,
                key="btn_dl_disabled",
            )

    with col_evo:
        if ya_ejecutado:
            evo_bytes = write_evolution_excel(pnl)
            st.download_button(
                ":material/table_chart: Descargar P&L Evolution (Excel)",
                data=evo_bytes,
                file_name=f"pnl_evolution_html_mes{st.session_state['mes_pivot']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
                key="btn_evo",
            )
        else:
            st.button(
                ":material/table_chart: Descargar P&L Evolution (Excel)",
                disabled=True,
                use_container_width=True,
                key="btn_evo_disabled",
            )


def _render_tabla_evolucion(pnl_filt: pd.DataFrame, mes_pivot: int) -> None:
    """Renderiza la tabla de evolución P&L con columnas Real / Run Rate / Budget.

    Parámetros
    ----------
    pnl_filt:
        DataFrame del P&L ya filtrado por los selectboxes del usuario.
    mes_pivot:
        Mes pivot de la proyección (entero 1–12). Los meses de actuals con
        mes < mes_pivot se muestran como "Real".
    """
    # ------------------------------------------------------------------
    # 1. Cargar actuals y budget
    # ------------------------------------------------------------------
    try:
        actuals = load_actuals()
    except Exception as e:
        st.warning(f"No se pudo cargar actuals.csv: {e}")
        actuals = pd.DataFrame(columns=["mes"] + PNL_METRICAS)

    try:
        budget = load_budget()
    except Exception as e:
        st.warning(f"No se pudo cargar budget.csv: {e}")
        budget = pd.DataFrame(columns=["mes"] + PNL_METRICAS)

    # ------------------------------------------------------------------
    # 2. Columnas Real: meses cerrados de actuals (mes < mes_pivot)
    # ------------------------------------------------------------------
    actuals_real = actuals[actuals["mes"] < mes_pivot].sort_values("mes")
    meses_real = actuals_real["mes"].tolist()

    # ------------------------------------------------------------------
    # 3. Columnas Run Rate: meses proyectados, ordenados por numero_mes_proyectado
    # ------------------------------------------------------------------
    if "numero_mes_proyectado" in pnl_filt.columns:
        pnl_filt = pnl_filt.copy()
        # numero_mes_proyectado puede ser "Mes 1", "Mes 2", etc. o int
        def _parse_num_mes(v) -> int:
            try:
                return int(v)
            except (ValueError, TypeError):
                s = str(v).strip()
                if s.lower().startswith("mes"):
                    return int(s.split()[-1])
                return 0

        pnl_filt["_ord"] = pnl_filt["numero_mes_proyectado"].apply(_parse_num_mes)
        orden_cols = (
            pnl_filt[["mes_proyectado", "_ord"]]
            .drop_duplicates()
            .sort_values("_ord")["mes_proyectado"]
            .tolist()
        )
    else:
        orden_cols = sorted(pnl_filt["mes_proyectado"].unique().tolist())

    # Agregar la proyección sumando por mes_proyectado
    rr_agg = (
        pnl_filt.groupby("mes_proyectado")[PNL_METRICAS]
        .sum()
        .reindex(orden_cols)
    )

    # mes_proyectado es un entero 1-12 (mes calendario)
    meses_rr_calendario = [int(m) for m in orden_cols]
    hay_duplicados_rr = len(meses_rr_calendario) != len(set(meses_rr_calendario))

    if hay_duplicados_rr:
        # Usar etiquetas secuenciales "Mes 1", "Mes 2", …
        labels_rr = [f"Mes {i + 1}" for i in range(len(orden_cols))]
    else:
        labels_rr = [
            _MESES_CORTOS.get(m, str(l))
            for m, l in zip(meses_rr_calendario, orden_cols)
        ]

    # ------------------------------------------------------------------
    # 4. Columnas Budget: mismos meses calendario que Run Rate
    # ------------------------------------------------------------------
    budget_indexed = budget.set_index("mes") if not budget.empty and "mes" in budget.columns else pd.DataFrame()

    labels_budget = labels_rr  # mismas etiquetas que RR

    # ------------------------------------------------------------------
    # 5. Construir el DataFrame multi-índice
    # ------------------------------------------------------------------
    lineas_display = [_NOMBRES_LINEAS.get(m, m) for m in PNL_METRICAS]

    # Tuplas (grupo, label_mes) para el MultiIndex de columnas
    tuples: list[tuple[str, str]] = []
    tuples += [("Real", _MESES_CORTOS.get(m, str(m))) for m in meses_real]
    tuples += [("Run Rate", lbl) for lbl in labels_rr]
    tuples += [("Budget", lbl) for lbl in labels_budget]

    multi_idx = pd.MultiIndex.from_tuples(tuples, names=["Grupo", "Mes"])

    # Construir datos: cada columna = una serie por (métrica × mes)
    data: dict[tuple[str, str], list[float]] = {}

    # Real
    for mes in meses_real:
        lbl = _MESES_CORTOS.get(mes, str(mes))
        fila = actuals_real[actuals_real["mes"] == mes]
        vals = []
        for metrica in PNL_METRICAS:
            if not fila.empty and metrica in fila.columns:
                vals.append(float(fila[metrica].iloc[0]))
            else:
                vals.append(0.0)
        data[("Real", lbl)] = vals

    # Run Rate
    for i, (label, mes_label) in enumerate(zip(labels_rr, orden_cols)):
        fila = rr_agg.loc[mes_label] if mes_label in rr_agg.index else None
        vals = []
        for metrica in PNL_METRICAS:
            if fila is not None and metrica in rr_agg.columns:
                vals.append(float(fila[metrica]))
            else:
                vals.append(0.0)
        data[("Run Rate", label)] = vals

    # Budget: coincidir por mes calendario con Run Rate
    for i, (label, mes_cal) in enumerate(zip(labels_budget, meses_rr_calendario)):
        fila_bud = None
        if not budget_indexed.empty and mes_cal is not None and mes_cal in budget_indexed.index:
            fila_bud = budget_indexed.loc[mes_cal]
        vals = []
        for metrica in PNL_METRICAS:
            if fila_bud is not None and metrica in budget_indexed.columns:
                vals.append(float(fila_bud[metrica]) if not isinstance(fila_bud, pd.DataFrame) else float(fila_bud[metrica].iloc[0]))
            else:
                vals.append(0.0)
        data[("Budget", label)] = vals

    # Armar DataFrame con MultiIndex de columnas e índice de líneas
    df_evo = pd.DataFrame(data, index=lineas_display)
    df_evo.columns = multi_idx

    # ------------------------------------------------------------------
    # 6. Agregar filas de subtotal: Cost of Revenue, S&M y OC al final
    # ------------------------------------------------------------------
    def _sumar_filas(nombres_internos: list[str]) -> pd.Series:
        """Suma las filas del df_evo correspondientes a las métricas indicadas."""
        nombres_display = [_NOMBRES_LINEAS.get(m, m) for m in nombres_internos]
        filas_presentes = [n for n in nombres_display if n in df_evo.index]
        if not filas_presentes:
            return pd.Series(0.0, index=df_evo.columns)
        return df_evo.loc[filas_presentes].sum()

    from config.settings import COLS_COST_OF_REVENUE, COLS_SALES_AND_MARKETING

    cor_serie = _sumar_filas(COLS_COST_OF_REVENUE)
    sam_serie = _sumar_filas(COLS_SALES_AND_MARKETING)
    nr_serie = df_evo.loc["Net Revenue"] if "Net Revenue" in df_evo.index else pd.Series(0.0, index=df_evo.columns)
    oc_serie = nr_serie + cor_serie + sam_serie

    df_evo.loc["Cost of Revenue"] = cor_serie
    df_evo.loc["Sales & Marketing"] = sam_serie
    df_evo.loc[_OC_LABEL] = oc_serie

    st.dataframe(_estilizar_tabla(df_evo), use_container_width=True)
    st.markdown(
        """
        <div class="rrai-legend">
            <div class="rrai-legend__item">
                <span class="rrai-legend__dot"
                      style="background:#DBEAFE;border:2px solid #3B82F6;"></span>
                Real — meses cerrados
            </div>
            <div class="rrai-legend__item">
                <span class="rrai-legend__dot"
                      style="background:#FEF3C7;border:2px solid #F59E0B;"></span>
                Run Rate — proyección
            </div>
            <div class="rrai-legend__item">
                <span class="rrai-legend__dot"
                      style="background:#EDE9FE;border:2px solid #8B5CF6;"></span>
                Budget
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render() -> bool:
    st.header("Paso 4 · Resultado")

    if st.session_state.get("base_2026") is None:
        st.warning("Subí Base 2026 (Paso 1) antes de ejecutar.")
        return False

    pnl = st.session_state.get("pnl_resultado")
    _render_action_row(pnl)

    if pnl is None:
        st.markdown(
            """
            <div class="rrai-empty">
                <div class="rrai-empty__icon">📊</div>
                <p class="rrai-empty__title">Todavía no hay proyección</p>
                <p class="rrai-empty__desc">
                    Completá la configuración y presioná
                    <strong>Ejecutar proyección</strong> para ver el P&amp;L.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return False

    _render_avisos_calidad(pnl)

    _render_section("Filtros")
    pnl_filt, _sel = _aplicar_filtros(pnl)

    _render_section("Métricas")
    _render_metric_cards(pnl_filt)

    _render_section("Proyección")
    _grafico_rr_vs_budget(pnl_filt)

    _render_section("P&L Evolution")
    _render_tabla_evolucion(pnl_filt, st.session_state["mes_pivot"])

    if st.session_state.get("contable") is not None:
        with st.expander("Tabla Contable (referencia)"):
            st.dataframe(
                st.session_state["contable"].head(200),
                use_container_width=True,
            )

    return True
