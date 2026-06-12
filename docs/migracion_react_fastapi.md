# Plan de migración: Streamlit → FastAPI + React

**Estado**: completada el 2026-06-12  
**Fecha de redacción**: 2026-06-12  
**Objetivo**: reemplazar la capa de UI de Streamlit por un frontend React
profesional servido por un backend FastAPI, sin tocar ninguna línea de lógica
financiera.

---

## Por qué esta migración

El modelo es usado por CEOs. Eso exige:

- Animaciones fluidas y transiciones entre pasos
- Layout de datos de alta densidad (tabla P&L) que Streamlit no puede renderizar
  con control real
- Componentes de UI propios (cards de métricas, stepper animado, gráficos
  interactivos con tooltip custom)
- Sin el overhead de re-ejecución total que Streamlit dispara en cada interacción

---

## Arquitectura objetivo

```
┌─────────────────────────────────┐
│  Frontend (React + Vite)        │  Puerto 5173
│  React + Tailwind + shadcn/ui   │
│  Recharts para gráficos         │
│  React Query para datos         │
└────────────┬────────────────────┘
             │ HTTP REST (JSON + multipart)
┌────────────▼────────────────────┐
│  Backend (FastAPI)              │  Puerto 8000
│  api/main.py                    │
│  api/routes/*.py                │
│  ↓ importa sin cambios          │
│  src/logica/   src/io/          │
│  src/export/   config/          │
└─────────────────────────────────┘
```

**Regla de oro**: todo lo que está en `src/` y `config/` no se toca.
La migración es una capa encima, no una reescritura.

---

## Stack tecnológico

| Capa | Tecnología | Razón |
|------|-----------|-------|
| Backend | FastAPI + Uvicorn | Async, tipado, genera OpenAPI gratis |
| Sesiones | Archivos temporales en `/tmp/rrai_sessions/` | Sin DB, sin overhead |
| Frontend framework | React 18 + Vite | HMR rápido, ecosistema maduro |
| Estilos | Tailwind CSS v3 | Utility-first, consistente con la paleta actual |
| Componentes | shadcn/ui (Radix primitives) | Accesibilidad + headless para customizar |
| Gráficos | Recharts | Más control que Plotly en React, tree-shakeable |
| Estado del servidor | TanStack Query (React Query) | Cache, loading states, re-fetch automático |
| Estado del wizard | Zustand | Liviano, sin boilerplate de Redux |
| HTTP client | Axios | Interceptors para manejo global de errores |
| Tipos | TypeScript | Seguridad de tipos end-to-end con el schema FastAPI |
| Animaciones | Framer Motion | Transiciones de pasos, micro-interacciones |

---

## Estructura de carpetas final

```
RR AI/
├── api/                            ← NUEVO
│   ├── main.py                     ← FastAPI app + CORS + montaje de rutas
│   ├── session.py                  ← Manejo de sesiones en disco
│   ├── models.py                   ← Pydantic request/response schemas
│   └── routes/
│       ├── upload.py               ← POST /upload/base2026, /upload/contable
│       ├── config.py               ← POST /config
│       ├── build.py                ← POST /build (ejecuta proyección)
│       ├── export.py               ← GET /export/pnl, /export/evolution
│       └── data.py                 ← GET /actuals, /budget, /status
├── frontend/                       ← NUEVO
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx                 ← Router + layout shell
│       ├── api/
│       │   └── client.ts           ← Axios instance + todas las llamadas API
│       ├── store/
│       │   └── wizard.ts           ← Zustand: step actual + datos de sesión
│       ├── components/
│       │   ├── ui/                 ← shadcn/ui components (Button, Card, etc.)
│       │   ├── Stepper.tsx         ← Stepper animado (sidebar)
│       │   ├── MetricCard.tsx      ← Card de métrica con número grande
│       │   ├── PnlTable.tsx        ← Tabla multi-header Real/RR/Budget
│       │   ├── RrVsBudgetChart.tsx ← Gráfico RR vs Budget (Recharts)
│       │   └── FileDropzone.tsx    ← Dropzone de upload con feedback
│       └── pages/
│           ├── Step1UploadBase.tsx
│           ├── Step2UploadContable.tsx
│           ├── Step3Config.tsx
│           └── Step4Resultado.tsx
├── app.py                          ← QUEDA (no borrar, puede coexistir)
├── requirements.txt                ← agregar: fastapi, uvicorn[standard], python-multipart
├── run_api.py                      ← NUEVO: `python run_api.py` arranca el backend
└── ...resto sin cambios...
```

---

## Contrato de API

### Sesiones

Cada browser tiene un `session_id` (UUID) guardado en `localStorage`.
El backend guarda DataFrames serializados en `/tmp/rrai_sessions/{session_id}/`.

### Endpoints

```
POST   /api/upload/base2026
  Body: multipart/form-data { file: File, session_id: str }
  Response: { ok: bool, rows: int, meses: int[], errors: str[] }

POST   /api/upload/contable
  Body: multipart/form-data { file: File, session_id: str }
  Response: { ok: bool, rows: int, errors: str[] }

POST   /api/config
  Body: JSON { session_id: str, mes_pivot: int, horizonte: int,
               dia_corte: int|null, escenario: str|null }
  Response: { ok: bool }

POST   /api/build
  Body: JSON { session_id: str }
  Response: {
    ok: bool,
    pnl: PnlRow[],          ← lista de filas del P&L (JSON)
    info_calibracion: str[],
    warnings_continuidad: str[],
    totales: { net_revenue: float, npv: float, bimo: float, revenue_margin: float }
  }

GET    /api/export/pnl?session_id=...
  Response: application/octet-stream (.xlsx)

GET    /api/export/evolution?session_id=...
  Response: application/octet-stream (.xlsx)

GET    /api/actuals
  Response: { rows: ActualsRow[] }

GET    /api/budget
  Response: { rows: BudgetRow[] }

GET    /api/status
  Response: { precargados: { macro: bool, est_orders: bool, est_asp: bool, base_2025: bool } }
```

---

## Plan de implementación paso a paso

### Fase 1 — Backend FastAPI (sin tocar frontend)

**Paso 1.1** — Agregar dependencias al `requirements.txt`:
```
fastapi
uvicorn[standard]
python-multipart
```

**Paso 1.2** — Crear `api/session.py`:
- `create_session() -> str` — genera UUID, crea carpeta en `/tmp/rrai_sessions/`
- `save_df(session_id, name, df)` — serializa con `df.to_parquet()`
- `load_df(session_id, name) -> pd.DataFrame` — deserializa
- `save_config(session_id, config: dict)` — guarda JSON
- `load_config(session_id) -> dict` — carga JSON
- `session_exists(session_id) -> bool`

**Paso 1.3** — Crear `api/models.py` con los Pydantic schemas de request/response
para cada endpoint.

**Paso 1.4** — Crear `api/routes/upload.py`:
- `POST /api/upload/base2026`: recibe el archivo, llama `read_base_2026()` y
  `validate_base_2026()` del código existente, guarda DataFrame con
  `save_df(session_id, "base_2026", df)`.
- `POST /api/upload/contable`: igual con `read_contable()` y `validate_contable()`.

**Paso 1.5** — Crear `api/routes/config.py`:
- `POST /api/config`: valida `mes_pivot` ∈ [1,12], `horizonte` ∈ [1,24],
  guarda config con `save_config()`.

**Paso 1.6** — Crear `api/routes/build.py`:
- `POST /api/build`: carga base_2026 y config de la sesión, llama `build_pnl()`,
  serializa el DataFrame resultante como lista de dicts JSON, extrae
  `pnl.attrs["info_calibracion"]` y `pnl.attrs["warnings_continuidad"]`,
  guarda el pnl en sesión para el export posterior.

**Paso 1.7** — Crear `api/routes/export.py`:
- `GET /api/export/pnl`: carga pnl de sesión, llama `write_pnl_excel()`,
  devuelve `StreamingResponse` con el .xlsx.
- `GET /api/export/evolution`: igual con `write_evolution_excel()`.

**Paso 1.8** — Crear `api/routes/data.py`:
- `GET /api/actuals`: llama `load_actuals()`, devuelve JSON.
- `GET /api/budget`: llama `load_budget()`, devuelve JSON.
- `GET /api/status`: llama `precargados_disponibles()`, devuelve JSON.

**Paso 1.9** — Crear `api/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import upload, config, build, export, data

app = FastAPI(title="RR AI API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])

app.include_router(upload.router, prefix="/api")
app.include_router(config.router, prefix="/api")
app.include_router(build.router,  prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(data.router,   prefix="/api")
```

**Paso 1.10** — Crear `run_api.py`:
```python
import uvicorn
if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
```

**Verificación Fase 1**: `python run_api.py` + abrir `http://localhost:8000/docs`
y probar todos los endpoints con la UI interactiva de FastAPI (Swagger).

---

### Fase 2 — Frontend React

**Paso 2.1** — Scaffolding:
```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npm install @tanstack/react-query axios zustand framer-motion recharts
npm install @radix-ui/react-dialog @radix-ui/react-select @radix-ui/react-tabs
npm install lucide-react clsx tailwind-merge
```

**Paso 2.2** — Configurar `tailwind.config.ts` con la paleta de marca:
```ts
colors: {
  brand: {
    DEFAULT: "#2E5BFF",
    dark:    "#1E49EF",
    darker:  "#1A3FD6",
  },
  slate: { /* tailwind defaults */ },
}
```

**Paso 2.3** — Crear `src/api/client.ts`:
- Instancia de Axios con `baseURL: "http://localhost:8000"`
- Interceptor de error global que muestra toast
- Funciones tipadas por endpoint: `uploadBase2026()`, `uploadContable()`,
  `setConfig()`, `buildPnl()`, `getActuals()`, `getBudget()`, `getStatus()`
- URLs de export como strings para usar en `<a href>` directo

**Paso 2.4** — Crear `src/store/wizard.ts` con Zustand:
```ts
interface WizardState {
  sessionId: string          // persistido en localStorage
  step: 0 | 1 | 2 | 3
  base2026Loaded: boolean
  contableLoaded: boolean
  config: { mesPivot: number, horizonte: number, diaCorte: number|null, escenario: string }
  pnlResult: PnlResult | null
  setStep: (n: number) => void
  setPnlResult: (r: PnlResult) => void
  // ...
}
```

**Paso 2.5** — Crear `src/components/Stepper.tsx`:
- Props: `steps: string[]`, `currentStep: number`
- Animación con Framer Motion: entrada del dot activo con `animate` + `spring`
- Conector vertical entre pasos con gradiente opacity
- Mismos colores que el stepper actual de Streamlit pero con CSS real

**Paso 2.6** — Crear `src/components/FileDropzone.tsx`:
- Drag & drop nativo + click para seleccionar
- Estado visual: idle / dragging / uploading / success / error
- Animación de éxito con scale + checkmark SVG animado (Framer Motion)
- Muestra nombre del archivo + número de filas tras upload exitoso

**Paso 2.7** — Crear `src/pages/Step1UploadBase.tsx`:
- `<FileDropzone>` para Base 2026
- Llama `uploadBase2026(sessionId, file)` con React Query `useMutation`
- En éxito: muestra badge "✓ {rows} filas cargadas, meses {meses}"
- Errores de validación listados como `<ul>` con ícono de alerta

**Paso 2.8** — Crear `src/pages/Step2UploadContable.tsx`:
- Igual que Step1 pero con `uploadContable()` y badge de "opcional"

**Paso 2.9** — Crear `src/pages/Step3Config.tsx`:
- Select de mes pivot (1–12 con nombres en español)
- Slider o number input para horizonte (1–24, default 12)
- Input opcional de día de corte
- Input opcional de escenario
- Preview en tiempo real: "Proyectando desde Mayo hasta Abril del año siguiente"

**Paso 2.10** — Crear `src/components/MetricCard.tsx`:
- Número grande (`text-4xl font-bold tabular-nums`)
- Label small-caps tracking-widest arriba
- Borde superior de 3px brand color
- Hover: `translateY(-2px)` + shadow más profundo (Framer Motion)
- Misma lógica visual que `.rrai-metric` del CSS actual

**Paso 2.11** — Crear `src/components/RrVsBudgetChart.tsx`:
- Recharts `<ComposedChart>`: líneas sólidas para RR, punteadas para Budget
- Custom `<Tooltip>` con fondo blanco, border `#E2E8F0`, valores formateados
  con `toLocaleString()`
- Eje X con nombres de mes cortos en español
- Misma paleta que el gráfico Plotly actual

**Paso 2.12** — Crear `src/components/PnlTable.tsx`:
- Multi-header con grupos Real / Run Rate / Budget
- Cada grupo con su color de fondo (azul / ámbar / violeta) — mismos que `_BG_GRUPO`
- Filas de subtotal en negrita con borde superior más grueso
- Fila Operating Contribution con fondo más saturado
- Sticky primera columna (labels) para scroll horizontal
- Virtualización con `react-window` si hay >50 filas (para performance)

**Paso 2.13** — Crear `src/pages/Step4Resultado.tsx`:
- Botón "Ejecutar proyección" → `useMutation` con `buildPnl()`
- Durante carga: spinner con texto "Calculando P&L proyectado..."
- En éxito: 4 `<MetricCard>` + `<RrVsBudgetChart>` + `<PnlTable>`
- Accordions colapsables para "Calibración aplicada" y "Avisos de continuidad"
- Botones de descarga como `<a href="/api/export/pnl?session_id=...">` con
  atributo `download` — nativo del browser, sin JS extra

**Paso 2.14** — Crear `src/App.tsx`:
- Layout: sidebar (240px fixed) + main content (flex-1)
- Sidebar: logo Despegar + `<Stepper>` + metadata
- Main: `<AnimatePresence>` de Framer Motion para transición entre pasos
- Transición: `x: 20 → 0` con `opacity: 0 → 1` al entrar cada paso

**Paso 2.15** — Configurar `vite.config.ts` con proxy:
```ts
server: {
  proxy: {
    '/api': 'http://localhost:8000'
  }
}
```
Esto evita problemas de CORS en desarrollo y permite usar `/api/...` directamente
desde el frontend.

---

### Fase 3 — Integración y ajuste visual

**Paso 3.1** — Correr ambos servidores en paralelo:
```bash
# Terminal 1
python run_api.py

# Terminal 2
cd frontend && npm run dev
```

**Paso 3.2** — Prueba end-to-end con el archivo real de Base 2026:
1. Subir `data/ejemplos/base 2026.xlsx` en Step 1
2. Saltar Contable en Step 2
3. Configurar mes pivot = 5 (Mayo), horizonte = 12
4. Ejecutar y verificar que los números del P&L son iguales a los de la app Streamlit
5. Descargar ambos Excel y comparar con los del export actual

**Paso 3.3** — Ajuste visual fino:
- Verificar que las fuentes, pesos y tamaños coinciden con los del CSS de `app.py`
- Paleta de colores: usar exactamente `#2E5BFF`, `#0F172A`, `#64748B`, `#E2E8F0`
- Comprobar que el stepper tiene el dot animado (pulse-ring) en el paso activo
- Comprobar que las metric cards tienen el hover de translateY(-2px)

**Paso 3.4** — Actualizar `CLAUDE.md`:
- Marcar la migración como completada
- Documentar el nuevo flujo de arranque (`python run_api.py` + `npm run dev`)
- Actualizar la sección de "Stack" con React + FastAPI

---

## Qué NO cambia

| Archivo/carpeta | Estado |
|----------------|--------|
| `src/logica/` | Sin tocar |
| `src/io/` | Sin tocar |
| `src/export/` | Sin tocar |
| `config/settings.py` | Sin tocar |
| `data/precargado/` | Sin tocar |
| `tests/` | Sin tocar |
| `app.py` | Se mantiene (puede coexistir con el nuevo stack) |

---

## Cómo correr la app migrada

```bash
# 1. Activar venv
.venv\Scripts\Activate.ps1

# 2. Backend (terminal 1)
python run_api.py
# → API en http://localhost:8000
# → Docs en http://localhost:8000/docs

# 3. Frontend (terminal 2)
cd frontend
npm run dev
# → UI en http://localhost:5173
```

---

## Prompt para Claude Code

Copiar y pegar este prompt tal cual en Claude Code para ejecutar la migración:

```
Lee docs/migracion_react_fastapi.md completo antes de empezar.

Implementa la migración de Streamlit a FastAPI + React según ese documento.
Respeta el orden exacto de las fases y pasos numerados.

Restricciones absolutas:
- No modificar ningún archivo dentro de src/, config/, data/, tests/
- No borrar app.py
- Toda la lógica financiera permanece intacta

Empieza por la Fase 1 (backend FastAPI) completa. Cuando termines la Fase 1,
verifica que `python run_api.py` levanta sin errores y que los endpoints
/api/status y /api/upload/base2026 responden correctamente usando los archivos
de data/ejemplos/ como test. Luego avanza a la Fase 2 (frontend React).

Al terminar cada paso numerado, marca el progreso brevemente (ej: "✓ Paso 1.3 completado").

Al terminar toda la migración, actualiza CLAUDE.md marcando la migración como completada
y documenta el nuevo flujo de arranque.
```
