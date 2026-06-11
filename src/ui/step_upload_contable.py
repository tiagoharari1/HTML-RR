"""Step 2 — upload de Contable (opcional, sólo referencia)."""
from __future__ import annotations

import streamlit as st

from src.io.readers import read_contable
from src.io.validators import validate_contable


def render() -> bool:
    """Renderiza el step. Devuelve siempre True — Contable es opcional."""
    st.header("Paso 2 · Cargar Contable (opcional)")
    st.markdown(
        """
        <div style="
            background:#F0FDF4;
            border:1px solid #BBF7D0;
            border-left:3px solid #22C55E;
            border-radius:10px;
            padding:14px 16px;
            margin-bottom:1rem;
        ">
            <div style="font-size:13px;font-weight:600;color:#15803D;margin-bottom:4px;">
                Paso opcional
            </div>
            <div style="font-size:13px;color:#166534;line-height:1.55;">
                Contable se usa sólo como <strong>tabla de referencia comparativa</strong>.
                No entra al cálculo del P&L en v1. Podés saltear este paso
                y avanzar directamente a Configuración.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Contable (.xlsx)",
        type=["xlsx"],
        key="upload_contable",
    )

    if uploaded is None:
        if st.session_state.get("contable") is not None:
            st.success(f"Contable ya cargada ({len(st.session_state['contable'])} filas)")
        else:
            st.markdown(
                """
                <div style="
                    color:#94A3B8;font-size:13px;
                    padding:10px 0 4px 2px;
                ">
                    Sin archivo cargado — podés avanzar al siguiente paso.
                </div>
                """,
                unsafe_allow_html=True,
            )
        return True

    try:
        df = read_contable(uploaded)
    except Exception as e:
        st.error(f"No pude leer el archivo: {e}")
        return True

    errores = validate_contable(df)
    if errores:
        st.warning("Contable cargada con observaciones:")
        for err in errores:
            st.markdown(f"- {err}")
    else:
        st.success(f"Contable cargada — {len(df)} filas")

    st.session_state["contable"] = df

    with st.expander("Vista previa (primeras 20 filas)"):
        st.dataframe(df.head(20), use_container_width=True)

    return True
