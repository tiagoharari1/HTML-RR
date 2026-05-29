# Notas de lógica financiera

Este documento centraliza los supuestos y reglas de cálculo que la app
implementa. Se va completando módulo a módulo.

## Decisiones tomadas en la sesión de diseño

- **Stack**: Streamlit + pandas + openpyxl + plotly
- **Inputs del usuario** (cada ejecución): Base 2026 (obligatorio) y Contable
  (opcional, sólo referencia)
- **Hojas pre-cargadas** (vienen con la app):
  - Macro (no se usa en v1 — passthrough)
  - Estacionalidad orders B2B
  - Estacionalidad B2B ASP
  - **Base 2025** (histórica — drivea ~16 líneas del P&L)
- **Mes pivot**: lo ingresa el usuario manualmente en el step de configuración
- **Día de corte** (opcional): si Base 2026 del mes pivot es MTD parcial al
  día N, se annualiza por `dias_del_mes / N`. Default = mes completo.
- **Horizonte de proyección**: configurable por el usuario (default 12 meses)
- **Escenarios**: uno solo por ejecución en la v1 (label libre)
- **Output**: Excel descargable (.xlsx con hoja `P&L`)
- **Mapeo canal**: B2B (Base 2026) → HTML (P&L output)

## Pipeline de cálculo (resumen)

1. Agregar Base 2026 al nivel de combo `(pais, marca, viaje, producto)` para
   el mes pivot. Si hay `dia_corte`, annualizar.
2. Proyectar `orders` con estacionalidad: para cada combo,
   `orders_proy[m] = orders_pivot × estac_orders[concat_estac, m]
                                  / estac_orders[concat_estac, mes_pivot]`,
   donde `concat_estac = pais + viaje + producto_agrupado`.
3. Proyectar `asp` con estacionalidad ASP (misma fórmula). Pivot ASP =
   `gross_bookings_pivot / orders_pivot`.
4. `gross_bookings_proy = orders_proy × asp_proy`.
5. Para las líneas de `LINEAS_DESDE_BASE_2026` (up_front_incentives, fees,
   cost_of_installments, credit_card_processing, affiliates, cancellations,
   other_incentives): `linea_proy[combo,m] = ratio_2026[combo, linea] × GB_proy[combo, m]`
   donde `ratio_2026 = Base2026[linea] / Base2026[gross_bookings]` agregado
   al nivel combo y filtrado a `Mes RI = mes_pivot`.
6. Para las líneas de `LINEAS_DESDE_BASE_2025` (income_from_outsourced_services,
   errors, revenue_tax, other_transactional_taxes, back_end_incentives,
   breakage_revenue, customer_claims, customer_service, media_revenue,
   vendor_commissions, intercompany, white_labels_api, operations, frauds,
   efecto_financiero, dif_fx, currency_hedge): mismo mecanismo pero usando
   `Base 2025` (precargada) en lugar de `Base 2026`.
7. Ajustes especiales:
   - `commercial_discounts = 0` (hardcodeado).
   - Para `pais ∈ {Brasil, Brazil}`: `efecto_financiero -= cost_of_installments`.
8. Calcular métricas derivadas:
   - `net_revenue` = upf + fees + cancellations + income_from_outsourced
                   + other_incentives + revenue_tax + back_end_incentives
                   + commercial_discounts + breakage_revenue + media_revenue
   - `npv` = suma de todas las líneas P&L (upf..currency_hedge)
   - `bimo = dif_fx + currency_hedge` (literal del Excel, no es lo que el
     nombre sugiere)
   - `revenue_margin = upf + fees + cancellations`
9. Mapeo canal `B2B → HTML` y construcción de `concatenado = pais & lob_canal &
   marca & viaje & producto`.

## Limitaciones conocidas de v1 (vs el Excel original)

Las siguientes simplificaciones se aceptaron con el usuario en la sesión de
v1 para acotar el alcance. Se mantienen como TODO para v2.

| Simplificación v1 | Excel original | Impacto |
|---|---|---|
| Modelo Orders simple (`pivot × estac[m] / estac[pivot]`) | Modelo Orders aplica gradiente, ajustes manuales y elasticidades | Orders/GB difieren ~1-5% por combo |
| ASP simple (misma fórmula) | Modelo ASP también con ajustes | ASP difiere ~1-5% |
| GB = orders[m] × ASP[m] | Calculo GB usa `orders[m] × ASP[m-1]` (shift 1 mes) | Diferencia menor |
| Macro/FX/CPI no aplicada | El Excel actual tampoco la aplica al P&L | Sin impacto en v1 |
| `up_front_incentives` usa ratio MTD del mes pivot | El Excel hardcodea ratio del **mes April** (upf-fees!B$1=4) | Diferencia ~5-10% en upf |
| Contable no drivea el P&L | Sólo aparece como "Ultimo Cierre contable" de referencia en Modelo Palancas | Sin impacto |
| `producto_agrupado` mapeado en settings.py | El Excel usa Diccionario hoja AT:AU | Equivalente si el mapping coincide |
| `media_revenue` y `back_end_incentives` desde Base 2025 → quedan en 0 si el header no matchea | Mismo comportamiento (IFERROR) | Coincide |

## Validación contra el Excel original

El test `tests/test_logica.py::test_comparacion_contra_excel_original`
compara totales mensuales (orders, gross_bookings, net_revenue,
revenue_margin) contra los valores cacheados de la hoja `P&L` del Excel
original. Tolerancia: **15%** sobre cada métrica × cada mes proyectado.

Resultados observados con `mes_pivot=5, dia_corte=20`:

- orders ratio mine/ref: 0.95 – 1.03
- gross_bookings ratio: 0.95 – 1.05
- net_revenue ratio: 1.02 – 1.12
- revenue_margin ratio: 1.02 – 1.12

La sobreestimación sistemática del net_revenue se origina principalmente
en `up_front_incentives` (el Excel usa ratios de April; v1 usa mes_pivot).

## Hoja Macro — pendiente para v2

La hoja Macro tiene FX (mensual, 2024-01..2027-03) y CPI por país en
formato wide. Estructura:

- Filas 3-10: FX por país (AR, BR, MX, CL, CO, EC, PE, OT)
- Filas 14-22: CPI por país (incluyendo USA)
- Fila 26+: "IMPACTO FX-CPI" — bloque con factor combinado por país y mes

El P&L del Excel original NO referencia ninguna celda de Macro, por eso v1
no la aplica. Si en una iteración futura se quiere convertir líneas de
moneda local a USD (caso de Argentina especialmente con inflación alta), el
hook está en `src/logica/macro_fx_cpi.py::aplicar_fx_cpi`.
