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
    """Estilos globales (paleta de marca Despegar, stepper, botones)."""
    st.markdown(
        """
        <style>
            /* ──────────────────────────────  Variables de easing  ──────────────── */
            :root {
                --ease-out: cubic-bezier(0.23, 1, 0.32, 1);
                --ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);
            }

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
            [data-testid="stMain"] .block-container {
                max-width: 1200px;
                margin-left: auto;
                margin-right: auto;
                padding-left: 2rem;
                padding-right: 2rem;
            }

            /* ──────────────────────────────  Jerarquía tipográfica  ────────────── */
            .rrai-header__title {
                font-size: 36px;
                font-weight: 700;
                color: #0F172A;
                margin: 0 0 0.65rem 0;
                letter-spacing: -0.025em;
                line-height: 1.1;
            }
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
            [data-testid="stMain"] h3 {
                font-size: 18px;
                font-weight: 600;
                color: #0F172A;
                letter-spacing: -0.01em;
                line-height: 1.3;
                margin-top: 1.5rem;
                margin-bottom: 0.6rem;
            }
            [data-testid="stMain"] p,
            [data-testid="stMain"] li,
            [data-testid="stMain"] [data-testid="stMarkdownContainer"] p {
                font-size: 15px;
                line-height: 1.55;
                color: #0F172A;
            }
            [data-testid="stMain"] [data-testid="stCaptionContainer"],
            [data-testid="stMain"] [data-testid="stCaptionContainer"] * {
                font-size: 12px;
                letter-spacing: 0.04em;
                color: #64748B;
                line-height: 1.5;
            }
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
                transition: border-color 150ms var(--ease-out);
            }
            .rrai-header__meta a:hover { border-bottom-color: #2E5BFF; }

            /* ──────────────────────────────  Sidebar  ─────────────────────────── */
            section[data-testid="stSidebar"] {
                background-color: #FFFFFF;
                border-right: 1px solid rgba(46, 91, 255, 0.10);
            }

            /* ──────────────────────────────  Stepper  ──────────────────────────── */
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
                padding: 0.6rem 0.75rem;
                border-radius: 8px;
                position: relative;
                transition: background-color 200ms var(--ease-out);
            }
            /* Conector vertical entre pasos */
            .rrai-step + .rrai-step::before {
                content: '';
                position: absolute;
                left: 1.55rem;
                top: -0.5rem;
                width: 2px;
                height: 1rem;
                background: linear-gradient(
                    to bottom,
                    rgba(46, 91, 255, 0.22),
                    rgba(46, 91, 255, 0.08)
                );
                border-radius: 1px;
            }
            .rrai-step__marker {
                font-variant-numeric: tabular-nums;
                font-size: 0.75rem;
                letter-spacing: 0.05em;
                min-width: 1.6rem;
                display: inline-flex;
                align-items: center;
                gap: 0.25rem;
                transition: color 200ms var(--ease-out),
                            font-weight 200ms var(--ease-out);
            }
            /* Dot de estado en paso activo */
            .rrai-step__dot {
                display: inline-block;
                width: 6px;
                height: 6px;
                border-radius: 50%;
                background-color: #2E5BFF;
                flex-shrink: 0;
            }
            .rrai-step--active .rrai-step__dot {
                animation: pulse-ring 2s var(--ease-out) infinite;
            }
            @keyframes pulse-ring {
                0%   { box-shadow: 0 0 0 0 rgba(46, 91, 255, 0.40); }
                60%  { box-shadow: 0 0 0 5px rgba(46, 91, 255, 0); }
                100% { box-shadow: 0 0 0 0 rgba(46, 91, 255, 0); }
            }
            .rrai-step__check {
                font-size: 0.7rem;
                line-height: 1;
            }
            .rrai-step__label {
                font-size: 0.875rem;
                transition: color 200ms var(--ease-out),
                            font-weight 200ms var(--ease-out);
            }
            /* Completado */
            .rrai-step--done .rrai-step__marker { color: #2E5BFF; font-weight: 600; }
            .rrai-step--done .rrai-step__label  { color: #475569; font-weight: 400; }
            /* Activo */
            .rrai-step--active {
                background-color: rgba(46, 91, 255, 0.08);
                box-shadow: inset 2px 0 0 0 #2E5BFF;
            }
            .rrai-step--active .rrai-step__marker { color: #2E5BFF; font-weight: 700; }
            .rrai-step--active .rrai-step__label  { color: #0F172A; font-weight: 600; }
            /* Futuro */
            .rrai-step--future .rrai-step__marker { color: #CBD5E1; font-weight: 400; }
            .rrai-step--future .rrai-step__label  { color: #94A3B8; font-weight: 400; }

            .rrai-sidebar__brand { padding: 0.25rem 0 0.75rem 0; }
            .rrai-sidebar__brand-title {
                font-size: 1.05rem;
                font-weight: 700;
                color: #0F172A;
                letter-spacing: -0.02em;
            }
            .rrai-sidebar__brand-sub {
                font-size: 0.68rem;
                color: #2E5BFF;
                letter-spacing: 0.10em;
                text-transform: uppercase;
                margin-top: 0.2rem;
                font-weight: 600;
            }
            .rrai-sidebar__section {
                font-size: 0.65rem;
                color: #CBD5E1;
                letter-spacing: 0.10em;
                text-transform: uppercase;
                margin-bottom: 0.55rem;
                font-weight: 700;
            }

            /* ──────────────────────────────  Botones  ─────────────────────────── */
            [data-testid="stMain"] .stButton > button,
            [data-testid="stMain"] [data-testid="stDownloadButton"] button {
                border-radius: 8px;
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                color: #334155;
                font-weight: 500;
                font-size: 15px;
                box-shadow: none;
                transition: background-color 150ms var(--ease-out),
                            border-color   150ms var(--ease-out),
                            color          150ms var(--ease-out),
                            transform      160ms var(--ease-out),
                            box-shadow     150ms var(--ease-out);
            }
            [data-testid="stMain"] .stButton > button:hover,
            [data-testid="stMain"] [data-testid="stDownloadButton"] button:hover {
                background-color: rgba(46, 91, 255, 0.06);
                border-color: #2E5BFF;
                color: #2E5BFF;
            }
            /* Press feedback — escala táctil */
            [data-testid="stMain"] .stButton > button:active,
            [data-testid="stMain"] [data-testid="stDownloadButton"] button:active {
                transform: scale(0.97);
            }
            [data-testid="stMain"] .stButton > button:focus:not(:active),
            [data-testid="stMain"] [data-testid="stDownloadButton"] button:focus:not(:active) {
                background-color: rgba(46, 91, 255, 0.06);
                border-color: #2E5BFF;
                color: #2E5BFF;
                box-shadow: 0 0 0 3px rgba(46, 91, 255, 0.18);
            }
            [data-testid="stMain"] .stButton > button:disabled,
            [data-testid="stMain"] .stButton > button[disabled],
            [data-testid="stMain"] [data-testid="stDownloadButton"] button:disabled {
                background-color: #F8FAFC;
                border-color: #E2E8F0;
                color: #CBD5E1;
                cursor: not-allowed;
            }
            /* Primary */
            [data-testid="stMain"] button[kind="primary"] {
                background-color: #2E5BFF;
                border-color: #2E5BFF;
                color: #FFFFFF;
                box-shadow: 0 1px 3px rgba(46, 91, 255, 0.30),
                            0 1px 2px rgba(46, 91, 255, 0.20);
            }
            [data-testid="stMain"] button[kind="primary"]:hover {
                background-color: #1E49EF;
                border-color: #1E49EF;
                color: #FFFFFF;
                box-shadow: 0 4px 12px rgba(46, 91, 255, 0.32);
            }
            [data-testid="stMain"] button[kind="primary"]:active {
                transform: scale(0.97);
                background-color: #1A3FD6;
                border-color: #1A3FD6;
                color: #FFFFFF;
            }
            [data-testid="stMain"] button[kind="primary"]:focus:not(:active) {
                background-color: #1E49EF;
                border-color: #1E49EF;
                color: #FFFFFF;
                box-shadow: 0 0 0 3px rgba(46, 91, 255, 0.30);
            }

            /* ──────────────────────────────  Form inputs  ──────────────────────── */
            [data-testid="stMain"] [data-testid="stTextInput"] input,
            [data-testid="stMain"] [data-testid="stNumberInput"] input,
            [data-testid="stMain"] [data-testid="stDateInput"] input {
                border-radius: 8px;
                border-color: #CBD5E1;
                font-size: 14px;
                transition: border-color 150ms var(--ease-out),
                            box-shadow   150ms var(--ease-out);
            }
            [data-testid="stMain"] [data-testid="stTextInput"] input:focus,
            [data-testid="stMain"] [data-testid="stNumberInput"] input:focus,
            [data-testid="stMain"] [data-testid="stDateInput"] input:focus {
                border-color: #2E5BFF !important;
                box-shadow: 0 0 0 3px rgba(46, 91, 255, 0.15) !important;
            }
            /* Selectbox */
            [data-testid="stMain"] [data-testid="stSelectbox"] > div > div {
                border-radius: 8px;
                border-color: #CBD5E1;
                transition: border-color 150ms var(--ease-out),
                            box-shadow   150ms var(--ease-out);
            }
            [data-testid="stMain"] [data-testid="stSelectbox"] > div > div:focus-within {
                border-color: #2E5BFF !important;
                box-shadow: 0 0 0 3px rgba(46, 91, 255, 0.15) !important;
            }
            /* File uploader */
            [data-testid="stMain"] [data-testid="stFileUploader"] > section {
                border-radius: 12px;
                border: 2px dashed #CBD5E1;
                background-color: #FAFBFD;
                transition: border-color 200ms var(--ease-out),
                            background-color 200ms var(--ease-out);
            }
            [data-testid="stMain"] [data-testid="stFileUploader"] > section:hover {
                border-color: #2E5BFF;
                background-color: rgba(46, 91, 255, 0.03);
            }
            /* Expander */
            [data-testid="stMain"] [data-testid="stExpander"] {
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                background-color: #FFFFFF;
            }
            [data-testid="stMain"] [data-testid="stExpander"]:hover {
                border-color: #CBD5E1;
            }

            /* ──────────────────────────────  Divisores  ───────────────────────── */
            [data-testid="stMain"] hr {
                border-color: rgba(46, 91, 255, 0.10);
            }

            /* ──────────────────────────────  Metric cards  ─────────────────────── */
            .rrai-metric {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-top: 3px solid #2E5BFF;
                border-radius: 12px;
                padding: 20px 20px 18px;
                box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
                transition: transform    200ms var(--ease-out),
                            border-color 150ms var(--ease-out),
                            box-shadow   200ms var(--ease-out);
            }
            @media (hover: hover) and (pointer: fine) {
                .rrai-metric:hover {
                    transform: translateY(-2px);
                    border-top-color: #1E49EF;
                    box-shadow: 0 8px 24px rgba(46, 91, 255, 0.12);
                }
            }
            .rrai-metric__label {
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.09em;
                color: #94A3B8;
                margin: 0 0 10px 0;
                line-height: 1;
            }
            .rrai-metric__value {
                font-size: 30px;
                font-weight: 700;
                color: #0F172A;
                letter-spacing: -0.025em;
                line-height: 1.1;
                font-variant-numeric: tabular-nums;
                margin: 0;
            }
            .rrai-metric__unit {
                font-size: 14px;
                font-weight: 500;
                color: #94A3B8;
                margin-left: 2px;
                letter-spacing: 0;
            }

            /* ──────────────────────────────  Section labels  ───────────────────── */
            .rrai-section {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                margin: 1.5rem 0 0.75rem 0;
            }
            .rrai-section__pill {
                font-size: 0.68rem;
                font-weight: 700;
                letter-spacing: 0.10em;
                text-transform: uppercase;
                color: #2E5BFF;
                background: rgba(46, 91, 255, 0.08);
                padding: 3px 10px;
                border-radius: 100px;
                white-space: nowrap;
                flex-shrink: 0;
            }
            .rrai-section__line {
                flex: 1;
                height: 1px;
                background: rgba(46, 91, 255, 0.10);
            }

            /* ──────────────────────────────  Legend pills  ─────────────────────── */
            .rrai-legend {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                flex-wrap: wrap;
                margin: 0.5rem 0 0.25rem 0;
            }
            .rrai-legend__item {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                font-size: 12px;
                font-weight: 500;
                color: #475569;
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 100px;
                padding: 4px 10px 4px 8px;
            }
            .rrai-legend__dot {
                width: 10px;
                height: 10px;
                border-radius: 2px;
                flex-shrink: 0;
            }

            /* ──────────────────────────────  Empty state  ──────────────────────── */
            .rrai-empty {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                text-align: center;
                padding: 3.5rem 2rem;
                border: 2px dashed #E2E8F0;
                border-radius: 16px;
                background: #FAFBFD;
                margin: 1rem 0;
            }
            .rrai-empty__icon {
                font-size: 2.5rem;
                margin-bottom: 1rem;
                opacity: 0.5;
            }
            .rrai-empty__title {
                font-size: 17px;
                font-weight: 600;
                color: #334155;
                margin: 0 0 0.4rem 0;
                letter-spacing: -0.01em;
            }
            .rrai-empty__desc {
                font-size: 14px;
                color: #94A3B8;
                margin: 0;
                max-width: 340px;
                line-height: 1.5;
            }

            /* ──────────────────────────────  Spinner  ──────────────────────────── */
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
