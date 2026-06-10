# Briefing: Proyecto RR AI — Run Rate HTML/B2B

Este documento resume el estado completo del proyecto para que una nueva sesión
de Claude tenga todo el contexto sin necesidad de leer el código.

---

## 1. Qué es este proyecto

Aplicación web en **Python + Streamlit** que emula la lógica de un modelo Excel
de **Run Rate financiero** para el canal **HTML/B2B** de Despegar (OTA de viajes).

El usuario carga datos transaccionales del mes actual (Base 2026), configura un
mes pivot y un horizonte de proyección, y obtiene un **P&L proyectado** a N meses
descargable en Excel.

El modelo original es un archivo Excel (`HTML - Modelo Run Rate.xlsx`) con 21 hojas.
La v1 replica la lógica de 6 de esas hojas.

**Estado**: v1 funcional end-to-end completada. Todos los módulos implementados y testeados.

---

## 2. Stack técnico

| Componente | Tecnología |
|---|---|
| UI | Streamlit |
| Datos | pandas + openpyxl |
| Visualización | plotly |
| Export Excel | xlsxwriter |
| Tests | pytest |
| Validación | funciones propias (list[str] de errores en español) |
| Python | 3.x con type hints en toda firma pública |

Convenciones: comentarios y docstrings **en español**, imports absolutos dentro de `src/`.

---

## 3. Estructura de carpetas

```
RR AI/
├── app.py                           Entry point Streamlit
├── config/
│   └── settings.py                  Todas las constantes: paths, mapeos, columnas, schema P&L
├── data/
│   ├── precargado/                  Macro + Estacionalidades + Base 2025 (fijas, no se editan)
│   ├── ejemplos/                    Archivos de prueba
│   └── referencia/                  Baseline de comparación para tests
├── src/
│   ├── io/
│   │   ├── readers.py               Lectores de Excel (Base 2026, Contable)
│   │   ├── validators.py            Validación de inputs (mensajes en español)
│   │   └── precargado.py            Loaders con @lru_cache para archivos pre-cargados
│   ├── logica/
│   │   ├── proyeccion_orders.py     Proyección de orders con estacionalidad
│   │   ├── proyeccion_asp.py        Proyección de ASP
│   │   ├── proyeccion_gb.py         Gross Bookings = orders × ASP
│   │   ├── lineas_transaccionales.py 7 líneas de Base 2026 via ratio × GB_proy
│   │   ├── lineas_contables.py      16 líneas de Base 2025 via ratio × GB_proy
│   │   ├── macro_fx_cpi.py          Placeholder (v1: passthrough, sin efecto)
│   │   ├── mapeo_canal.py           B2B → HTML
│   │   └── pnl_builder.py           Orquestador del pipeline completo
│   ├── ui/
│   │   ├── wizard.py                Stepper de 4 pasos + navegación lateral
│   │   ├── step_upload_base.py      Paso 1: upload Base 2026
│   │   ├── step_upload_contable.py  Paso 2: upload Contable (opcional)
│   │   ├── step_config.py           Paso 3: mes pivot + horizonte + día corte
│   │   └── step_resultado.py        Paso 4: resultados, filtros, gráficos, descarga
│   └── export/
│       └── excel_writer.py          Generador Excel (2 formatos: long + evolution)
└── tests/
    ├── test_io.py                   Tests de validación de inputs
    └── test_logica.py               Tests de proyección + comparación con baseline Excel
```

---

## 4. Flujo de datos

### Inputs del usuario (por ejecución)
- **Base 2026** (obligatorio): Datos MTD del mes pivot. Hoja "Base 2026" del Excel.
  - Columnas clave: `Mes RI`, `pais`, `marca`, `LOB`, `productooriginal`, `viaje`, `gross_bookings`, `orders` + 19 líneas transaccionales
- **Contable** (opcional): Tabla contable de referencia. En v1 no afecta los cálculos, solo se muestra.

### Archivos pre-cargados (en `data/precargado/`, cacheados en memoria)
- **Macro**: FX y CPI por país/mes — cargado pero no aplicado en v1
- **Estacionalidad orders B2B**: Índices por `(pais, viaje, producto_agrupado)` × mes
- **Estacionalidad B2B ASP**: Igual, para ASP
- **Base 2025**: Datos históricos — fuente para 16 líneas del P&L

### Parámetros de configuración
- **mes_pivot** (1–12): Mes base de la proyección
- **horizonte** (1–24, default 12): Meses a proyectar
- **dia_corte** (opcional): Si Base 2026 es MTD parcial al día N, anualiza al mes completo
- **escenario**: Etiqueta libre (no afecta cálculos)

---

## 5. Lógica financiera (pipeline completo)

**Principio central**: todo es ratio-based. Las proyecciones siguen:
```
linea_proy[mes] = (linea_MTD / gross_bookings_MTD) × gross_bookings_proy[mes]
```

### Paso 1 — Agregación pivot
- Filtra Base 2026 al `mes_pivot`
- Agrupa por `(pais, marca, viaje, producto)` → sumas del mes pivot
- Si `dia_corte` está definido: multiplica por `(días_del_mes / dia_corte)` para anualizar

### Paso 2 — Proyección de orders
```
orders_proy[mes] = orders_pivot × estac_orders[concat, mes] / estac_orders[concat, mes_pivot]
concat = pais + viaje + producto_agrupado
```
Donde `producto_agrupado` mapea Cars/Cruises/Dest.Serv./Insurance/Vacation Rentals → `ONA`.

### Paso 3 — Proyección de ASP
```
asp_proy[mes] = asp_pivot × estac_asp[concat, mes] / estac_asp[concat, mes_pivot]
asp_pivot = gross_bookings_pivot / orders_pivot
```

### Paso 4 — Gross Bookings proyectado
```
gross_bookings_proy[mes] = orders_proy[mes] × asp_proy[mes]
```

### Paso 5 — Líneas transaccionales (fuente: Base 2026, 7 líneas)
Estas líneas vienen del mes pivot del usuario y se proyectan por ratio × GB:
- `up_front_incentives`, `fees`, `cost_of_installments`, `credit_card_processing`
- `affiliates`, `cancellations`, `other_incentives`

### Paso 6 — Líneas históricas (fuente: Base 2025, 16 líneas)
Mismo mecanismo pero usando datos del año anterior como base del ratio:
- `income_from_outsourced_services`, `errors`, `revenue_tax`, `other_transactional_taxes`
- `back_end_incentives`, `breakage_revenue`, `customer_claims`, `customer_service`
- `media_revenue`, `vendor_commissions`, `intercompany`, `white_labels_api`
- `operations`, `frauds`, `efecto_financiero`, `dif_fx`, `currency_hedge`

### Paso 7 — Ajustes especiales
- `commercial_discounts = 0` (hardcodeado, replica el Excel v1)
- Para Brasil: `efecto_financiero -= cost_of_installments`

### Paso 8 — Métricas derivadas
```
net_revenue    = upf + fees + cancellations + income_from_outsourced + other_incentives
               + revenue_tax + back_end_incentives + commercial_discounts
               + breakage_revenue + media_revenue

npv            = suma de todas las líneas del P&L (28 líneas)

bimo           = dif_fx + currency_hedge   (literal del Excel, aunque parezca raro)

revenue_margin = upf + fees + cancellations
```

### Paso 9 — Ensamblado P&L
- Columnas dimensiones: `concatenado`, `escenario`, `mes_pivot`, `pais`, `lob_canal`, `marca`, `partner`, `viaje`, `producto`, `numero_mes_proyectado`, `mes_proyectado`
- Columnas métricas: las 28 líneas + 4 derivadas (32 métricas en total)
- `lob_canal = "HTML"` (mapeado desde `LOB = "B2B"`)
- `Mes 1 = mes_pivot` (no mes_pivot+1)

---

## 6. Mapeos clave (en config/settings.py)

### Países
| Input en Base 2026 | Código |
|---|---|
| Argentina | AR |
| Brasil / Brazil | BR |
| México / Mexico | MX |
| Chile | CL |
| Colombia | CO |
| Ecuador | EC |
| Perú / Peru | PE |
| Other Countries / Uruguay / Paraguay | OT |

### Productos agrupados (para lookup de estacionalidad)
| Productos | Agrupado |
|---|---|
| Vuelos / Flights | Flights |
| Hoteles / Hotels | Hotels |
| Paquetes / Packages General | Packages General |
| Cars, Cruceros, Dest. Services, Insurance, Vacation Rentals | ONA |

### Canal
- Input: `LOB = "B2B"` → Output: `lob_canal = "HTML"`

---

## 7. UI — Wizard de 4 pasos

Estilo: paleta Despegar (azul #2E5BFF, fondo gris claro #F7F9FC). Stepper en sidebar.

**Paso 1** — Upload Base 2026
- Uploader Excel, lee hoja "Base 2026" (fallback: primera hoja)
- Valida esquema, muestra conteo de filas y países

**Paso 2** — Upload Contable (opcional)
- No bloquea el avance aunque no se cargue
- En v1 solo aparece como tabla de referencia en el Paso 4

**Paso 3** — Configuración
- Date picker: mes pivot (ignora el día)
- Botón "Usar fecha de hoy"
- Slider: horizonte (1–24)
- Input texto: nombre de escenario
- Expander "Avanzado": día de corte para anualizar MTD parcial

**Paso 4** — Resultados
- Botón "Ejecutar proyección" (dispara `build_pnl()`)
- 4 metric cards: Net Revenue, NPV, BIMO, Revenue Margin (totales)
- Filtros dropdown: país, marca, viaje, producto
- Gráfico de líneas Plotly: net_revenue / bimo / revenue_margin por mes
- Tabla completa del P&L
- Botones de descarga: "P&L completo" (formato long) + "P&L Evolution" (formato pivotado)

---

## 8. Excel de salida (2 formatos)

### Hoja "P&L" (formato long)
- Una fila por combinación `(concatenado, mes)`
- Todas las dimensiones + todas las métricas
- Columnas de dimensión ancho 18, métricas ancho 14

### Hoja "P&L Evolution" (formato pivotado)
- Filas: 28 líneas del P&L + 4 derivadas
- Columnas: meses en español (Enero, Febrero, …)
- Header: fondo azul oscuro (#0F172A), texto blanco, negrita
- Filas subtotales (net_revenue, npv, bimo, revenue_margin): fondo azul claro (#E8EDFF), negrita
- Separador de miles en números

---

## 9. Tests

### test_io.py
- DataFrame mínimo válido pasa sin errores
- Detecta: columnas faltantes, nulls en obligatorias, `Mes RI` fuera de 1–12, `LOB` inválido
- Skips si no existe el archivo de referencia real

### test_logica.py
- Verifica estructura del P&L output (dimensiones, métricas, 12 meses por combo)
- Verifica que Mes 1 = mes_pivot
- Verifica fórmulas derivadas: bimo = dif_fx + currency_hedge, etc.
- Verifica que se genere Excel sin errores
- **Comparación con baseline**: tolerancia 15% en totales (orders, GB, net_revenue, revenue_margin)
  - La diferencia residual viene de simplificaciones aceptadas (sin elasticidades, sin shift ASP, sin override upf-fees de abril)

---

## 10. Diferencias conocidas con el Excel original

| Aspecto | v1 (Python) | Excel original | Impacto |
|---|---|---|---|
| Orders | Ratio simple × estac[m]/estac[pivot] | Gradiente + elasticidades + ajustes manuales | ~1–5% diferencia |
| ASP | Mismo mecanismo | Con ajustes adicionales | ~1–5% diferencia |
| Cálculo GB | orders[m] × ASP[m] | orders[m] × ASP[m-1] (shift) | Menor |
| FX/CPI | No aplicado | Aplicado via Macro | No aplica en v1 |
| Up Front Incentives | Ratio del mes pivot | Ratio hardcodeado de abril | ~5–10% varianza |
| Contable en P&L | Solo referencia | Maneja ~6 líneas | No aplica en v1 |

---

## 11. Estado de módulos

| # | Módulo | Estado |
|---|---|---|
| M1 | Estructura de carpetas + setup | ✅ |
| M2 | Reader/validator Base 2026 | ✅ |
| M3 | Reader/validator Contable | ✅ |
| M4 | Carga pre-cargados (Macro + Estacionalidades + Base 2025) | ✅ |
| M5 | Stepper wizard | ✅ |
| M6 | Paso 1 upload Base 2026 | ✅ |
| M7 | Paso 2 upload Contable | ✅ |
| M8 | Paso 3 configuración | ✅ |
| M9 | Proyección orders | ✅ |
| M10 | Proyección ASP + GB | ✅ |
| M11 | Líneas transaccionales | ✅ |
| M12 | Líneas históricas (Base 2025) | ✅ |
| M13 | FX/CPI | ⚠️ Saltado en v1 (passthrough) |
| M14 | Mapeo canal + ensamblado P&L | ✅ |
| M15 | Vista resultado + export Excel | ✅ |

---

## 12. Pendiente para v2

- Aplicar FX/CPI via hoja Macro
- Elasticidades en proyección de orders/ASP (Modelo Orders / Modelo ASP del Excel)
- Shift de ASP: usar ASP[m-1] en lugar de ASP[m] para calcular GB
- Override de ratios Up Front Incentives para el mes de abril
- Refactor del Paso 4 en componentes separados (`src/ui/components/`)
- Definir si Contable debe manejar líneas del P&L en v2

---

## 13. Cómo correr la app

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
streamlit run app.py
# Abre http://localhost:8501
```

---

## 14. Archivos más importantes para entender la lógica

1. `config/settings.py` — todas las constantes y mapeos
2. `src/logica/pnl_builder.py` — orquestador del pipeline (leer primero para entender el flujo)
3. `src/logica/lineas_transaccionales.py` y `lineas_contables.py` — lógica de ratio
4. `src/logica/proyeccion_orders.py` — estacionalidad
5. `src/ui/step_resultado.py` — UI de resultados
6. `src/export/excel_writer.py` — formato de salida Excel
7. `tests/test_logica.py` — mejor documentación del comportamiento esperado

---

*Generado el 2026-06-09 desde el proyecto en `c:\Users\tiago.harari\Desktop\RR AI`*
