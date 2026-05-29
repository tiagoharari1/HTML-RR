"""Step 2 — upload de Contable (opcional, sólo referencia)."""
from __future__ import annotations

import streamlit as st

from src.io.readers import read_contable
from src.io.validators import validate_contable


def render() -> bool:
    """Renderiza el step. Devuelve siempre True — Contable es opcional."""
    st.header("Paso 2 · Cargar Contable (opcional)")
    st.info(
        "Contable se carga sólo como **tabla de referencia comparativa**. "
        "En v1 no entra al cálculo del P&L (el Excel original tampoco la usa "
        "para esto). Podés saltear este paso."
    )

    uploaded = st.file_uploader(
        "Contable (.xlsx)",
        type=["xlsx"],
        key="upload_contable",
    )

    if uploaded is None:
        if st.session_state.get("contable") is not None:
            st.success(
                f"Contable ya cargada ({len(st.session_state['contable'])} filas)"
            )
        else:
            st.caption("Sin archivo cargado. Podés avanzar al paso siguiente.")
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
