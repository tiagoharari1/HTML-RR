/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        base: "var(--bg-base)",
        surface: "var(--bg-surface)",
        surface2: "var(--bg-surface-2)",
        accent: "var(--accent)",
        accent2: "var(--accent2)",
        pos: "var(--positive)",
        neg: "var(--negative)",
        warn: "var(--warning)",
        neutral: "var(--neutral)",
        // Legacy alias para no romper referencias residuales
        brand: {
          DEFAULT: "var(--accent)",
          dark: "var(--accent)",
          darker: "var(--accent)",
        },
      },
      textColor: {
        primary: "var(--text-primary)",
        secondary: "var(--text-secondary)",
        muted: "var(--text-muted)",
      },
      borderColor: {
        DEFAULT: "var(--border)",
        hover: "var(--border-hover)",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        serif: ['"Playfair Display"', "Georgia", "serif"],
        mono: ['"JetBrains Mono"', "monospace"],
      },
      boxShadow: {
        card: "var(--shadow-card)",
        glow: "var(--shadow-glow)",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "hero-mesh": `
          radial-gradient(ellipse at 20% 30%, rgba(108,99,255,0.16) 0%, transparent 55%),
          radial-gradient(ellipse at 85% 15%, rgba(0,229,160,0.12) 0%, transparent 50%),
          radial-gradient(ellipse at 60% 90%, rgba(108,99,255,0.08) 0%, transparent 55%)
        `,
      },
    },
  },
  plugins: [],
}
