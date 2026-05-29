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


def proyectar_orders(
    pivot_por_combo: pd.DataFrame,
    mes_pivot: int,
    horizonte: int,
) -> pd.DataFrame:
    """Proyecta orders para cada combo (país, marca, viaje, producto).

    Args:
        pivot_por_combo: DataFrame con columnas pais, marca, viaje, producto,
            orders (suma MTD del mes pivot).
        mes_pivot: mes calendario (1..12) del pivot.
        horizonte: cantidad de meses a proyectar (1..24).

    Returns:
        DataFrame long con columnas pais, marca, viaje, producto,
        numero_mes_proyectado, mes_proyectado, orders (proyectado).
    """
    estac = load_estacionalidad_orders()

    filas: list[dict] = []
    for _, row in pivot_por_combo.iterrows():
        pais = row["pais"]
        marca = row["marca"]
        viaje = row["viaje"]
        producto = row["producto"]
        orders_pivot = float(row["orders"]) if pd.notna(row["orders"]) else 0.0

        concat_estac = concat_estacionalidad(pais, viaje, producto)
        indice_pivot = indice_estacionalidad(estac, concat_estac, mes_pivot)
        if indice_pivot == 0:
            indice_pivot = 1.0

        for n in range(1, horizonte + 1):
            mes_proy = mes_proyectado_a_calendario(mes_pivot, n)
            indice_m = indice_estacionalidad(estac, concat_estac, mes_proy)
            orders_proy = orders_pivot * indice_m / indice_pivot
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
