"""
Ensamblado final del P&L dimensional.

Pipeline:
  1. Aggregate Base 2026 al mes pivot → pivot_por_combo
  2. Proyectar orders, asp, gross_bookings
  3. Proyectar líneas de Base 2026 (ratio × GB_proy)
  4. Proyectar líneas de Base 2025 (ratio histórico × GB_proy)
  5. Aplicar ajustes especiales (commercial_discounts=0, efecto_financiero Brasil, etc.)
  6. Calcular métricas derivadas (net_revenue, npv, bimo, revenue_margin)
  7. Construir DataFrame con dimensiones + métricas en el orden de PNL_METRICAS

Devuelve un DataFrame con las dimensiones de PNL_DIMENSIONES y las métricas
de PNL_METRICAS en ese orden exacto.
"""
from __future__ import annotations

import pandas as pd

from config.settings import (
    COLS_BIMO,
    COLS_NET_REVENUE,
    COLS_NPV,
    COLS_REVENUE_MARGIN,
    LINEAS_DESDE_BASE_2025,
    LINEAS_DESDE_BASE_2026,
    LINEAS_EN_CERO,
    PNL_DIMENSIONES,
    PNL_METRICAS,
)
from src.io.precargado import load_base_2025
from src.logica.calibracion import (
    curva_budget_asp_relativa,
    curva_budget_relativa,
    factores_calibracion,
)
from src.logica.lineas_contables import (
    calcular_ratios_base_2025,
    proyectar_lineas_base_2025,
)
from src.logica.lineas_transaccionales import (
    calcular_ratios_base_2026,
    proyectar_lineas_base_2026,
)
from src.logica.mapeo_canal import mapear_canal
from src.logica.proyeccion_asp import proyectar_asp
from src.logica.proyeccion_gb import proyectar_gb
from src.logica.proyeccion_orders import proyectar_orders


_KEY_COLS = ["pais", "marca", "viaje", "producto"]


def aplicar_piso_continuidad(
    gb_proy: pd.DataFrame,
    umbral: float = 0.05,
) -> tuple[pd.DataFrame, list[str]]:
    """Aplica un piso a la serie proyectada para evitar quiebres anómalos.

    Para cada combo, ningún mes proyectado puede tener orders por debajo de
    `umbral x mediana_de_orders_del_combo`. Si lo está, se eleva al piso y se
    recalcula gross_bookings = orders x asp. Cada ajuste se reporta como warning.

    Se usa la mediana (no el promedio) como nivel de referencia: es robusta a
    outliers y estable bajo el propio piso (elevar meses bajos no la corre, así
    que la serie queda continua sin iterar).

    Returns:
        (gb_proy_ajustado, lista_de_warnings_en_español)
    """
    df = gb_proy.copy()
    warns: list[str] = []
    for keys, idx in df.groupby(_KEY_COLS, dropna=False).groups.items():
        sub = df.loc[idx]
        nivel = sub["orders"].median()
        if nivel <= 0:
            continue
        piso = umbral * nivel
        bajos = sub.loc[sub["orders"] < piso]
        for i, r in bajos.iterrows():
            warns.append(
                f"{keys[0]}/{keys[1]}/{keys[2]}/{keys[3]}: orders en "
                f"{r['numero_mes_proyectado']} (mes {int(r['mes_proyectado'])}) "
                f"= {r['orders']:,.0f} estaba por debajo del {umbral:.0%} de la "
                f"mediana ({nivel:,.0f}); se elevó a {piso:,.0f}."
            )
            df.at[i, "orders"] = piso
    df["gross_bookings"] = df["orders"] * df["asp"]
    return df, warns


def validar_continuidad_pnl(pnl: pd.DataFrame, umbral: float = 0.05) -> list[str]:
    """Detecta quiebres anómalos residuales en la serie proyectada.

    Para cada combo (pais, marca, viaje, producto), verifica que ningún mes
    proyectado tenga orders o gross_bookings por debajo de `umbral` de la mediana
    del combo. Usa la mediana (consistente con `aplicar_piso_continuidad`).
    Devuelve una lista de warnings descriptivos en español (vacía si la serie es
    continua).
    """
    warns: list[str] = []
    for keys, sub in pnl.groupby(_KEY_COLS, dropna=False):
        for met in ("orders", "gross_bookings"):
            if met not in sub.columns:
                continue
            nivel = sub[met].median()
            if nivel <= 0:
                continue
            bajos = sub.loc[sub[met] < umbral * nivel]
            for _, r in bajos.iterrows():
                warns.append(
                    f"{keys[0]}/{keys[1]}/{keys[2]}/{keys[3]}: {met} en "
                    f"{r['numero_mes_proyectado']} (mes {int(r['mes_proyectado'])}) "
                    f"= {r[met]:,.0f} es <{umbral:.0%} de la mediana ({nivel:,.0f})."
                )
    return warns


_DIAS_DEL_MES: dict[int, int] = {
    1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
    7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31,
}


def _agregar_pivot(
    base_2026: pd.DataFrame,
    mes_pivot: int,
    dia_corte: int | None = None,
) -> pd.DataFrame:
    """Agrega Base 2026 al nivel de combo para el mes pivot.

    Si `dia_corte` está dado, los valores se annualizan al mes completo
    multiplicando por `dias_del_mes / dia_corte` (equivale al MTD cierre
    del Excel original).
    """
    df = base_2026.loc[base_2026["Mes RI"] == mes_pivot].copy()
    df = df.rename(columns={"productooriginal": "producto"})

    numeric_cols = ["gross_bookings", "orders"]
    agg = (
        df.groupby(_KEY_COLS, dropna=False)[numeric_cols]
        .sum()
        .reset_index()
    )
    if dia_corte:
        factor = _DIAS_DEL_MES.get(mes_pivot, 30) / dia_corte
        agg["orders"] = agg["orders"] * factor
        agg["gross_bookings"] = agg["gross_bookings"] * factor
    return agg


def build_pnl(
    base_2026: pd.DataFrame,
    mes_pivot: int,
    horizonte: int = 12,
    base_2025: pd.DataFrame | None = None,
    escenario: str | None = None,
    dia_corte: int | None = None,
    *,
    usar_actuals: bool = True,
    usar_budget: bool = True,
    peso_budget: float = 0.30,
    usar_mediana_ratios: bool = True,
    aplicar_piso: bool = True,
    umbral_continuidad: float = 0.05,
) -> pd.DataFrame:
    """Construye el P&L proyectado a partir de Base 2026 y Base 2025.

    Mejoras de proyección (todas activas por default, degradan a v1 si falta
    el dato o se desactivan con los flags):

      - `usar_actuals`: ancla el nivel del mes pivot al valor real observado en
        actuals.csv (corrige MTD parciales como mayo 33.9k → ~52.9k real).
      - `usar_budget` / `peso_budget`: inclina la forma de la curva proyectada
        hacia la trayectoria del budget (blend con la estacionalidad del Excel).
      - `usar_mediana_ratios`: los ratios de líneas usan la mediana de varios
        meses en vez de un único mes pivot (más robusto a outliers).
      - `aplicar_piso` / `umbral_continuidad`: piso de continuidad que evita
        quiebres anómalos (orders < umbral del promedio del combo).

    Args:
        dia_corte: si está dado, indica que Base 2026 del mes pivot es MTD
            parcial al día N. Annualiza orders / GB por dias_del_mes / N.
            Default None = se asume mes completo.

    Los warnings de continuidad quedan en `pnl.attrs["warnings_continuidad"]` y
    los mensajes de calibración en `pnl.attrs["info_calibracion"]`.
    """
    if base_2025 is None:
        base_2025 = load_base_2025()

    # 1) Pivot por combo
    pivot = _agregar_pivot(base_2026, mes_pivot, dia_corte=dia_corte)

    # 2) Señales de calibración (actuals) y tendencia (budget)
    if usar_actuals:
        cal_orders, cal_gb, info_calibracion = factores_calibracion(
            float(pivot["orders"].sum()),
            float(pivot["gross_bookings"].sum()),
            mes_pivot,
        )
    else:
        cal_orders, cal_gb, info_calibracion = 1.0, 1.0, []

    if usar_budget:
        curva_b_orders = curva_budget_relativa(mes_pivot, "orders")
        curva_b_asp = curva_budget_asp_relativa(mes_pivot)
    else:
        curva_b_orders, curva_b_asp = {}, {}
    peso = peso_budget if (usar_budget and curva_b_orders) else 0.0

    # cal del ASP: cal_gb / cal_orders → así GB = orders × ASP queda anclado
    # al GB real de actuals.
    cal_asp = (cal_gb / cal_orders) if cal_orders else 1.0

    # 3) Proyección de orders, asp, gb
    orders_proy = proyectar_orders(
        pivot, mes_pivot, horizonte,
        cal_factor=cal_orders, curva_budget=curva_b_orders, peso_budget=peso,
    )
    asp_proy = proyectar_asp(
        pivot, mes_pivot, horizonte,
        cal_factor=cal_asp, curva_budget=curva_b_asp, peso_budget=peso,
    )
    gb_proy = proyectar_gb(orders_proy, asp_proy)

    # 3b) Piso de continuidad (evita quiebres anómalos en la serie)
    warnings_continuidad: list[str] = []
    if aplicar_piso:
        gb_proy, warnings_continuidad = aplicar_piso_continuidad(
            gb_proy, umbral=umbral_continuidad
        )

    # 4) Líneas de Base 2026
    ratios_b2026 = calcular_ratios_base_2026(
        base_2026, mes_pivot, usar_mediana=usar_mediana_ratios
    )
    pnl = proyectar_lineas_base_2026(gb_proy, ratios_b2026)

    # 5) Líneas de Base 2025
    ratios_b2025 = calcular_ratios_base_2025(
        base_2025, mes_pivot, usar_mediana=usar_mediana_ratios
    )
    pnl = proyectar_lineas_base_2025(pnl, ratios_b2025)

    # 5) Ajustes especiales
    for linea in LINEAS_EN_CERO:
        pnl[linea] = 0.0

    # Asegurar que todas las líneas P&L existan como columna numérica.
    todas = (
        set(LINEAS_DESDE_BASE_2026)
        | set(LINEAS_DESDE_BASE_2025)
        | set(LINEAS_EN_CERO)
        | set(PNL_METRICAS)
    )
    for linea in todas:
        if linea not in pnl.columns:
            pnl[linea] = 0.0

    # efecto_financiero en Brasil neto de cost_of_installments
    mask_brasil = pnl["pais"].astype(str).str.casefold().eq("brasil") | pnl[
        "pais"
    ].astype(str).str.casefold().eq("brazil")
    pnl.loc[mask_brasil, "efecto_financiero"] = (
        pnl.loc[mask_brasil, "efecto_financiero"]
        - pnl.loc[mask_brasil, "cost_of_installments"]
    )

    # 6) Métricas derivadas
    pnl["net_revenue"] = pnl[COLS_NET_REVENUE].sum(axis=1)
    pnl["npv"] = pnl[COLS_NPV].sum(axis=1)
    pnl["bimo"] = pnl[COLS_BIMO].sum(axis=1)
    pnl["revenue_margin"] = pnl[COLS_REVENUE_MARGIN].sum(axis=1)

    # 7) Construcción de dimensiones
    pnl["lob_canal"] = "HTML"
    if "marca" in pnl.columns:
        pass  # ya está
    pnl["partner"] = pd.NA
    pnl["escenario"] = escenario if escenario is not None else pd.NA
    pnl["mes_pivot"] = mes_pivot

    # concatenado = pais & lob_canal & marca & viaje & producto
    pnl["concatenado"] = (
        pnl["pais"].astype(str)
        + pnl["lob_canal"].astype(str)
        + pnl["marca"].astype(str)
        + pnl["viaje"].astype(str)
        + pnl["producto"].astype(str)
    )

    pnl = pnl[PNL_DIMENSIONES + PNL_METRICAS].copy()
    pnl = pnl.sort_values(
        ["pais", "marca", "viaje", "producto", "mes_proyectado"]
    ).reset_index(drop=True)

    # Validación residual de continuidad (debería estar vacía si se aplicó piso)
    warnings_continuidad += validar_continuidad_pnl(pnl, umbral=umbral_continuidad)
    pnl.attrs["warnings_continuidad"] = warnings_continuidad
    pnl.attrs["info_calibracion"] = info_calibracion

    return pnl
