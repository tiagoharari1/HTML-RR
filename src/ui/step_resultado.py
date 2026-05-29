"""Step 4 — ejecutar la proyección y mostrar resultados."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.export.excel_writer import write_pnl_excel
from src.logica.pnl_builder import build_pnl


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


def _aplicar_filtros(df: pd.DataFrame) -> pd.DataFrame:
    cols = st.columns(4)
    sel = {}
    for col, dim in zip(cols, ["pais", "marca", "viaje", "producto"]):
        opciones = ["(todos)"] + sorted(df[dim].dropna().unique().tolist())
        with col:
            elegido = st.selectbox(f"Filtrar por {dim}", opciones, key=f"flt_{dim}")
        if elegido != "(todos)":
            sel[dim] = elegido

    out = df
    for k, v in sel.items():
        out = out[out[k] == v]
    return out


def _grafico_metricas(df: pd.DataFrame) -> None:
    tot = (
        df.groupby("mes_proyectado")[["net_revenue", "bimo", "revenue_margin"]]
        .sum()
        .reset_index()
        .melt(id_vars="mes_proyectado", var_name="metrica", value_name="valor")
    )
    fig = px.line(
        tot,
        x="mes_proyectado",
        y="valor",
        color="metrica",
        markers=True,
        title="Evolución mensual",
    )
    fig.update_layout(xaxis=dict(tickmode="linear", dtick=1))
    st.plotly_chart(fig, use_container_width=True)


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


def _render_action_row(pnl: pd.DataFrame | None) -> None:
    """Action row con jerarquía visual según el estado del flujo.

    Pre-ejecución: Ejecutar = primary, Descargar = disabled ghost.
    Post-ejecución: Ejecutar degrada a ghost ("Re-ejecutar"), Descargar = primary.
    """
    ya_ejecutado = pnl is not None
    col_run, col_dl = st.columns([1, 1])

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


def render() -> bool:
    st.header("Paso 4 · Resultado")

    if st.session_state.get("base_2026") is None:
        st.warning("Subí Base 2026 (Paso 1) antes de ejecutar.")
        return False

    pnl = st.session_state.get("pnl_resultado")
    _render_action_row(pnl)

    if pnl is None:
        st.caption(
            "Aún no se ejecutó la proyección — completá la configuración y "
            "presioná Ejecutar."
        )
        return False

    st.subheader("Filtros")
    pnl_filt = _aplicar_filtros(pnl)

    _render_metric_cards(pnl_filt)

    st.subheader("Gráficos")
    _grafico_metricas(pnl_filt)

    st.subheader("Tabla P&L")
    st.dataframe(pnl_filt, use_container_width=True, hide_index=True)

    if st.session_state.get("contable") is not None:
        with st.expander("Tabla Contable (referencia)"):
            st.dataframe(
                st.session_state["contable"].head(200),
                use_container_width=True,
            )

    return True
