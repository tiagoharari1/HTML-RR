"""
RR AI — Entry point de la app Streamlit.

Wizard de 4 pasos para proyectar el P&L del canal HTML/B2B a partir
de Base 2026 (MTD) + factores pre-cargados (Macro, Estacionalidades,
Base 2025 histórica).

Correr con:
    streamlit run app.py
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.io.precargado import precargados_disponibles
from src.ui import (
    step_config,
    step_resultado,
    step_upload_base,
    step_upload_contable,
    wizard,
)


LOGO_PATH = Path(__file__).parent / "assets" / "despegar_logo.png"
FAVICON_PATH = Path(__file__).parent / "assets" / "favicon.svg"

AUTHOR_EMAIL = "tiago.harari@despegar.com"

APP_DESCRIPTION = (
    "Emulador del modelo Run Rate del canal HTML/B2B. "
    "Cargá la Base 2026, configurá el mes pivot y el horizonte, "
    "y obtené el P&L proyectado listo para descargar en Excel."
)


st.set_page_config(
    page_title="RR AI — Run Rate HTML/B2B",
    page_icon=str(FAVICON_PATH) if FAVICON_PATH.exists() else ":material/bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)


STEP_RENDERERS = [
    step_upload_base.render,
    step_upload_contable.render,
    step_config.render,
    step_resultado.render,
]


def _inject_styles() -> None:
    """Estilos globales (paleta de marca Despegar, stepper, botones).

    Paleta "Despegar Blue" — fondos claros + azul de marca como acento:
      - Background main  #F7F9FC  (tinte azulado casi-blanco — canvas)
      - Background side  #FFFFFF  (blanco puro — sidebar / cards)
      - Text primary     #0F172A  (slate-900, negro-navy cálido)
      - Text secondary   #64748B
      - Text muted       #94A3B8
      - Brand / Accent   #2E5BFF  (azul Despegar — botón primario, paso activo, links, spinner)
      - Brand hover      #1E40D6  (azul más profundo)
      - Brand tint       rgba(46,91,255,0.08)  (fondo paso activo, hovers sutiles)
      - Brand soft       #64748B  (gris medio — paso completado)
      - Hairline         rgba(46,91,255,0.10)
    """
    st.markdown(
        """
        <style>
            /* ──────────────────────────────  Tipografía base  ──────────────────── */
            html, body, [class*="css"] {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                             Inter, Roboto, "Helvetica Neue", Arial, sans-serif;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
            }

            /* ──────────────────────────────  Canvas principal  ─────────────────── */
            [data-testid="stMain"] {
                background-color: #F7F9FC;
                color: #0F172A;
            }
            [data-testid="stAppViewContainer"] {
                background-color: #F7F9FC;
            }
            /* Max-width centrado para que el contenido no se desparrame en monitores grandes */
            [data-testid="stMain"] .block-container {
                max-width: 1200px;
                margin-left: auto;
                margin-right: auto;
                padding-left: 2rem;
                padding-right: 2rem;
            }

            /* ──────────────────────────────  Jerarquía tipográfica  ────────────── */
            /* Display — sólo el título principal del header */
            .rrai-header__title {
                font-size: 36px;
                font-weight: 700;
                color: #0F172A;
                margin: 0 0 0.65rem 0;
                letter-spacing: -0.025em;
                line-height: 1.1;
            }
            /* Heading — st.header (h2) */
            [data-testid="stMain"] h1,
            [data-testid="stMain"] h2 {
                font-size: 22px;
                font-weight: 600;
                color: #0F172A;
                letter-spacing: -0.015em;
                line-height: 1.25;
                margin-top: 1.5rem;
                margin-bottom: 0.85rem;
            }
            /* Subheading — st.subheader (h3) */
            [data-testid="stMain"] h3 {
                font-size: 18px;
                font-weight: 600;
                color: #0F172A;
                letter-spacing: -0.01em;
                line-height: 1.3;
                margin-top: 1.5rem;
                margin-bottom: 0.6rem;
            }
            /* Body */
            [data-testid="stMain"] p,
            [data-testid="stMain"] li,
            [data-testid="stMain"] [data-testid="stMarkdownContainer"] p {
                font-size: 15px;
                line-height: 1.55;
                color: #0F172A;
            }
            /* Caption — 12px, tracking-wide */
            [data-testid="stMain"] [data-testid="stCaptionContainer"],
            [data-testid="stMain"] [data-testid="stCaptionContainer"] * {
                font-size: 12px;
                letter-spacing: 0.04em;
                color: #64748B;
                line-height: 1.5;
            }
            /* Header subtítulo + meta usan body y caption scale */
            .rrai-header__left { max-width: 70%; }
            .rrai-header__desc {
                font-size: 15px;
                color: #64748B;
                margin: 0 0 0.7rem 0;
                line-height: 1.55;
            }
            .rrai-header__meta {
                font-size: 12px;
                color: #94A3B8;
                letter-spacing: 0.04em;
            }
            .rrai-header__meta a {
                color: #2E5BFF;
                text-decoration: none;
                font-weight: 500;
                border-bottom: 1px solid rgba(46, 91, 255, 0.30);
                transition: border-color 150ms ease;
            }
            .rrai-header__meta a:hover {
                border-bottom-color: #2E5BFF;
            }

            /* ──────────────────────────────  Sidebar  ─────────────────────────── */
            section[data-testid="stSidebar"] {
                background-color: #FFFFFF;
                border-right: 1px solid rgba(46, 91, 255, 0.10);
            }

            /* ──────────────────────────────  Stepper (sidebar)  ───────────────── */
            .rrai-stepper {
                display: flex;
                flex-direction: column;
                gap: 0;
                margin-top: 0.25rem;
            }
            .rrai-step {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                padding: 0.55rem 0.75rem;
                border-radius: 8px;
                position: relative;
                transition: background-color 200ms ease-out,
                            color 200ms ease-out;
            }
            .rrai-step + .rrai-step::before {
                content: '';
                position: absolute;
                left: 1.5rem;
                top: -0.35rem;
                width: 1px;
                height: 0.7rem;
                background-color: rgba(46, 91, 255, 0.18);
            }
            .rrai-step__marker {
                font-variant-numeric: tabular-nums;
                font-size: 0.75rem;
                letter-spacing: 0.05em;
                min-width: 1.6rem;
                display: inline-flex;
                align-items: baseline;
                gap: 0.25rem;
                transition: color 200ms ease-out,
                            font-weight 200ms ease-out;
            }
            .rrai-step__check {
                font-size: 0.7rem;
                line-height: 1;
            }
            .rrai-step__label {
                font-size: 0.9rem;
                transition: color 200ms ease-out,
                            font-weight 200ms ease-out;
            }
            /* — Estado completado — (azul de marca, semibold) */
            .rrai-step--done .rrai-step__marker { color: #2E5BFF; font-weight: 600; }
            .rrai-step--done .rrai-step__label  { color: #475569; font-weight: 400; }
            /* — Estado activo — (fondo tinte azul + barra de acento a la izquierda) */
            .rrai-step--active {
                background-color: rgba(46, 91, 255, 0.08);
                box-shadow: inset 2px 0 0 0 #2E5BFF;
            }
            .rrai-step--active .rrai-step__marker { color: #2E5BFF; font-weight: 700; }
            .rrai-step--active .rrai-step__label  { color: #0F172A; font-weight: 600; }
            /* — Estado futuro — */
            .rrai-step--future .rrai-step__marker { color: #94A3B8; font-weight: 400; }
            .rrai-step--future .rrai-step__label  { color: #94A3B8; font-weight: 400; }

            .rrai-sidebar__brand {
                padding: 0.25rem 0 0.75rem 0;
            }
            .rrai-sidebar__brand-title {
                font-size: 1.05rem;
                font-weight: 600;
                color: #0F172A;
                letter-spacing: -0.02em;
            }
            .rrai-sidebar__brand-sub {
                font-size: 0.7rem;
                color: #2E5BFF;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                margin-top: 0.2rem;
                font-weight: 600;
            }
            .rrai-sidebar__section {
                font-size: 0.68rem;
                color: #94A3B8;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                margin-bottom: 0.55rem;
                font-weight: 600;
            }

            /* ──────────────────────────────  Botones  ─────────────────────────── */
            /* Default — ghost: transparente, hairline border, texto slate.
               Hover y focus viran a tinte azul de marca (nunca texto oscuro
               sobre fondo oscuro). */
            [data-testid="stMain"] .stButton > button,
            [data-testid="stMain"] [data-testid="stDownloadButton"] button {
                border-radius: 8px;
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                color: #334155;
                font-weight: 500;
                font-size: 15px;
                box-shadow: none;
                transition: background-color 150ms ease,
                            border-color 150ms ease,
                            color 150ms ease;
            }
            [data-testid="stMain"] .stButton > button:hover,
            [data-testid="stMain"] [data-testid="stDownloadButton"] button:hover {
                background-color: rgba(46, 91, 255, 0.06);
                border-color: #2E5BFF;
                color: #2E5BFF;
            }
            /* Focus (teclado / click) del ghost — borde azul, texto azul,
               nunca el primaryColor de Streamlit como fondo */
            [data-testid="stMain"] .stButton > button:focus:not(:active),
            [data-testid="stMain"] [data-testid="stDownloadButton"] button:focus:not(:active) {
                background-color: rgba(46, 91, 255, 0.06);
                border-color: #2E5BFF;
                color: #2E5BFF;
                box-shadow: 0 0 0 3px rgba(46, 91, 255, 0.18);
            }
            /* Disabled — gris, sin sombra, cursor not-allowed */
            [data-testid="stMain"] .stButton > button:disabled,
            [data-testid="stMain"] .stButton > button[disabled],
            [data-testid="stMain"] [data-testid="stDownloadButton"] button:disabled {
                background-color: #F1F5F9;
                border-color: #E2E8F0;
                color: #94A3B8;
                cursor: not-allowed;
            }
            /* Primary — sólido azul de marca. Texto SIEMPRE blanco en todos los
               estados (hover/focus/active) para garantizar contraste AA. */
            [data-testid="stMain"] button[kind="primary"] {
                background-color: #2E5BFF;
                border-color: #2E5BFF;
                color: #FFFFFF;
                box-shadow: 0 1px 2px rgba(46, 91, 255, 0.28);
            }
            [data-testid="stMain"] button[kind="primary"]:hover {
                background-color: #1E40D6;
                border-color: #1E40D6;
                color: #FFFFFF;
            }
            [data-testid="stMain"] button[kind="primary"]:focus,
            [data-testid="stMain"] button[kind="primary"]:active,
            [data-testid="stMain"] button[kind="primary"]:focus:not(:active) {
                background-color: #1E40D6;
                border-color: #1E40D6;
                color: #FFFFFF;
                box-shadow: 0 0 0 3px rgba(46, 91, 255, 0.30);
            }

            /* ──────────────────────────────  Divisores  ───────────────────────── */
            [data-testid="stMain"] hr {
                border-color: rgba(46, 91, 255, 0.12);
            }

            /* ──────────────────────────────  Metric cards (Paso 4)  ───────────── */
            .rrai-metric {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-top: 3px solid #2E5BFF;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
                transition: border-color 150ms ease, box-shadow 150ms ease;
            }
            .rrai-metric:hover {
                border-color: #CBD5E1;
                border-top-color: #1E40D6;
                box-shadow: 0 4px 12px rgba(46, 91, 255, 0.12);
            }
            .rrai-metric__label {
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                color: #64748B;
                margin: 0 0 12px 0;
                line-height: 1;
            }
            .rrai-metric__value {
                font-size: 32px;
                font-weight: 700;
                color: #0F172A;
                letter-spacing: -0.02em;
                line-height: 1.1;
                font-variant-numeric: tabular-nums;
                margin: 0;
            }

            /* ──────────────────────────────  Spinner (acento de marca)  ───────── */
            [data-testid="stSpinner"] > div > div {
                border-top-color: #2E5BFF !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_header() -> None:
    """Header con título, descripción breve, mail y logo."""
    col_text, col_logo = st.columns([0.72, 0.28], vertical_alignment="center")

    with col_text:
        st.markdown(
            f"""
            <div class="rrai-header__left">
                <p class="rrai-header__title">RR AI · Run Rate HTML/B2B</p>
                <p class="rrai-header__desc">{APP_DESCRIPTION}</p>
                <p class="rrai-header__meta">
                    Contacto ·
                    <a href="mailto:{AUTHOR_EMAIL}">{AUTHOR_EMAIL}</a>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_logo:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), use_container_width=True)

    st.markdown(
        '<div style="border-bottom:1px solid rgba(46,91,255,0.12); '
        'margin: 0 0 1.25rem 0;"></div>',
        unsafe_allow_html=True,
    )


def _check_precargados() -> None:
    """Avisa si faltan archivos pre-cargados en data/precargado/."""
    estado = precargados_disponibles()
    faltantes = [k for k, ok in estado.items() if not ok]
    if faltantes:
        st.sidebar.error(
            "Faltan archivos pre-cargados en `data/precargado/`: "
            + ", ".join(faltantes)
        )


def main() -> None:
    _inject_styles()
    wizard.init_state()
    wizard.render_sidebar()
    _check_precargados()

    _render_header()

    paso_actual = st.session_state.step
    puede_avanzar = STEP_RENDERERS[paso_actual]()

    wizard.navigation_buttons(puede_avanzar=puede_avanzar)


if __name__ == "__main__":
    main()
