# data/precargado/

Hojas estructurales que vienen con la app y NO las sube el usuario:

- `macro.xlsx` — FX y CPI por país y mes (2024-2027)
- `estacionalidad_orders.xlsx` — índices mensuales por concatenado
- `estacionalidad_asp.xlsx` — índices mensuales por concatenado

Se cargan automáticamente al iniciar la app (ver `src/io/precargado.py`).

> En M4 se completan los archivos extrayendo las hojas correspondientes
> del Excel original de Run Rate.
