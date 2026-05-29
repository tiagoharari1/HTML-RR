"""Step 1 — upload de Base 2026."""
from __future__ import annotations

import streamlit as st

from src.io.readers import read_base_2026
from src.io.validators import validate_base_2026


def render() -> bool:
    """Renderiza el step. Devuelve True si el step está completo."""
    st.header("Paso 1 · Cargar Base 2026")
    st.write(
        "Subí el archivo Excel con los datos transaccionales MTD del canal "
        "HTML/B2B. Esperado: hoja `Base 2026` con columnas `Mes RI`, `pais`, "
        "`marca`, `LOB`, `productooriginal`, `viaje`, `gross_bookings`, "
        "`orders`, y todas las líneas transaccionales."
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
