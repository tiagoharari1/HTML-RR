"""
Señales de calibración y tendencia para anclar la proyección a datos reales.

El modelo v1 proyectaba todo a partir del mes pivot crudo de Base 2026, que
puede ser un MTD parcial (e.g. mayo con 33.9k orders cuando el nivel real del
mes fue ~52.9k). Este módulo aporta dos señales que corrigen eso:

  - **Actuals** (`output/actuals.csv`): nivel real observado del canal B2B/MIN
    por mes. Se usa para calibrar el nivel del mes pivot al valor real
    (factor `cal = actuals[mes_pivot] / agregado_pivot_Base2026`).
  - **Budget** (`output/budget.csv`): trayectoria planificada del año completo.
    Se usa como señal de **tendencia** para inclinar la forma de la curva
    proyectada (blend con la estacionalidad del Excel).

Todas las funciones degradan con gracia: si los CSV no existen o están vacíos,
devuelven factores neutros (cal=1.0, curva vacía) y el modelo se comporta
exactamente como la v1.
"""
from __future__ import annotations

import logging

import pandas as pd

_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Carga segura (los CSV pueden no existir en entornos de test)
# ---------------------------------------------------------------------------
def _actuals_seguro() -> pd.DataFrame | None:
    """Carga actuals; devuelve None si no se puede (sin romper la lógica)."""
    try:
        from src.io.actuals_budget import load_actuals

        df = load_actuals()
        return df if df is not None and not df.empty else None
    except Exception as e:  # pragma: no cover - depende de archivos externos
        _log.warning("No se pudo cargar actuals para calibración: %s", e)
        return None


def _budget_seguro() -> pd.DataFrame | None:
    """Carga budget; devuelve None si no se puede (sin romper la lógica)."""
    try:
        from src.io.actuals_budget import load_budget

        df = load_budget()
        return df if df is not None and not df.empty else None
    except Exception as e:  # pragma: no cover - depende de archivos externos
        _log.warning("No se pudo cargar budget para tendencia: %s", e)
        return None


def _valor_mes(df: pd.DataFrame, mes: int, col: str) -> float | None:
    """Valor de `col` para `mes` en un DataFrame con columna 'mes'. None si 0/ausente."""
    if df is None or col not in df.columns:
        return None
    fila = df.loc[df["mes"] == mes]
    if fila.empty:
        return None
    valor = float(fila.iloc[0][col])
    return valor if valor != 0 else None


# ---------------------------------------------------------------------------
# Factores de calibración de nivel (actuals)
# ---------------------------------------------------------------------------
def factores_calibracion(
    orders_pivot_total: float,
    gb_pivot_total: float,
    mes_pivot: int,
) -> tuple[float, float, list[str]]:
    """Calcula factores que escalan el agregado del pivot al nivel real de actuals.

    Para cada métrica (orders, gross_bookings):
        cal = actuals[mes_pivot] / agregado_pivot_Base_2026

    Así, al multiplicar el nivel del pivot por `cal`, el Mes 1 de la proyección
    reproduce el nivel **real observado** del mes (corrige MTD parciales).

    Si el mes pivot no tiene actuals, usa el último mes disponible como proxy.
    Si no hay actuals en absoluto, devuelve (1.0, 1.0) — comportamiento v1.

    Returns:
        (cal_orders, cal_gross_bookings, mensajes_informativos)
    """
    msgs: list[str] = []
    act = _actuals_seguro()
    if act is None:
        return 1.0, 1.0, msgs

    def _cal(total_base: float, col: str, etiqueta: str) -> float:
        if total_base is None or total_base <= 0:
            return 1.0
        real = _valor_mes(act, mes_pivot, col)
        origen = mes_pivot
        if real is None:
            disponibles = act.loc[act[col] > 0, "mes"]
            if disponibles.empty:
                return 1.0
            origen = int(disponibles.max())
            real = _valor_mes(act, origen, col)
            if real is None:
                return 1.0
            msgs.append(
                f"Calibración de {etiqueta}: el mes pivot {mes_pivot} no tiene "
                f"actuals; se usó el mes {origen} como proxy de nivel."
            )
        factor = real / total_base
        if abs(factor - 1.0) > 0.10:
            msgs.append(
                f"Calibración de {etiqueta}: nivel del pivot ajustado "
                f"×{factor:.2f} para anclar al actual real "
                f"({real:,.0f} vs {total_base:,.0f} de Base 2026)."
            )
        return factor

    cal_o = _cal(orders_pivot_total, "orders", "orders")
    cal_g = _cal(gb_pivot_total, "gross_bookings", "gross_bookings")
    return cal_o, cal_g, msgs


# ---------------------------------------------------------------------------
# Curvas de tendencia del budget (relativas al mes pivot)
# ---------------------------------------------------------------------------
def curva_budget_relativa(mes_pivot: int, col: str = "orders") -> dict[int, float]:
    """Trayectoria del budget normalizada al mes pivot.

    Returns:
        dict {mes_calendario: budget[mes, col] / budget[mes_pivot, col]}.
        Vacío si no hay budget o el mes pivot no tiene dato (>0).
    """
    bud = _budget_seguro()
    if bud is None:
        return {}
    base = _valor_mes(bud, mes_pivot, col)
    if not base:
        return {}
    out: dict[int, float] = {}
    for _, r in bud.iterrows():
        valor = float(r[col]) if col in bud.columns else 0.0
        out[int(r["mes"])] = valor / base
    return out


def curva_budget_asp_relativa(mes_pivot: int) -> dict[int, float]:
    """Trayectoria del ASP implícito del budget (gb/orders), normalizada al pivot.

    Returns:
        dict {mes_calendario: asp_budget[mes] / asp_budget[mes_pivot]}.
        Vacío si no hay budget o falta el dato del pivot.
    """
    bud = _budget_seguro()
    if bud is None:
        return {}

    def _asp(mes: int) -> float | None:
        o = _valor_mes(bud, mes, "orders")
        g = _valor_mes(bud, mes, "gross_bookings")
        return (g / o) if (o and g) else None

    base = _asp(mes_pivot)
    if not base:
        return {}
    out: dict[int, float] = {}
    for mes in bud["mes"].astype(int):
        a = _asp(int(mes))
        if a:
            out[int(mes)] = a / base
    return out
