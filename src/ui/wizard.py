"""
Stepper del wizard de 4 pasos.

Provee:
  - STEPS: labels de los pasos
  - init_state: inicializa st.session_state con defaults
  - render_sidebar: navegación visual
  - navigation_buttons: controles Anterior / Siguiente
"""
from __future__ import annotations

import streamlit as st


STEPS: list[str] = [
    "Cargar Base 2026",
    "Cargar Contable",
    "Configuración",
    "Resultado",
]


def init_state() -> None:
    """Inicializa las claves esperadas en st.session_state."""
    defaults: dict[str, object] = {
        "step": 0,
        "base_2026": None,
        "contable": None,
        "mes_pivot": 5,
        "horizonte": 12,
        "dia_corte": None,
        "escenario": "Base",
        "pnl_resultado": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_sidebar() -> None:
    """Sidebar con stepper numerado (01..04), línea conectora y check sutil."""
    st.sidebar.markdown(
        """
        <div class="rrai-sidebar__brand">
            <div class="rrai-sidebar__brand-title">RR AI</div>
            <div class="rrai-sidebar__brand-sub">Run Rate · HTML/B2B</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.divider()
    st.sidebar.markdown(
        '<div class="rrai-sidebar__section">Progreso</div>',
        unsafe_allow_html=True,
    )

    current = st.session_state.step
    parts: list[str] = ['<div class="rrai-stepper">']
    for i, label in enumerate(STEPS):
        num = f"{i + 1:02d}"
        if i < current:
            state = "done"
            marker = (
                f'<span class="rrai-step__num">{num}</span>'
                f'<span class="rrai-step__check">✓</span>'
            )
        elif i == current:
            state = "active"
            marker = (
                f'<span class="rrai-step__num">{num}</span>'
                f'<span class="rrai-step__dot"></span>'
            )
        else:
            state = "future"
            marker = f'<span class="rrai-step__num">{num}</span>'
        parts.append(
            f'<div class="rrai-step rrai-step--{state}">'
            f'<div class="rrai-step__marker">{marker}</div>'
            f'<div class="rrai-step__label">{label}</div>'
            f'</div>'
        )
    parts.append('</div>')
    st.sidebar.markdown("".join(parts), unsafe_allow_html=True)


def navigation_buttons(*, puede_avanzar: bool = True) -> None:
    """Botones Anterior / Siguiente del wizard.

    `Siguiente` es la acción primaria del wizard y se renderiza con
    énfasis (type="primary"); `Anterior` queda como botón secundario.
    Los íconos usan Material Symbols vía la sintaxis nativa de Streamlit
    (`:material/...:`), que renderiza glifos vectoriales con `currentColor`.
    """
    st.divider()
    col_prev, col_next = st.columns([1, 1])
    with col_prev:
        if st.session_state.step > 0:
            if st.button(
                ":material/arrow_back: Anterior",
                use_container_width=True,
                key="btn_prev",
            ):
                st.session_state.step -= 1
                st.rerun()
    with col_next:
        if st.session_state.step < len(STEPS) - 1:
            if st.button(
                "Siguiente :material/arrow_forward:",
                use_container_width=True,
                key="btn_next",
                type="primary",
                disabled=not puede_avanzar,
            ):
                st.session_state.step += 1
                st.rerun()
