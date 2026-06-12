---
name: web-design-landing
description: >
  Skill de diseño web para landing pages y dashboards de aplicaciones. Úsala cuando
  el usuario quiera mejorar el diseño visual de su app (colores, tipografía, layout,
  animaciones, componentes). Aplicable al stack React + Vite + TypeScript + Tailwind CSS v3
  + Framer Motion del proyecto RR AI, pero los principios son universales.
  Triggers: "mejorar el diseño", "landing page", "UI", "look and feel", "colores",
  "tipografía", "animaciones", "componentes visuales", "dashboard", "estilo".
---

# Skill: Diseño Web para Landing Pages y Dashboards

## Contexto de este proyecto

Stack: **React 18 + Vite + TypeScript + Tailwind CSS v3 + Framer Motion + Recharts**.
Todas las referencias de código en esta skill usan este stack.

---

## 1. Paleta de colores de referencia

### Tokens CSS (agregar en `frontend/src/index.css`)

La imagen de referencia del usuario muestra un **dark dashboard financiero**:
fondo azul-marino oscuro, texto blanco/gris claro, verde brillante para métricas
positivas, rojo/naranja para negativas, y secciones en púrpura/índigo oscuro.

La web de referencia (cielhomes.in) usa **lujo minimalista**:
alto contraste, tipografía serif en titulares, mucho espacio blanco, secciones
claramente delimitadas.

La combinación para el proyecto es: **dark luxury data dashboard**.

```css
/* frontend/src/index.css — agregar dentro de @layer base */
:root {
  /* Fondos */
  --bg-base:          #090D1A;   /* azul-marino muy oscuro */
  --bg-surface:       #111827;   /* superficie de cards */
  --bg-surface-2:     #1A2235;   /* superficie elevada / hover */
  --bg-glass:         rgba(255,255,255,0.04);

  /* Acento principal */
  --accent:           #00E5A0;   /* verde esmeralda — KPIs positivos */
  --accent-dim:       rgba(0,229,160,0.15);

  /* Acento secundario */
  --accent2:          #6C63FF;   /* índigo/violeta — gráficos, badges */
  --accent2-dim:      rgba(108,99,255,0.15);

  /* Semáforo */
  --positive:         #00E676;   /* verde — crecimiento */
  --negative:         #FF5252;   /* rojo — caída */
  --warning:          #FFD740;   /* amarillo — warning */
  --neutral:          #90A4AE;   /* gris azulado — sin cambio */

  /* Texto */
  --text-primary:     #F0F4FF;
  --text-secondary:   #8E9BB5;
  --text-muted:       #4A5568;

  /* Bordes */
  --border:           rgba(255,255,255,0.08);
  --border-hover:     rgba(255,255,255,0.16);

  /* Sombras */
  --shadow-card:      0 4px 24px rgba(0,0,0,0.4);
  --shadow-glow:      0 0 24px rgba(0,229,160,0.2);
}
```

### Extensión de Tailwind (`frontend/tailwind.config.ts`)

```ts
import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        base:     'var(--bg-base)',
        surface:  'var(--bg-surface)',
        surface2: 'var(--bg-surface-2)',
        accent:   'var(--accent)',
        accent2:  'var(--accent2)',
        pos:      'var(--positive)',
        neg:      'var(--negative)',
        warn:     'var(--warning)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        serif: ['"Playfair Display"', 'Georgia', 'serif'],   // titulares elegantes
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        card:  'var(--shadow-card)',
        glow:  'var(--shadow-glow)',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'hero-mesh': `
          radial-gradient(ellipse at 20% 50%, rgba(108,99,255,0.15) 0%, transparent 60%),
          radial-gradient(ellipse at 80% 20%, rgba(0,229,160,0.1) 0%, transparent 50%)
        `,
      },
    },
  },
  plugins: [],
}
export default config
```

---

## 2. Tipografía

### Fuentes a usar

Agregar en el `<head>` del `frontend/index.html`:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,600;1,600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

### Jerarquía tipográfica

| Uso                         | Clase Tailwind                               | Ejemplo                        |
|-----------------------------|----------------------------------------------|--------------------------------|
| H1 hero                     | `font-serif text-5xl italic text-white`      | *Run Rate* B2B                 |
| H2 sección                  | `font-serif text-3xl font-semibold`          | Resultado del P&L              |
| H3 card / métrica           | `font-sans text-xl font-semibold`            | Net Revenue                    |
| Valor numérico grande        | `font-mono text-3xl font-medium text-accent` | $22.2M                         |
| Etiqueta / label            | `font-sans text-xs font-medium tracking-widest uppercase text-[--text-secondary]` | GB [M] |
| Cuerpo / descripción        | `font-sans text-sm text-[--text-secondary]`  | Datos MTD al 15 de mayo       |
| Delta / variación           | `font-mono text-xs font-medium`              | +15% / -4%                     |

**Regla clave** (referencia cielhomes.in): usar `font-serif italic` solo en 1-2
palabras clave del título para crear énfasis elegante. Ejemplo:
```tsx
<h1 className="font-sans text-4xl font-light text-white">
  Run Rate <em className="font-serif italic text-accent not-italic">B2B</em>
</h1>
```

---

## 3. Estructura de layout

### Hero de la landing / paso 0 del wizard

```tsx
// Patrón: fondo oscuro + malla de gradientes + stat highlights

<section className="relative min-h-screen bg-base overflow-hidden">
  {/* Fondo mesh */}
  <div className="absolute inset-0 bg-hero-mesh pointer-events-none" />

  {/* Contenido centrado */}
  <div className="relative z-10 max-w-5xl mx-auto px-6 py-24 flex flex-col items-center text-center gap-8">

    {/* Badge */}
    <span className="px-3 py-1 rounded-full border border-accent/30 bg-accent/10
                     text-accent text-xs font-medium tracking-widest uppercase">
      HTML · B2B · Canal
    </span>

    {/* Titular */}
    <h1 className="text-5xl md:text-6xl font-sans font-light text-white leading-tight">
      Modelo{' '}
      <span className="font-serif italic text-accent">Run Rate</span>
    </h1>

    {/* Subtítulo */}
    <p className="text-lg text-[--text-secondary] max-w-xl">
      Proyección inteligente del P&L con estacionalidad, actuals calibrados
      y export a Excel en segundos.
    </p>

    {/* CTA */}
    <button className="px-8 py-3 rounded-full bg-accent text-base font-semibold
                       text-black hover:shadow-glow transition-all duration-300
                       hover:scale-105 active:scale-95">
      Iniciar modelo →
    </button>

    {/* Stats row */}
    <div className="grid grid-cols-3 gap-8 mt-12 pt-12 border-t border-[--border] w-full">
      {[
        { label: 'Países', value: '10+' },
        { label: 'Líneas P&L', value: '20+' },
        { label: 'Meses proyectados', value: '24' },
      ].map(s => (
        <div key={s.label} className="flex flex-col gap-1">
          <span className="font-mono text-3xl font-medium text-accent">{s.value}</span>
          <span className="text-xs uppercase tracking-widest text-[--text-secondary]">{s.label}</span>
        </div>
      ))}
    </div>
  </div>
</section>
```

### Card de métricas (estilo imagen de referencia)

```tsx
interface MetricCardProps {
  label: string
  value: string | number
  delta?: string        // ej: "+15%"
  deltaType?: 'pos' | 'neg' | 'neutral'
  subLabel?: string
}

export function MetricCard({ label, value, delta, deltaType = 'neutral', subLabel }: MetricCardProps) {
  const deltaColor = {
    pos: 'text-pos',
    neg: 'text-neg',
    neutral: 'text-[--text-secondary]',
  }[deltaType]

  return (
    <div className="bg-surface border border-[--border] rounded-2xl p-5
                    hover:border-[--border-hover] hover:bg-surface2
                    transition-all duration-200 shadow-card">
      <div className="flex items-start justify-between gap-2">
        <span className="text-xs uppercase tracking-widest text-[--text-secondary] font-medium">
          {label}
        </span>
        {delta && (
          <span className={`text-xs font-mono font-medium ${deltaColor}`}>
            {delta}
          </span>
        )}
      </div>
      <div className="mt-3">
        <span className="font-mono text-2xl font-medium text-white">{value}</span>
      </div>
      {subLabel && (
        <p className="mt-1 text-xs text-[--text-muted]">{subLabel}</p>
      )}
    </div>
  )
}
```

---

## 4. Animaciones con Framer Motion

### Principios (basados en cielhomes.in)

- Entradas suaves: `fadeInUp` con 0.4–0.6s, stagger entre elementos
- No sobrecargar: máx 1 animación por región visible
- Reducir para `prefers-reduced-motion`

### Variantes reutilizables

```ts
// frontend/src/lib/motion.ts
export const fadeInUp = {
  hidden:  { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } },
}

export const staggerContainer = {
  hidden:  {},
  visible: { transition: { staggerChildren: 0.08 } },
}

export const scaleIn = {
  hidden:  { opacity: 0, scale: 0.95 },
  visible: { opacity: 1, scale: 1, transition: { duration: 0.4 } },
}
```

### Uso en componentes

```tsx
import { motion } from 'framer-motion'
import { fadeInUp, staggerContainer } from '@/lib/motion'

// Grid de cards con stagger
<motion.div
  variants={staggerContainer}
  initial="hidden"
  animate="visible"
  className="grid grid-cols-2 md:grid-cols-4 gap-4"
>
  {metrics.map(m => (
    <motion.div key={m.label} variants={fadeInUp}>
      <MetricCard {...m} />
    </motion.div>
  ))}
</motion.div>
```

---

## 5. Stepper / Wizard

### Diseño del stepper (pasos del wizard)

```tsx
// Stepper horizontal minimal — top of page
interface StepperProps {
  steps: string[]
  current: number
}

export function Stepper({ steps, current }: StepperProps) {
  return (
    <div className="flex items-center gap-0 w-full max-w-2xl mx-auto">
      {steps.map((step, i) => (
        <React.Fragment key={step}>
          {/* Step dot */}
          <div className="flex flex-col items-center gap-1.5 flex-shrink-0">
            <div className={`
              w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold
              transition-all duration-300
              ${i < current  ? 'bg-accent text-black'               : ''}
              ${i === current ? 'bg-accent text-black ring-2 ring-accent/30 ring-offset-2 ring-offset-base' : ''}
              ${i > current  ? 'bg-surface border border-[--border] text-[--text-secondary]' : ''}
            `}>
              {i < current ? '✓' : i + 1}
            </div>
            <span className={`text-xs whitespace-nowrap
              ${i === current ? 'text-accent font-medium' : 'text-[--text-muted]'}`}>
              {step}
            </span>
          </div>

          {/* Connector */}
          {i < steps.length - 1 && (
            <div className={`flex-1 h-px mx-2 mb-5 transition-all duration-500
              ${i < current ? 'bg-accent/60' : 'bg-[--border]'}`} />
          )}
        </React.Fragment>
      ))}
    </div>
  )
}
```

---

## 6. Tabla del P&L (Step 4 - resultados)

### Diseño de tabla financiera estilo dashboard

```tsx
// Cabecera sticky, filas alternadas, deltas con color semáforo

<div className="overflow-x-auto rounded-2xl border border-[--border]">
  <table className="w-full text-sm">
    <thead>
      <tr className="border-b border-[--border] bg-surface2">
        <th className="text-left px-4 py-3 text-xs uppercase tracking-widest text-[--text-secondary] font-medium sticky left-0 bg-surface2">
          Línea
        </th>
        {meses.map(m => (
          <th key={m} className="text-right px-4 py-3 text-xs uppercase tracking-widest text-[--text-secondary] font-medium">
            {m}
          </th>
        ))}
      </tr>
    </thead>
    <tbody>
      {filas.map((fila, i) => (
        <tr key={fila.nombre}
            className={`border-b border-[--border]/50 transition-colors
              hover:bg-surface2
              ${fila.esTotal ? 'bg-accent/5 font-semibold' : ''}`}>
          <td className="px-4 py-2.5 text-[--text-primary] sticky left-0 bg-inherit">
            {fila.nombre}
          </td>
          {fila.valores.map((v, j) => (
            <td key={j} className={`px-4 py-2.5 text-right font-mono
              ${v < 0 ? 'text-neg' : v > 0 ? 'text-[--text-primary]' : 'text-[--text-muted]'}`}>
              {formatM(v)}
            </td>
          ))}
        </tr>
      ))}
    </tbody>
  </table>
</div>
```

---

## 7. Gráficos con Recharts

### Tema oscuro para todos los gráficos

```tsx
// frontend/src/lib/chartTheme.ts
export const CHART_COLORS = {
  primary:   '#00E5A0',
  secondary: '#6C63FF',
  tertiary:  '#FFD740',
  negative:  '#FF5252',
  grid:      'rgba(255,255,255,0.06)',
  axis:      '#4A5568',
  tooltip_bg: '#1A2235',
}

// Wrapper para recharts responsivo
export function ChartContainer({ children, height = 280 }: { children: React.ReactNode, height?: number }) {
  return (
    <div className="bg-surface border border-[--border] rounded-2xl p-4">
      <ResponsiveContainer width="100%" height={height}>
        {children}
      </ResponsiveContainer>
    </div>
  )
}
```

### AreaChart para net_revenue / bimo

```tsx
import { AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts'
import { CHART_COLORS, ChartContainer } from '@/lib/chartTheme'

<ChartContainer height={240}>
  <AreaChart data={data}>
    <defs>
      <linearGradient id="gradAccent" x1="0" y1="0" x2="0" y2="1">
        <stop offset="5%"  stopColor={CHART_COLORS.primary} stopOpacity={0.3} />
        <stop offset="95%" stopColor={CHART_COLORS.primary} stopOpacity={0} />
      </linearGradient>
    </defs>
    <CartesianGrid stroke={CHART_COLORS.grid} vertical={false} />
    <XAxis dataKey="mes" tick={{ fill: CHART_COLORS.axis, fontSize: 11 }} axisLine={false} tickLine={false} />
    <YAxis tick={{ fill: CHART_COLORS.axis, fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `$${v}M`} />
    <Tooltip
      contentStyle={{ background: CHART_COLORS.tooltip_bg, border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12 }}
      labelStyle={{ color: '#F0F4FF', fontWeight: 600 }}
      itemStyle={{ color: CHART_COLORS.primary }}
    />
    <Area type="monotone" dataKey="net_revenue" stroke={CHART_COLORS.primary}
          strokeWidth={2} fill="url(#gradAccent)" dot={false} />
  </AreaChart>
</ChartContainer>
```

---

## 8. Patrones de UX claves (cielhomes.in)

### Secciones con revelación en scroll

```tsx
// Patrón de cielhomes.in: cada sección entra desde abajo al hacer scroll
import { useInView } from 'framer-motion'
import { useRef } from 'react'

function Section({ children, className }: { children: React.ReactNode, className?: string }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-80px' })

  return (
    <motion.section
      ref={ref}
      initial={{ opacity: 0, y: 40 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {children}
    </motion.section>
  )
}
```

### Navbar sticky con blur

```tsx
<nav className="fixed top-0 left-0 right-0 z-50
                bg-base/80 backdrop-blur-xl border-b border-[--border]
                transition-all duration-300">
  <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
    <span className="font-serif italic text-accent text-xl">Run Rate</span>
    {/* steps indicator aquí */}
  </div>
</nav>
```

### Feedback visual de upload (Step 1 y 2)

```tsx
// Drop zone elegante
<div className={`
  border-2 border-dashed rounded-2xl p-12 text-center
  transition-all duration-200 cursor-pointer
  ${isDragging
    ? 'border-accent bg-accent/10 scale-[1.02]'
    : 'border-[--border] hover:border-accent/40 hover:bg-surface2'
  }
`}>
  <div className="text-4xl mb-3">📊</div>
  <p className="font-semibold text-white">Arrastrá el archivo aquí</p>
  <p className="text-sm text-[--text-secondary] mt-1">o hacé click para seleccionar · .xlsx</p>
</div>
```

---

## 9. Checklist de diseño para aplicar

Cuando el usuario pida mejorar una pantalla, verificar:

- [ ] **Fondo**: `bg-base` (#090D1A) como base global
- [ ] **Superficies**: cards con `bg-surface` + `border border-[--border]` + `rounded-2xl`
- [ ] **Tipografía**: `font-serif italic` en 1-2 palabras del título principal
- [ ] **Valores numéricos**: `font-mono` siempre, color semáforo (pos/neg/neutral)
- [ ] **Espaciado**: padding generoso (`p-6`/`p-8`), gaps de al menos `gap-4`
- [ ] **Animaciones**: `fadeInUp` en secciones, `staggerChildren` en listas/grids
- [ ] **Gráficos**: fondo `bg-surface`, sin ejes recargados, tooltip custom oscuro
- [ ] **Gradiente hero**: `bg-hero-mesh` en la pantalla principal
- [ ] **Hover states**: `hover:bg-surface2` + `transition-all duration-200`
- [ ] **Responsive**: grid `grid-cols-1 md:grid-cols-2 lg:grid-cols-4`

---

## 10. Recursos y repositorios de referencia

### GitHub — templates y sistemas de diseño

| Repositorio | Por qué es útil |
|---|---|
| [cruip/tailwind-landing-page-template](https://github.com/cruip/tailwind-landing-page-template) | React + Tailwind, clean dark landing |
| [tailwindtoolbox/Rainblur-Landing-Page](https://github.com/tailwindtoolbox/Rainblur-Landing-Page) | Dark mode + gradients, minimalista |
| [shadcn/ui](https://github.com/shadcn-ui/ui) | Componentes accesibles, theming con CSS vars |
| [tremor](https://github.com/tremorlabs/tremor) | Componentes de dashboard financiero en React |
| [nextjs-subscription-payments](https://github.com/vercel/nextjs-subscription-payments) | Patrón de landing SaaS profesional |

### Inspiración visual (dark dashboard financiero)

- [Muzli Best Dashboards 2026](https://muz.li/blog/best-dashboard-design-examples-inspirations-for-2026/) — colección curada de dashboards
- [Colorlib Dark Admin Templates](https://colorlib.com/wp/dark-admin-dashboard-templates/) — templates oscuros
- [Dribbble Dark Themes](https://dribbble.com/erikdkennedy/collections/160688-Dark-themes) — exploración visual

### Herramientas de color

- **Coolors**: https://coolors.co — generar paletas
- **Realtime Colors**: https://www.realtimecolors.com — previsualizar paletas en UI real
- **UI Colors**: https://uicolors.app — generar escala Tailwind desde un hex

### Fuentes

- **Inter** (sans): https://fonts.google.com/specimen/Inter
- **Playfair Display** (serif italic titulares): https://fonts.google.com/specimen/Playfair+Display
- **JetBrains Mono** (números): https://fonts.google.com/specimen/JetBrains+Mono

---

## 11. Cómo usar esta skill

Cuando el usuario pida mejorar el diseño:

1. **Identificar qué pantalla/componente** quiere mejorar (landing, step 1, step 4, tabla P&L, gráficos).
2. **Leer el archivo existente** (`frontend/src/`) para entender qué está implementado.
3. **Aplicar los tokens de color** primero (paso rápido, mayor impacto visual).
4. **Mejorar tipografía**: identificar titulares que merezcan el tratamiento serif italic.
5. **Agregar animaciones** con los variants predefinidos — no inventar nuevas.
6. **Chequear la lista** de la sección 9 antes de entregar.
7. **Preguntar al usuario** si prefiere que el cambio sea solo en un componente o en toda la app.

No inventar tokens de color fuera de la paleta definida. Toda variación de color
debe ser una opacidad de los existentes (ej: `accent/20`, `accent/5`).
