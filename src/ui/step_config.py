"""Step 3 — configuración: fecha pivot, horizonte, día de corte opcional."""
from __future__ import annotations

import datetime

import streamlit as st

from config.settings import HORIZONTE_DEFAULT, HORIZONTE_MAX, HORIZONTE_MIN

_NOMBRE_MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


def _shift_month(d: datetime.date, n: int) -> datetime.date:
    """Devuelve `d` desplazada `n` meses, fijada al día 1."""
    total = (d.month - 1) + n
    return datetime.date(d.year + total // 12, total % 12 + 1, 1)


def _label_mes(d: datetime.date) -> str:
    return f"{_NOMBRE_MESES[d.month - 1]} {d.year}"


def _usar_hoy() -> None:
    """Callback del botón 'Usar fecha actual'."""
    st.session_state["sel_fecha_pivot"] = datetime.date.today()


def render() -> bool:
    """Renderiza el step de configuración."""
    st.header("Paso 3 · Configuración")

    if "sel_fecha_pivot" not in st.session_state:
        st.session_state["sel_fecha_pivot"] = (
            st.session_state.get("fecha_pivot") or datetime.date.today()
        )

    col1, col2 = st.columns(2)
    with col1:
        fecha_pivot = st.date_input(
            "Fecha pivot",
            format="DD/MM/YYYY",
            key="sel_fecha_pivot",
            help=(
                "Elegí el mes calendario del MTD usado como base de proyección. "
                "El día seleccionado se ignora — se trabaja con el mes completo."
            ),
        )
        st.button(
            "Usar fecha actual",
            on_click=_usar_hoy,
            key="btn_hoy",
            help="Setea la fecha pivot al día de hoy.",
        )
        st.session_state["fecha_pivot"] = fecha_pivot
        st.session_state["mes_pivot"] = fecha_pivot.month

    with col2:
        horizonte = st.number_input(
            "Horizonte de proyección (meses)",
            min_value=HORIZONTE_MIN,
            max_value=HORIZONTE_MAX,
            value=int(st.session_state.get("horizonte") or HORIZONTE_DEFAULT),
            step=1,
            key="sel_horizonte",
            help=(
                f"Cantidad de meses a proyectar a partir del mes pivot "
                f"({HORIZONTE_MIN}..{HORIZONTE_MAX})."
            ),
        )
        st.session_state["horizonte"] = int(horizonte)

    inicio = _shift_month(fecha_pivot, 0)
    fin = _shift_month(fecha_pivot, int(horizonte) - 1)
    st.caption(
        f"Se proyectarán **{int(horizonte)} meses**: "
        f"{_label_mes(inicio)} → {_label_mes(fin)}."
    )

    escenario = st.text_input(
        "Escenario (label opcional)",
        value=st.session_state.get("escenario") or "Base",
        key="sel_escenario",
    )
    st.session_state["escenario"] = escenario

    with st.expander("Avanzado — Base 2026 MTD parcial"):
        st.caption(
            "Si el mes pivot está cerrado (todo el mes), dejá este campo en 0. "
            "Si es MTD parcial al día N, ingresá ese N y la app annualiza al mes."
        )
        dia_corte_raw = st.number_input(
            "Día de corte del mes pivot",
            min_value=0,
            max_value=31,
            value=st.session_state.get("dia_corte") or 0,
            step=1,
            key="sel_dia_corte",
        )
        st.session_state["dia_corte"] = int(dia_corte_raw) or None

    base = st.session_state.get("base_2026")
    if base is None:
        st.warning("Falta cargar Base 2026 (Paso 1) antes de avanzar.")
        return False

    mes_pivot = fecha_pivot.month
    n_filas_pivot = int((base["Mes RI"] == mes_pivot).sum())
    if n_filas_pivot == 0:
        st.error(
            f"No hay filas en Base 2026 con `Mes RI = {mes_pivot}` "
            f"({_NOMBRE_MESES[mes_pivot - 1]}). Revisá la fecha pivot."
        )
        return False

    st.success(
        f"OK. Pivot {_label_mes(inicio)}: {n_filas_pivot} filas en Base 2026, "
        f"horizonte {int(horizonte)} meses."
    )
    return True
