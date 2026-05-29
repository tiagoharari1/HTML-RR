# CLAUDE.md — Contexto del proyecto RR AI

Este archivo le da contexto persistente a Claude Code en cada sesión. Léelo
antes de empezar a trabajar.

---

## 1. Misión del proyecto

Construir, de forma **incremental y modular**, una aplicación web en Python
(Streamlit) que emule la lógica del modelo Excel **Run Rate** del canal
**HTML/B2B** de la empresa. El usuario carga inputs, configura parámetros,
ejecuta la emulación y obtiene un **P&L proyectado descargable en Excel**.

El modelo Excel original (`HTML - Modelo Run Rate.xlsx`) tiene 21 hojas; para
esta v1 solo se usan 6:

- **Base 2026** — datos transaccionales MTD (input del usuario)
- **Contable** — referencia contable por línea P&L (input del usuario)
- **Macro** — FX y CPI por país y mes (pre-cargada)
- **Estacionalidad orders B2B** — índices mensuales por concatenado (pre-cargada)
- **Estacionalidad B2B ASP** — índices mensuales por concatenado (pre-cargada)
- **P&L** — output dimensional

---

## 2. Decisiones de diseño (tomadas con el usuario)

### Stack
- **Streamlit** como framework de UI
- **pandas + openpyxl** para Excel
- **pydantic** para validación de esquemas
- **plotly** para gráficos
- **xlsxwriter** para escribir Excel de salida
- **pytest** para tests
- Versiones sin pinear estricto (compatibilidad con Python 3.14)

### Flujo de datos
- El **usuario sube en cada ejecución**: Base 2026 y Contable
- **Pre-cargadas en la app** (en `data/precargado/`): Macro, Estacionalidad orders,
  Estacionalidad ASP
- Editables por el usuario: solo Base 2026 y Contable
- Pre-cargadas: fijas, no se editan en la app

### Parámetros
- **Mes pivot**: lo ingresa el usuario manualmente en el wizard
- **Horizonte de proyección**: configurable por el usuario (default 12,
  rango 1–24)
- **Escenarios**: uno solo por ejecución en la v1 (campo `escenario` se
  guarda como label pero no afecta cálculos)

### Output
- **Excel descargable** (.xlsx) con la hoja P&L
- **Vista previa en la app** antes de descargar: tabla con totales +
  filtros (país / marca / producto / LOB) + gráficos resumen
  (net_revenue, bimo, revenue_margin)
- **Deployment**: corre local desde VS Code

### Mapeo de canal
- Base 2026 viene con `LOB = "B2B"`
- P&L output usa `lob_canal = "HTML"`
- Mapeo hardcodeado en `config/settings.py`: `MAPEO_LOB_CANAL = {"B2B": "HTML"}`

---

## 3. Lógica financiera

### Proyección de orders y gross_bookings (M9, M10)

- **Orders proyectado**: se calcula multiplicando el dato MTD por el índice
  de Estacionalidad orders B2B correspondiente al `concatenado`
  (país + canal + marca + viaje + producto), normalizando por el mes pivot.
- **ASP proyectado**: análogamente con la hoja Estacionalidad B2B ASP.
- **gross_bookings proyectado**: `orders_proy × ASP_proy`.

### Líneas transaccionales (M11)

Cada línea transaccional se proyecta como un **ratio MTD aplicado al
gross_bookings** (o `orders`, según corresponda) **proyectado**:

```
linea_proy[mes] = (linea_MTD / gross_bookings_MTD) × gross_bookings_proy[mes]
```

Líneas afectadas:
`up_front_incentives`, `fees`, `commercial_discounts`, `cost_of_installments`,
`credit_card_processing`, `affiliates`, `other_incentives`, `errors`,
`revenue_tax`, `other_transactional_taxes`, `cancellations`,
`breakage_revenue`, `customer_claims`, `customer_service`, `media_revenue`,
`frauds`, `efecto_financiero`, `dif_fx`, `currency_hedge`.

> Pendiente: confirmar para cada línea si el denominador es `gross_bookings`,
> `orders`, o una métrica intermedia.

### Líneas no transaccionales (M12)

Se toman **directo de la hoja Contable**, sin proyección por ratios:

- `vendor_commissions`
- `intercompany`
- `white_labels_api`
- `operations`
- `back_end_incentives`
- `income_from_outsourced_services`

### Aplicación de FX y CPI (M13)

Macro aplica a **todas las líneas del P&L**. Convierte de moneda local a USD
usando la curva de FX por país y mes, y ajusta por CPI cuando corresponde.

> Pendiente: definir cuáles líneas necesitan solo FX, cuáles también CPI,
> y cómo se combina el factor en función del mes pivot.

### Ensamblado del P&L (M14)

DataFrame final con:

- **Dimensiones**: `concatenado`, `escenario`, `mes_pivot`, `pais`,
  `lob_canal`, `marca`, `partner`, `viaje`, `producto`,
  `numero_mes_proyectado`, `mes_proyectado`
- **Métricas**: ver `config.settings.PNL_METRICAS` (lista completa)

### Métricas derivadas

> Pendiente de definir las fórmulas exactas de `net_revenue`, `npv`, `bimo`,
> `revenue_margin` a partir de las líneas P&L.

---

## 4. Estado del plan modular (15 módulos)

| # | Módulo | Estado |
|---|--------|--------|
| M1 | Estructura de carpetas + setup base | ✅ Completado |
| M2 | Reader y validator de Base 2026 | ✅ Completado |
| M3 | Reader y validator de Contable | ✅ Completado |
| M4 | Carga de hojas pre-cargadas (Macro + Estacionalidades + Base 2025) | ✅ Completado |
| M5 | Stepper general del wizard | ✅ Completado |
| M6 | Step 1 — upload Base 2026 | ✅ Completado |
| M7 | Step 2 — upload Contable (opcional, sólo referencia) | ✅ Completado |
| M8 | Step 3 — configuración (mes pivot + horizonte + día corte) | ✅ Completado |
| M9 | Proyección de orders con estacionalidad | ✅ Completado |
| M10 | Proyección de ASP y gross_bookings | ✅ Completado |
| M11 | Líneas transaccionales (ratios Base 2026 sobre GB) | ✅ Completado |
| M12 | Líneas históricas (ratios Base 2025 sobre GB) — repurposed | ✅ Completado |
| M13 | Aplicación de FX y CPI | ⚠️ Saltado en v1 (no usado por el Excel original) |
| M14 | Mapeo canal y ensamblado P&L final | ✅ Completado |
| M15 | Step 4 — vista de resultado + export Excel | ✅ Completado |

**v1 funcional end-to-end completada el 2026-05-27.**

### Decisiones tomadas en la sesión de v1 (cambios vs el plan original)

1. **Base 2025** se agregó como archivo pre-cargado (`data/precargado/base_2025.xlsx`).
   El Excel original la usa para ~16 líneas del P&L (income_from_outsourced_services,
   errors, revenue_tax, other_transactional_taxes, back_end_incentives,
   breakage_revenue, customer_claims, customer_service, media_revenue,
   vendor_commissions, intercompany, white_labels_api, operations, frauds,
   efecto_financiero, dif_fx, currency_hedge) vía ratio histórico × GB_proy.
2. **Contable** dejó de driver el P&L. En el Excel original no se usa para esto
   — sólo aparece como "Ultimo Cierre contable" de referencia interna en Modelo
   Palancas. v1 la mantiene en el wizard como tabla de referencia opcional.
3. **Macro (FX/CPI)** no se aplica en v1. Las cifras de Base 2026 ya vienen en
   USD y el P&L del Excel original no referencia Macro. Módulo dejado como
   passthrough (hook para v2).
4. **Estacionalidad** se indexa por `pais + viaje + producto_agrupado` (no por
   el concatenado de 5 campos). Se agregó `MAPEO_PRODUCTO_AGRUPADO` en settings.
5. **Mes proyectado**: `Mes 1 = mes_pivot` (NO mes_pivot+1). Verificado contra
   el Excel original.
6. **Día de corte**: parámetro opcional en `build_pnl(dia_corte=N)` para
   annualizar Base 2026 MTD parcial al mes completo. Default = mes completo.
7. **Fórmulas derivadas** (confirmadas contra el Excel):
   - `net_revenue` = upf + fees + cancellations + income_from_outsourced + other_incentives
                   + revenue_tax + back_end_incentives + commercial_discounts
                   + breakage_revenue + media_revenue
   - `npv` = suma de todas las líneas del P&L (upf..currency_hedge)
   - `bimo` = `dif_fx + currency_hedge` (sí, literal del Excel)
   - `revenue_margin` = upf + fees + cancellations
8. **Ajuste especial**: para país=Brasil, `efecto_financiero -= cost_of_installments`.
9. **commercial_discounts = 0** hardcodeado (replicando el Excel v1).
10. **Países nuevos**: "Other Countries", "Uruguay", "Paraguay" → mapean a `OT`.
11. **Validación contra el Excel original**: el test `test_comparacion_contra_excel_original`
    compara totales mensuales con tolerancia del 15%. La diferencia residual
    viene de simplificaciones aceptadas con el usuario (sin elasticidades del
    Modelo Orders/ASP, sin shift de ASP en Calculo GB, sin override de upf-fees
    al mes April del Excel).

### Notas de M2

- `read_base_2026(file)` acepta `Path | str | file-like` (incluye el
  `UploadedFile` de Streamlit). Por defecto lee la hoja `"Base 2026"`; si no
  existe en el workbook se cae a la primera hoja.
- El archivo real de referencia (`data/referencia/base 2026.xlsx`) tiene 39
  columnas y 7750 filas; los tests verifican que pase el validator sin errores.
- Se descartó pydantic para la validación: para un DataFrame de miles de filas
  los chequeos directos son más eficientes y más claros. El validator devuelve
  `list[str]` con mensajes en español (lista vacía = válido).
- Validaciones implementadas: columnas obligatorias y transaccionales presentes,
  nulls en obligatorias, `Mes RI` numérico en 1..12, `gross_bookings`/`orders`
  numéricos, `LOB` en el dominio de `MAPEO_LOB_CANAL` (hoy solo `"B2B"`).
- La hoja real trae países fuera del `MAPEO_PAIS_CODIGO`
  (`"Other Countries"`, `"Uruguay"`, `"Paraguay"`). M2 los deja pasar — el
  mapeo a códigos es responsabilidad de M14.

---

## 5. Estructura del repositorio

```
RR AI/
├── app.py                          Entry point Streamlit
├── requirements.txt
├── README.md
├── CLAUDE.md                       (este archivo)
├── .gitignore
├── config/
│   └── settings.py                 Paths, mapeos, columnas esperadas, schema P&L
├── data/
│   ├── precargado/                 Macro + Estacionalidades (a poblar en M4)
│   └── ejemplos/                   Archivos de prueba
├── src/
│   ├── io/
│   │   ├── readers.py              (M2, M3)
│   │   ├── validators.py           (M2, M3)
│   │   └── precargado.py           (M4)
│   ├── logica/
│   │   ├── proyeccion_orders.py    (M9)
│   │   ├── proyeccion_asp.py       (M10)
│   │   ├── proyeccion_gb.py        (M10)
│   │   ├── lineas_transaccionales.py  (M11)
│   │   ├── lineas_contables.py     (M12)
│   │   ├── macro_fx_cpi.py         (M13)
│   │   ├── mapeo_canal.py          (M14)
│   │   └── pnl_builder.py          (M14)
│   ├── ui/
│   │   ├── wizard.py               (M5)
│   │   ├── step_upload_base.py     (M6)
│   │   ├── step_upload_contable.py (M7)
│   │   ├── step_config.py          (M8)
│   │   ├── step_resultado.py       (M15)
│   │   └── components/             (M15)
│   └── export/
│       └── excel_writer.py         (M15)
├── tests/
│   ├── test_io.py
│   └── test_logica.py
└── docs/
    └── notas_logica_financiera.md  Documentación viva de la lógica
```

Cada archivo de módulo pendiente tiene un docstring que indica a qué módulo
pertenece y un `TODO Mxx` con la firma de la función a implementar.

---

## 6. Convenciones de código

- **Comentarios y docstrings en español** (es la lengua de trabajo del usuario).
- **Type hints** en toda firma pública (`from __future__ import annotations`
  en cada archivo).
- **No usar `print()` para debug** en código de producción; usar `st.write` o
  `logging`.
- **Validación de inputs**: pydantic para esquemas, mensajes de error claros
  al usuario (en español).
- **Tests**: pytest, archivos en `tests/`, nombres `test_*.py`.
- **Imports relativos**: dentro de `src/`, usar imports absolutos
  (`from src.logica.proyeccion_orders import ...`).
- **Constantes**: centralizar en `config/settings.py` — no hardcodear nombres
  de columnas, países, mapeos en la lógica de negocio.

---

## 7. Cómo correr la app

```bash
# 1. Activar venv
.venv\Scripts\Activate.ps1            # Windows PowerShell
source .venv/bin/activate             # macOS / Linux

# 2. Correr Streamlit
streamlit run app.py
```

Se abre en `http://localhost:8501`.

---

## 8. Flujo de trabajo con Claude Code

Cuando le pidas a Claude que avance con un módulo:

1. Claude debe leer este archivo primero para entender el contexto.
2. Antes de codear, debe revisar el estado del módulo en la tabla de arriba
   y los archivos relevantes (los TODOs ya indican qué falta).
3. Implementar el módulo respetando la estructura y las convenciones.
4. Agregar tests en `tests/` cuando aplique.
5. Actualizar este archivo: marcar el módulo como completado, anotar
   decisiones que se tomaron durante la implementación, y agregar cualquier
   aprendizaje al documento `docs/notas_logica_financiera.md`.
6. Si una decisión tomada en este archivo entra en conflicto con la
   realidad del Excel original, **preguntar al usuario antes de improvisar**.

---

## 9. Archivo de referencia del Excel original

El usuario tiene el archivo `HTML - Modelo Run Rate.xlsx` con la fuente de
verdad de la lógica. Cuando haya dudas sobre fórmulas, ofrecer al usuario
revisar la hoja correspondiente del Excel y traducir esa lógica a Python.

Hojas relevantes en el Excel original:
- `Base 2026`, `Contable`, `Macro`
- `Estacionalidad orders B2B`, `Estacionalidad B2B ASP`
- `P&L` (output objetivo)
- `Modelo Orders`, `Modelo ASP`, `Calculo GB`, `Modelo Palancas` —
  contienen la lógica de cómo se construyen orders y ASP proyectados;
  consultar cuando se implementen M9 y M10.
