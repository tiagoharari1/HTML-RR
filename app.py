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
    """Estilos minimalistas globales (paleta neutra, stepper, botones).

    Paleta (post-inversión):
      - Background main  #FAFAFA  (near-white — canvas)
      - Background side  #FFFFFF  (blanco puro — sidebar)
      - Text primary     #0A0A0A
      - Text secondary   #6B7280
      - Text muted       #9CA3AF
      - Accent           #6320EE  (violeta — solo botón primario, paso activo, links, spinner)
      - Accent soft      #8075FF  (lavanda — paso completado)
      - Hairline         rgba(10,10,10,0.08)

    El violeta deja de ser canvas y pasa a ser acento puntual. Los widgets
    de Streamlit conservan su estilo default sobre superficie clara, por
    lo que ya no hace falta forzar colores con `!important`.
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
                background-color: #FAFAFA;
                color: #0A0A0A;
            }
            [data-testid="stAppViewContainer"] {
                background-color: #FAFAFA;
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
                color: #0A0A0A;
                margin: 0 0 0.65rem 0;
                letter-spacing: -0.025em;
                line-height: 1.1;
            }
            /* Heading — st.header (h2) */
            [data-testid="stMain"] h1,
            [data-testid="stMain"] h2 {
                font-size: 22px;
                font-weight: 600;
                color: #0A0A0A;
                letter-spacing: -0.015em;
                line-height: 1.25;
                margin-top: 1.5rem;
                margin-bottom: 0.85rem;
            }
            /* Subheading — st.subheader (h3) */
            [data-testid="stMain"] h3 {
                font-size: 18px;
                font-weight: 600;
                color: #0A0A0A;
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
                color: #0A0A0A;
            }
            /* Caption — 12px, tracking-wide */
            [data-testid="stMain"] [data-testid="stCaptionContainer"],
            [data-testid="stMain"] [data-testid="stCaptionContainer"] * {
                font-size: 12px;
                letter-spacing: 0.04em;
                color: #6B7280;
                line-height: 1.5;
            }
            /* Header subtítulo + meta usan body y caption scale */
            .rrai-header__left { max-width: 70%; }
            .rrai-header__desc {
                font-size: 15px;
                color: #6B7280;
                margin: 0 0 0.7rem 0;
                line-height: 1.55;
            }
            .rrai-header__meta {
                font-size: 12px;
                color: #9CA3AF;
                letter-spacing: 0.04em;
            }
            .rrai-header__meta a {
                color: #6320EE;
                text-decoration: none;
                font-weight: 500;
                border-bottom: 1px solid rgba(99, 32, 238, 0.25);
                transition: border-color 150ms ease;
            }
            .rrai-header__meta a:hover {
                border-bottom-color: #6320EE;
            }

            /* ──────────────────────────────  Sidebar  ─────────────────────────── */
            section[data-testid="stSidebar"] {
                background-color: #FFFFFF;
                border-right: 1px solid rgba(10, 10, 10, 0.06);
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
                background-color: rgba(10, 10, 10, 0.10);
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
            /* — Estado completado — */
            .rrai-step--done .rrai-step__marker { color: #8075FF; font-weight: 600; }
            .rrai-step--done .rrai-step__label  { color: #6B7280; font-weight: 400; }
            /* — Estado activo — */
            .rrai-step--active {
                background-color: rgba(99, 32, 238, 0.07);
            }
            .rrai-step--active .rrai-step__marker { color: #6320EE; font-weight: 700; }
            .rrai-step--active .rrai-step__label  { color: #0A0A0A; font-weight: 600; }
            /* — Estado futuro — */
            .rrai-step--future .rrai-step__marker { color: #9CA3AF; font-weight: 400; }
            .rrai-step--future .rrai-step__label  { color: #9CA3AF; font-weight: 400; }

            .rrai-sidebar__brand {
                padding: 0.25rem 0 0.75rem 0;
            }
            .rrai-sidebar__brand-title {
                font-size: 1.05rem;
                font-weight: 600;
                color: #0A0A0A;
                letter-spacing: -0.02em;
            }
            .rrai-sidebar__brand-sub {
                font-size: 0.7rem;
                color: #9CA3AF;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                margin-top: 0.2rem;
                font-weight: 500;
            }
            .rrai-sidebar__section {
                font-size: 0.68rem;
                color: #9CA3AF;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                margin-bottom: 0.55rem;
                font-weight: 600;
            }

            /* ──────────────────────────────  Botones  ─────────────────────────── */
            /* Default — ghost: transparente, hairline border, texto medium-dark */
            [data-testid="stMain"] .stButton > button,
            [data-testid="stMain"] [data-testid="stDownloadButton"] button {
                border-radius: 8px;
                background-color: transparent;
                border: 1px solid #E5E7EB;
                color: #374151;
                font-weight: 500;
                font-size: 15px;
                box-shadow: none;
                transition: background-color 150ms ease,
                            border-color 150ms ease,
                            color 150ms ease;
            }
            [data-testid="stMain"] .stButton > button:hover,
            [data-testid="stMain"] [data-testid="stDownloadButton"] button:hover {
                background-color: #F9FAFB;
                border-color: #D1D5DB;
                color: #0A0A0A;
            }
            /* Disabled — gris, sin sombra, cursor not-allowed */
            [data-testid="stMain"] .stButton > button:disabled,
            [data-testid="stMain"] .stButton > button[disabled],
            [data-testid="stMain"] [data-testid="stDownloadButton"] button:disabled {
                background-color: #F9FAFB;
                border-color: #F3F4F6;
                color: #9CA3AF;
                cursor: not-allowed;
            }
            /* Primary — violeta sólido (acento). Aplica a st.button y st.download_button con type="primary" */
            [data-testid="stMain"] button[kind="primary"] {
                background-color: #6320EE;
                border-color: #6320EE;
                color: #FFFFFF;
                box-shadow: 0 1px 2px rgba(99, 32, 238, 0.18);
            }
            [data-testid="stMain"] button[kind="primary"]:hover {
                background-color: #5018D0;
                border-color: #5018D0;
                color: #FFFFFF;
            }

            /* ──────────────────────────────  Divisores  ───────────────────────── */
            [data-testid="stMain"] hr {
                border-color: rgba(10, 10, 10, 0.08);
            }

            /* ──────────────────────────────  Metric cards (Paso 4)  ───────────── */
            .rrai-metric {
                background-color: #FFFFFF;
                border: 1px solid #F3F4F6;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
                transition: border-color 150ms ease, box-shadow 150ms ease;
            }
            .rrai-metric:hover {
                border-color: #E5E7EB;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
            }
            .rrai-metric__label {
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                color: #6B7280;
                margin: 0 0 12px 0;
                line-height: 1;
            }
            .rrai-metric__value {
                font-size: 32px;
                font-weight: 700;
                color: #0A0A0A;
                letter-spacing: -0.02em;
                line-height: 1.1;
                font-variant-numeric: tabular-nums;
                margin: 0;
            }

            /* ──────────────────────────────  Spinner (acento violeta)  ────────── */
            [data-testid="stSpinner"] > div > div {
                border-top-color: #6320EE !important;
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
        '<div style="border-bottom:1px solid rgba(10,10,10,0.08); '
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
