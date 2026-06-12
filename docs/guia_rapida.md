# Guía rápida — RR AI

## Cómo abrir la app

Necesitás dos terminales abiertas en la carpeta del proyecto.

### Terminal 1 — Backend

```powershell
.venv\Scripts\Activate.ps1
python run_api.py
```

Queda escuchando en **http://localhost:8000**
Documentación interactiva de la API: **http://localhost:8000/docs**

### Terminal 2 — Frontend

```powershell
cd frontend
npm run dev
```

La UI queda en **http://localhost:5173**

> También podés correr la versión Streamlit (v1) con `streamlit run app.py` → http://localhost:8501

---

## Estructura del proyecto

```
RR AI/
│
├── run_api.py               Arranca el servidor FastAPI (Uvicorn)
├── app.py                   Entry point Streamlit (v1, sigue disponible)
│
├── api/                     Backend HTTP
│   ├── main.py              App FastAPI, CORS, montaje de routers
│   ├── models.py            Schemas Pydantic (request / response)
│   ├── session.py           Estado de sesión en memoria (archivos subidos + config)
│   └── routes/
│       ├── upload.py        POST /upload/base, /upload/contable
│       ├── config.py        POST /config  (mes pivot, horizonte, día corte)
│       ├── build.py         POST /build   (dispara el cálculo del P&L)
│       ├── data.py          GET  /data    (devuelve el P&L como JSON)
│       └── export.py        GET  /export  (descarga el .xlsx)
│
├── frontend/                UI React + Vite + TypeScript
│   └── src/
│       ├── App.tsx          Router principal (4 pasos del wizard)
│       ├── store/wizard.ts  Estado global con Zustand (paso actual, sesión, config)
│       ├── api/client.ts    Axios + TanStack Query (llamadas al backend)
│       ├── components/      Piezas reutilizables (Stepper, Dropzone, tabla P&L, gráfico)
│       └── pages/
│           ├── Step1UploadBase.tsx      Subir Base 2026
│           ├── Step2UploadContable.tsx  Subir Contable (opcional)
│           ├── Step3Config.tsx          Mes pivot, horizonte, día de corte
│           └── Step4Resultado.tsx       Vista previa P&L + descarga Excel
│
├── src/                     Lógica financiera (Python puro, sin web)
│   ├── io/
│   │   ├── readers.py       Lee Base 2026, Contable, pre-cargados
│   │   └── validators.py    Valida columnas, tipos, dominios
│   └── logica/
│       ├── proyeccion_orders.py   Orders × estacionalidad
│       ├── proyeccion_asp.py      ASP × estacionalidad
│       ├── proyeccion_gb.py       gross_bookings = orders × ASP
│       ├── lineas_transaccionales.py  Ratios sobre GB (Base 2026)
│       ├── lineas_contables.py    Ratios históricos (Base 2025)
│       ├── calibracion.py         Ancla a actuals reales + blend con budget
│       ├── mapeo_canal.py         B2B → HTML
│       └── pnl_builder.py         Ensambla el DataFrame P&L final
│
├── config/settings.py       Constantes centralizadas (mapeos, columnas, paths)
├── data/
│   ├── precargado/          Macro, Estacionalidades, Base 2025 (fijos)
│   └── ejemplos/            Archivos de prueba
└── tests/                   pytest
```

---

## Flujo de datos (de punta a punta)

```
Usuario sube Base 2026 (Excel)
        ↓
  api/routes/upload.py  →  src/io/readers.py + validators.py
        ↓
Usuario configura (mes pivot, horizonte, día corte)
        ↓
  api/routes/build.py  →  src/logica/pnl_builder.py
                              ├── calibracion (ancla a actuals)
                              ├── proyeccion orders / ASP / GB
                              ├── líneas transaccionales (ratios Base 2026)
                              ├── líneas históricas (ratios Base 2025)
                              └── mapeo canal + ensamblado DataFrame
        ↓
  api/routes/data.py   →  P&L como JSON  →  frontend Step4 (tabla + gráficos)
  api/routes/export.py →  P&L como .xlsx →  descarga del usuario
```
