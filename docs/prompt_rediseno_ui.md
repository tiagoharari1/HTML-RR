# Prompt: Rediseño completo de la UI — Run Rate B2B

> Pegá este prompt en una nueva sesión de Claude Code / Cowork con el proyecto abierto.

---

## Contexto

Quiero hacer un rediseño visual completo del frontend de la app **Run Rate B2B**
(`frontend/`). El stack es React 18 + Vite + TypeScript + Tailwind CSS v3 + Framer Motion + Recharts.

Tengo una skill instalada llamada **`web-design-landing`** en
`docs/skills/web-design-landing/SKILL.md` — leela antes de tocar cualquier archivo.
Contiene la paleta de colores, tokens CSS, componentes, variantes de animación
y un checklist de calidad. Seguila al pie de la letra.

---

## Referencias de diseño

### 1. Sitio de referencia visual: https://www.cielhomes.in/

Analizá este sitio y extraé los siguientes patrones para aplicarlos en la app:

- **Hero section**: titular con palabra clave en serif italic + subtítulo en gris claro + CTA grande redondeado + fila de stats (números grandes con etiquetas pequeñas en uppercase)
- **Tipografía dual**: sans-serif (Inter) para el cuerpo, serif italic (Playfair Display) en 1-2 palabras de cada título principal
- **Secciones**: separadas con mucho espacio vertical, cada una con un badge/label pequeño en uppercase que anuncia la categoría antes del título
- **Entradas en scroll**: cada sección entra con `fadeInUp` + `useInView` — no todo anima a la vez, solo cuando entra en el viewport
- **Navbar**: fijo, con `backdrop-blur` y borde inferior sutil
- **Footer**: fondo más oscuro que el body, columnas de navegación + tagline

### 2. Paleta de colores (imagen de referencia adjunta)

El dashboard financiero de referencia usa:
- Fondo azul marino muy oscuro (`#090D1A`)
- Texto blanco/gris claro
- Verde brillante para métricas positivas (`#00E676`)
- Rojo para negativas (`#FF5252`)
- Secciones elevadas en azul-gris oscuro (`#111827` / `#1A2235`)
- Acento secundario índigo/violeta (`#6C63FF`)
- Números siempre en `font-mono`

---

## Qué tenés que hacer (orden estricto)

### Paso 1 — Leer la skill
```
Lee docs/skills/web-design-landing/SKILL.md completo.
Luego lee CLAUDE.md para entender la estructura del proyecto.
```

### Paso 2 — Auditar el frontend actual
```
Lee todos los archivos en frontend/src/ y listá:
- Qué archivos de estilos/tokens existen hoy
- Qué componentes tienen estilos hardcodeados
- Qué colores/fuentes están siendo usados actualmente
Resumí el estado actual antes de tocar nada.
```

### Paso 3 — Aplicar tokens de diseño globales
Modificá o creá:

1. **`frontend/index.html`** — agregar las fuentes de Google Fonts (Inter, Playfair Display, JetBrains Mono) en el `<head>`
2. **`frontend/src/index.css`** — agregar todos los tokens CSS de la skill (`--bg-base`, `--accent`, `--text-primary`, etc.) dentro de `:root`
3. **`frontend/tailwind.config.ts`** — extender con los colores, familias tipográficas, sombras y gradientes de la skill
4. **`frontend/src/lib/motion.ts`** — crear el archivo con las variantes `fadeInUp`, `staggerContainer`, `scaleIn`
5. **`frontend/src/lib/chartTheme.ts`** — crear el archivo con `CHART_COLORS` y el wrapper `ChartContainer`

### Paso 4 — Rediseñar los componentes clave

Para cada componente, leé el archivo actual, entendé qué hace, y reescribí los estilos siguiendo la skill. **No cambies la lógica, solo el diseño.**

#### A. Layout principal / App shell
- `frontend/src/App.tsx` o el componente raíz
- Fondo global `bg-base`, fuente base Inter
- Navbar fija con blur siguiendo el patrón de la skill (sección 8)

#### B. Stepper del wizard
- El componente de pasos (buscar en `frontend/src/`)
- Aplicar el stepper de la skill (sección 5): dots con estado, connector line, etiquetas debajo
- Animar transición entre pasos con `AnimatePresence` de Framer Motion

#### C. Landing / pantalla inicial (paso 0 o home)
- Aplicar el patrón Hero de la skill (sección 3) con:
  - Fondo `bg-hero-mesh` (gradiente radial de la skill)
  - Badge de canal en la parte superior
  - H1 con palabra clave en `font-serif italic text-accent`
  - Fila de 3 stats con `font-mono text-3xl text-accent`
  - CTA con `hover:shadow-glow`
  - Animación `fadeInUp` con stagger entre elementos

#### D. Steps de upload (paso 1 y 2)
- Drop zone elegante siguiendo el patrón de la skill (sección 8)
- Card de archivo cargado: nombre, tamaño, checkmark en verde `text-pos`
- Animación `scaleIn` al confirmar el archivo

#### E. Step de configuración (paso 3)
- Inputs/selects con estilo oscuro: `bg-surface border border-[--border] rounded-xl`
- Focus state: `focus:border-accent focus:ring-1 focus:ring-accent/30`
- Labels en uppercase tracking-widest `text-[--text-secondary]`

#### F. Vista de resultados (paso 4)
- Grid de MetricCards usando el componente de la skill (sección 3)
  - net_revenue, bimo, revenue_margin con sus deltas en color semáforo
- Tabla del P&L con el diseño de la skill (sección 6):
  - Header sticky `bg-surface2`, filas con hover
  - Valores negativos en `text-neg`, positivos en `text-[--text-primary]`
  - Totales con fondo `bg-accent/5`
- Gráficos con `ChartContainer` y `CHART_COLORS` de la skill (sección 7):
  - AreaChart para net_revenue con gradiente de relleno
  - Tooltip con fondo `#1A2235`
- Botón de descarga Excel: `bg-accent text-black font-semibold rounded-full hover:shadow-glow`

### Paso 5 — Verificación final

Recorré el checklist completo de la sección 9 de la skill. Para cada ítem que no esté cumplido, arreglarlo antes de terminar.

Luego corré `npm run build` dentro de `frontend/` para confirmar que no hay errores de TypeScript ni de compilación.

---

## Restricciones importantes

- **No tocar** nada en `src/`, `config/`, `tests/`, `app.py`, ni el backend (`api/`, `run_api.py`)
- **No cambiar** la lógica de los componentes React, solo los estilos/clases
- **No agregar** dependencias nuevas que no estén ya en `package.json` — Framer Motion, Recharts, Tailwind y Axios ya están instalados
- **No usar** colores fuera de la paleta definida en la skill. Si necesitás una variación, usá opacidad (ej: `accent/20`)
- Si un componente tiene estilos en un archivo `.css` separado, migrarlos a clases Tailwind en el mismo `.tsx`

---

## Entregable esperado

Al terminar, mostrá:
1. Lista de archivos modificados con una línea de descripción de cada cambio
2. Captura o descripción de cómo quedó cada pantalla principal
3. Output de `npm run build` sin errores
