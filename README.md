# RR AI — Run Rate B2B/HTML

Aplicación web en Python (Streamlit) que emula la lógica del modelo Excel de
Run Rate del canal HTML/B2B. Permite al usuario cargar Base 2026 y Contable,
configurar mes pivot y horizonte, y obtener un P&L proyectado descargable
en Excel.

## Setup rápido

```bash
# 1. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate          # macOS / Linux
.venv\Scripts\activate             # Windows

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Correr la app
streamlit run app.py
```

La app abre en `http://localhost:8501`.

## Estructura del proyecto

```
RR AI/
├── app.py                  Entry point Streamlit
├── requirements.txt
├── config/                 Constantes y configuración
├── data/
│   ├── precargado/         Hojas fijas (Macro, Estacionalidades)
│   └── ejemplos/           Archivos de muestra para testing
├── src/
│   ├── io/                 Lectura y validación de inputs
│   ├── logica/             Lógica de proyección financiera
│   ├── ui/                 Componentes Streamlit
│   └── export/             Generación de Excel descargable
├── tests/
└── docs/                   Notas de lógica financiera
```

## Flujo del wizard

1. **Upload Base 2026** — datos transaccionales MTD
2. **Upload Contable** — referencia contable por línea P&L
3. **Configuración** — mes pivot + horizonte de meses a proyectar
4. **Resultado** — preview con filtros + gráficos + descarga Excel

## Lógica financiera (resumen)

- **Orders** y **gross_bookings** se proyectan aplicando los índices de las
  hojas pre-cargadas de Estacionalidad (orders y ASP).
- **Líneas transaccionales** (`fees`, `commercial_discounts`,
  `up_front_incentives`, `cost_of_installments`, etc.) se proyectan como
  ratio observado en Base 2026 (MTD) aplicado sobre el gross_bookings /
  orders proyectado.
- **Líneas no transaccionales** (`vendor_commissions`, `intercompany`,
  `white_labels_api`, `operations`, `back_end_incentives`,
  `income_from_outsourced_services`) se toman directo de la hoja Contable.
- **FX y CPI** de Macro se aplican a todas las líneas según país y mes
  proyectado.

Ver `docs/notas_logica_financiera.md` para el detalle.

## Estado actual

Módulo 1 completado: estructura base lista para desarrollo incremental.
