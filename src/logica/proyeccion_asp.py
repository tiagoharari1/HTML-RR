"""
Proyección de ASP (Average Selling Price = gross_bookings / orders)
aplicando los índices de Estacionalidad B2B ASP.

Fórmula:
    asp_proy[m] = asp_pivot × estac_asp[concat_estac, m]
                            / estac_asp[concat_estac, mes_pivot]
"""
from __future__ import annotations

import pandas as pd

from src.io.precargado import load_estacionalidad_asp
from src.logica.proyeccion_orders import (
    concat_estacionalidad,
    indice_estacionalidad,
    mes_proyectado_a_calendario,
)


def proyectar_asp(
    pivot_por_combo: pd.DataFrame,
    mes_pivot: int,
    horizonte: int,
) -> pd.DataFrame:
    """Proyecta ASP para cada combo (país, marca, viaje, producto).

    Args:
        pivot_por_combo: DataFrame con columnas pais, marca, viaje, producto,
            gross_bookings, orders (sumas MTD del mes pivot).

    Returns:
        DataFrame long con pais, marca, viaje, producto,
        numero_mes_proyectado, mes_proyectado, asp.
    """
    estac = load_estacionalidad_asp()

    filas: list[dict] = []
    for _, row in pivot_por_combo.iterrows():
        pais = row["pais"]
        marca = row["marca"]
        viaje = row["viaje"]
        producto = row["producto"]
        gb_pivot = float(row["gross_bookings"]) if pd.notna(row["gross_bookings"]) else 0.0
        orders_pivot = float(row["orders"]) if pd.notna(row["orders"]) else 0.0
        asp_pivot = gb_pivot / orders_pivot if orders_pivot else 0.0

        concat_estac = concat_estacionalidad(pais, viaje, producto)
        indice_pivot = indice_estacionalidad(estac, concat_estac, mes_pivot)
        if indice_pivot == 0:
            indice_pivot = 1.0

        for n in range(1, horizonte + 1):
            mes_proy = mes_proyectado_a_calendario(mes_pivot, n)
            indice_m = indice_estacionalidad(estac, concat_estac, mes_proy)
            asp_proy = asp_pivot * indice_m / indice_pivot
            filas.append(
                {
                    "pais": pais,
                    "marca": marca,
                    "viaje": viaje,
                    "producto": producto,
                    "numero_mes_proyectado": f"Mes {n}",
                    "mes_proyectado": mes_proy,
                    "asp": asp_proy,
                }
            )

    return pd.DataFrame(filas)
