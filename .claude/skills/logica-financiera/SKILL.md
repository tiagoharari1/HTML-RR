---
name: logica-financiera
description: >
  Skill de mejora de la matemática financiera del modelo Run Rate HTML/B2B.
  Cubre: fidelidad al Excel original, validación de continuidad de tendencia en
  actuals+budget, corrección de proyecciones con quiebres anómalos (e.g. 50k
  orders en mayo → 250 en junio), y uso de datos históricos reales como ancla
  estadística para la proyección. Invocar siempre que el trabajo toque
  src/logica/, config/settings.py, o cualquier cálculo de proyección de orders,
  ASP, gross_bookings o líneas P&L.
---

# Skill: Mejora de Lógica Financiera — Run Rate HTML/B2B

## Cuándo aplicar esta skill

Actívala al inicio de cualquier sesión que toque:

- `src/logica/proyeccion_orders.py`
- `src/logica/proyeccion_asp.py`
- `src/logica/proyeccion_gb.py`
- `src/logica/lineas_transaccionales.py`
- `src/logica/lineas_contables.py`
- `src/logica/pnl_builder.py`
- `config/settings.py` (constantes de proyección)
- Cualquier cálculo numérico que produzca el P&L final

---

## 1. Problema central que esta iteración resuelve

El modelo v1 proyecta cada línea aplicando un **ratio único del mes pivot** a
todos los meses futuros. Esto genera quiebres absurdos cuando el mes pivot es
atípico o cuando la serie de datos tiene tendencia:

> **Ejemplo real**: si en Abril hubo 50.399 orders y en Mayo 52.923 orders,
> Junio no puede ser 250 orders. Pero el modelo actual puede producir eso si
> el ratio de Estacionalidad del mes origen es alto y el mes destino bajo,
> sin anclar el resultado a la magnitud observada.

El objetivo es que la proyección sea **matemáticamente coherente** con la
serie histórica: respete la tendencia real de los actuals, use el budget como
señal de escala, y aplique la estacionalidad relativa —no en valores absolutos—
para modular la curva proyectada.

---

## 2. Fuentes de verdad a respetar (en orden de prioridad)

1. **Excel original** (`HTML - Modelo Run Rate.xlsx`) — hojas:
   - `Modelo Orders`: lógica de proyección de orders con elasticidades y shifts
   - `Modelo ASP`: ídem para ASP
   - `Calculo GB`: cómo se combina orders × ASP con posibles overrides
   - `P&L`: output objetivo y fórmulas de líneas derivadas
   - `Estacionalidad orders B2B`, `Estacionalidad B2B ASP`: índices mensuales
   - `Macro`: FX / CPI por país y mes
2. **Base 2026** — actuals MTD del año en curso (datos reales)
3. **Base 2025** — actuals del año anterior (proxy de tendencia histórica)
4. **Budget / Plan** — si el usuario lo provee en el futuro: señal de escala esperada

Cuando una decisión de implementación contradiga el Excel original, **preguntar
al usuario** antes de improvisar.

---

## 3. Problemas conocidos en la implementación v1

### 3.1 Estacionalidad sin ancla de nivel

**Código actual** (`proyeccion_orders.py:87`):
```python
orders_proy = orders_pivot * indice_m / indice_pivot
```

**Problema**: si `indice_m / indice_pivot` es muy bajo (e.g. 0.005) el
resultado es ridículo aunque los actuals muestren una serie estable de 50k+
orders por mes.

**Causa raíz**: la estacionalidad en el Excel no es un ratio sobre el mes
pivot — es un índice sobre la media anual (o sobre el total del año). Al
dividir por `indice_pivot` se amplifica el error cuando el mes pivot no es
representativo.

**Corrección esperada**: usar la media de los últimos N meses de actuals como
nivel base, y modular con la curva de estacionalidad relativa sobre esa media:

```
nivel_base = mean(orders_actuals[-N_meses])
orders_proy[m] = nivel_base * indice_m / mean(indices_todos_los_meses)
```

### 3.2 Ratio de líneas transaccionales congelado en el mes pivot

**Código actual** (`lineas_transaccionales.py:44`):
```python
agg[f"ratio_{linea}"] = r[linea] / r["gross_bookings"]  # ratio fijo del pivot
```

**Problema**: el ratio puede ser atípico en el mes pivot (fin de año fiscal,
campaña puntual, etc.). Se propaga a todos los meses sin corrección.

**Corrección esperada**: calcular el ratio como promedio ponderado de los
últimos meses disponibles en Base 2026 (no solo el mes pivot), o al menos
detectar outliers estadísticos y reemplazarlos por la mediana histórica.

### 3.3 Sin validación de continuidad

El modelo no verifica que la proyección sea continua con los actuals. No hay
ningún assert ni warning cuando un mes proyectado es < 1% del mes anterior.

**Corrección esperada**: agregar una función de validación post-build que
detecte quiebres anómalos en la serie de orders/GB y los reporte como
warnings en la UI (no errores fatales).

### 3.4 Base 2025 usada de forma estática

Las líneas de Base 2025 se proyectan con un ratio único (`mes_pivot` del año
anterior) sin considerar la tendencia histórica ni la estacionalidad de ese año.

---

## 4. Objetivos de la iteración de mejora financiera

### Objetivo 1: Proyección de orders con ancla estadística

Reemplazar la proyección por ratio simple con un modelo que:
- Calcula el **nivel base** usando media de los últimos meses de actuals
  disponibles en Base 2026 (todos los meses, no solo el pivot)
- Aplica la curva de estacionalidad de forma **relativa** (índice del mes m /
  media anual de índices), no absoluta
- Resultado: la proyección nunca se aleja >2× del nivel observado en actuals
  sin justificación estacional explícita

### Objetivo 2: Ratios de líneas como promedios robustos

Para cada línea transaccional:
- Calcular el ratio `linea / gross_bookings` para **todos los meses
  disponibles** en Base 2026 (no solo el pivot)
- Usar la **mediana** en lugar de un único ratio (más robusto a outliers)
- Si solo hay 1 mes disponible, usar ese ratio pero emitir un warning

### Objetivo 3: Validación de continuidad (post-build check)

Nueva función `validar_continuidad_pnl(pnl_df) -> list[str]` que:
- Para cada combo (pais, marca, viaje, producto), verifica que ningún mes
  proyectado tenga orders o gross_bookings < 5% del promedio del período
- Devuelve lista de strings con warnings descriptivos en español
- Se llama desde `build_pnl()` y los warnings se muestran en la UI

### Objetivo 4: Reconciliación con actuals en el período histórico

Cuando Base 2026 tiene datos de múltiples meses (e.g. enero a mayo):
- El modelo debería poder "calibrarse" contra esos meses
- Es decir, si corremos el modelo con pivot=Febrero, los meses Marzo/Abril/Mayo
  proyectados deberían ser comparables a los actuals reales de esos meses
- Esta comparación permite ajustar los índices de estacionalidad o los ratios
  de líneas antes de proyectar meses futuros

---

## 5. Approach técnico recomendado para implementar

### Paso 1: Agregar función de nivel base en `proyeccion_orders.py`

```python
def nivel_base_orders(base_2026: pd.DataFrame, combo: dict, mes_pivot: int) -> float:
    """Calcula la media de orders de los meses disponibles <= mes_pivot."""
    ...
```

### Paso 2: Refactorizar `proyectar_orders()` para usar nivel base

```python
orders_proy = nivel_base * (indice_m / media_indices_anuales)
```

### Paso 3: Refactorizar `calcular_ratios_base_2026()` para usar mediana

```python
# Usar todos los meses disponibles, no solo mes_pivot
df_todos = base_2026.loc[base_2026["Mes RI"] <= mes_pivot]
# ... calcular ratio por mes y tomar mediana
```

### Paso 4: Agregar `validar_continuidad_pnl()` en `pnl_builder.py`

```python
def validar_continuidad_pnl(pnl: pd.DataFrame, umbral: float = 0.05) -> list[str]:
    """Detecta quiebres anómalos en la serie proyectada."""
    ...
```

### Paso 5: Integrar warnings en la UI (`step_resultado.py`)

Mostrar warnings de continuidad en un `st.warning()` collapsable antes del
preview de la tabla.

---

## 6. Restricciones y convenciones

- **No romper la interfaz pública** de `build_pnl()` — cualquier parámetro
  nuevo debe ser opcional con default backward-compatible
- **Tests primero**: antes de refactorizar una función, escribir un test que
  capture el comportamiento actual (puede que falle con el nuevo comportamiento
  —eso está bien, es el objetivo)
- **Tolerancia del test de comparación**: el test `test_comparacion_contra_excel_original`
  corre con 15% de tolerancia. Si los cambios mejoran la precisión, actualizar
  la tolerancia al nuevo valor más ajustado
- **Mensajes en español** — todos los warnings, logs y docstrings en español
- **No usar print()** — usar `logging.warning()` o retornar lista de mensajes

---

## 7. Checklist antes de cerrar una tarea de mejora financiera

- [ ] La proyección de orders/GB nunca produce valores <5% del nivel observado
      en actuals sin justificación explícita de estacionalidad
- [ ] Los ratios de líneas transaccionales usan mediana de múltiples meses
      cuando hay datos disponibles
- [ ] `validar_continuidad_pnl()` existe y corre dentro de `build_pnl()`
- [ ] El test de comparación contra Excel original pasa (con tolerancia ≤15%)
- [ ] No hay regresiones en tests existentes (`pytest tests/`)
- [ ] Los warnings de continuidad aparecen en la UI si hay quiebres
- [ ] CLAUDE.md actualizado con decisiones tomadas en esta iteración
