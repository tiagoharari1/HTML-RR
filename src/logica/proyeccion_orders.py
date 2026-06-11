"""
Proyección de orders a partir del MTD del mes pivot y la curva de
Estacionalidad orders B2B.

Fórmula:
    orders_proy[m] = orders_pivot × estac_orders[concat_estac, m]
                                  / estac_orders[concat_estac, mes_pivot]

Donde:
    concat_estac = pais + viaje + producto_agrupado
    m            = mes calendario 1..12

El número de mes proyectado N (1..horizonte) corresponde al mes calendario
((mes_pivot - 1 + N - 1) mod 12) + 1, es decir Mes 1 = mes_pivot.
"""
from __future__ import annotations

import pandas as pd

from config.settings import MAPEO_PRODUCTO_AGRUPADO
from src.io.precargado import load_estacionalidad_orders


def concat_estacionalidad(pais: str, viaje: str, producto: str) -> str:
    """Devuelve la clave de lookup en la hoja Estacionalidad orders B2B."""
    prod_agr = MAPEO_PRODUCTO_AGRUPADO.get(producto, producto)
    return f"{pais}{viaje}{prod_agr}"


def indice_estacionalidad(estac: pd.DataFrame, concat: str, mes: int) -> float:
    """Lookup del índice de estacionalidad para (concat_estac, mes).

    Devuelve 1.0 si no hay match (mismo default que el IFERROR del Excel).
    """
    fila = estac.loc[estac["concatenado"] == concat]
    if fila.empty:
        return 1.0
    valor = fila.iloc[0].get(mes)
    if pd.isna(valor):
        return 1.0
    return float(valor)


def mes_proyectado_a_calendario(mes_pivot: int, n: int) -> int:
    """Mapea el número de mes proyectado (1..horizonte) a mes calendario.

    Mes 1 = mes_pivot, Mes 2 = mes_pivot+1, ... (cíclico módulo 12).
    """
    return ((mes_pivot - 1 + n - 1) % 12) + 1


def shape_proyeccion(
    indice_m: float,
    indice_pivot: float,
    budget_rel_m: float | None = None,
    peso_budget: float = 0.0,
) -> float:
    """Forma relativa de la curva proyectada, normalizada al mes pivot.

    Combina dos señales (ambas valen 1.0 en el mes pivot, garantizando que
    Mes 1 reproduzca el nivel ancla):

      - Estacionalidad del Excel: `indice_m / indice_pivot`
      - Tendencia del budget:     `budget_rel_m` (budget[m] / budget[pivot])

    El blend es `(1 - peso) * estacionalidad + peso * budget`. Con
    `peso_budget = 0` o sin curva de budget, se reduce a la estacionalidad pura
    (comportamiento v1).
    """
    shape_estac = (indice_m / indice_pivot) if indice_pivot else 1.0
    if budget_rel_m is not None and peso_budget > 0:
        return (1.0 - peso_budget) * shape_estac + peso_budget * budget_rel_m
    return shape_estac


def proyectar_orders(
    pivot_por_combo: pd.DataFrame,
    mes_pivot: int,
    horizonte: int,
    *,
    cal_factor: float = 1.0,
    curva_budget: dict[int, float] | None = None,
    peso_budget: float = 0.0,
) -> pd.DataFrame:
    """Proyecta orders para cada combo (país, marca, viaje, producto).

    Args:
        pivot_por_combo: DataFrame con columnas pais, marca, viaje, producto,
            orders (suma MTD del mes pivot).
        mes_pivot: mes calendario (1..12) del pivot.
        horizonte: cantidad de meses a proyectar (1..24).
        cal_factor: factor de calibración de nivel (actuals). Escala el nivel
            del pivot al valor real observado. Default 1.0 = sin calibración.
        curva_budget: dict {mes_calendario: budget[m] / budget[pivot]} con la
            trayectoria del budget. None = no se usa budget.
        peso_budget: peso del budget en el blend de forma (0..1). Default 0.

    Returns:
        DataFrame long con columnas pais, marca, viaje, producto,
        numero_mes_proyectado, mes_proyectado, orders (proyectado).
    """
    estac = load_estacionalidad_orders()
    curva_budget = curva_budget or {}

    filas: list[dict] = []
    for _, row in pivot_por_combo.iterrows():
        pais = row["pais"]
        marca = row["marca"]
        viaje = row["viaje"]
        producto = row["producto"]
        orders_pivot = float(row["orders"]) if pd.notna(row["orders"]) else 0.0
        nivel_base = orders_pivot * cal_factor

        concat_estac = concat_estacionalidad(pais, viaje, producto)
        indice_pivot = indice_estacionalidad(estac, concat_estac, mes_pivot)
        if indice_pivot == 0:
            indice_pivot = 1.0

        for n in range(1, horizonte + 1):
            mes_proy = mes_proyectado_a_calendario(mes_pivot, n)
            indice_m = indice_estacionalidad(estac, concat_estac, mes_proy)
            shape = shape_proyeccion(
                indice_m, indice_pivot, curva_budget.get(mes_proy), peso_budget
            )
            orders_proy = nivel_base * shape
            filas.append(
                {
                    "pais": pais,
                    "marca": marca,
                    "viaje": viaje,
                    "producto": producto,
                    "numero_mes_proyectado": f"Mes {n}",
                    "mes_proyectado": mes_proy,
                    "orders": orders_proy,
                }
            )

    return pd.DataFrame(filas)
