"""Step 1 — upload de Base 2026."""
from __future__ import annotations

import streamlit as st

from src.io.readers import read_base_2026
from src.io.validators import validate_base_2026


def render() -> bool:
    """Renderiza el step. Devuelve True si el step está completo."""
    st.header("Paso 1 · Cargar Base 2026")
    st.markdown(
        """
        <div style="
            background:#FFFFFF;
            border:1px solid #E2E8F0;
            border-left:3px solid #2E5BFF;
            border-radius:10px;
            padding:14px 16px;
            margin-bottom:1rem;
        ">
            <div style="font-size:13px;font-weight:600;color:#0F172A;margin-bottom:4px;">
                Archivo esperado
            </div>
            <div style="font-size:13px;color:#64748B;line-height:1.55;">
                Excel <strong>(.xlsx)</strong> con hoja
                <code style="background:#F1F5F9;padding:1px 5px;border-radius:4px;font-size:12px;">Base 2026</code>
                — columnas mínimas:
                <code style="background:#F1F5F9;padding:1px 5px;border-radius:4px;font-size:12px;">Mes RI</code>,
                <code style="background:#F1F5F9;padding:1px 5px;border-radius:4px;font-size:12px;">pais</code>,
                <code style="background:#F1F5F9;padding:1px 5px;border-radius:4px;font-size:12px;">LOB</code>,
                <code style="background:#F1F5F9;padding:1px 5px;border-radius:4px;font-size:12px;">gross_bookings</code>,
                <code style="background:#F1F5F9;padding:1px 5px;border-radius:4px;font-size:12px;">orders</code>
                y todas las líneas transaccionales.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Base 2026 (.xlsx)",
        type=["xlsx"],
        key="upload_base_2026",
    )

    if uploaded is None:
        if st.session_state.get("base_2026") is not None:
            st.success(f"Base 2026 ya cargada ({len(st.session_state['base_2026'])} filas)")
            return True
        return False

    try:
        df = read_base_2026(uploaded)
    except Exception as e:
        st.error(f"No pude leer el archivo: {e}")
        return False

    errores = validate_base_2026(df)
    if errores:
        st.error("Hay problemas con la Base 2026:")
        for err in errores:
            st.markdown(f"- {err}")
        return False

    st.session_state["base_2026"] = df
    st.success(f"Base 2026 válida — {len(df)} filas, {df['pais'].nunique()} países")

    with st.expander("Vista previa (primeras 20 filas)"):
        st.dataframe(df.head(20), use_container_width=True)

    return True
