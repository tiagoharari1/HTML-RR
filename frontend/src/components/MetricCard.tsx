import { motion } from "framer-motion";
import { fadeInUp } from "../lib/motion";

interface MetricCardProps {
  label: string;
  value: number;
  prefix?: string;
  suffix?: string;
  /** Color del acento (default verde). Usar tokens de la paleta. */
  accent?: string;
  delta?: string;
  deltaType?: "pos" | "neg" | "neutral";
  subLabel?: string;
}

function formatNumber(n: number): string {
  if (Math.abs(n) >= 1_000_000) {
    return (
      (n / 1_000_000).toLocaleString("es-AR", { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + "M"
    );
  }
  if (Math.abs(n) >= 1_000) {
    return (
      (n / 1_000).toLocaleString("es-AR", { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + "K"
    );
  }
  return n.toLocaleString("es-AR", { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

export function MetricCard({
  label,
  value,
  prefix = "$",
  suffix = "",
  accent = "var(--accent)",
  delta,
  deltaType = "neutral",
  subLabel,
}: MetricCardProps) {
  const deltaColor = {
    pos: "text-pos",
    neg: "text-neg",
    neutral: "text-secondary",
  }[deltaType];

  return (
    <motion.div
      variants={fadeInUp}
      whileHover={{ y: -3 }}
      transition={{ type: "spring", stiffness: 400, damping: 26 }}
      className="relative bg-surface border border-[color:var(--border)] rounded-2xl p-5
                 shadow-card overflow-hidden transition-colors duration-200
                 hover:border-[color:var(--border-hover)] hover:bg-surface2"
    >
      {/* Barra de acento superior */}
      <span
        className="absolute top-0 left-0 right-0 h-px"
        style={{ background: `linear-gradient(90deg, transparent, ${accent}, transparent)` }}
      />

      <div className="flex items-start justify-between gap-2">
        <span className="text-[10px] uppercase tracking-widest text-secondary font-medium">
          {label}
        </span>
        {delta && <span className={`text-xs font-mono font-medium ${deltaColor}`}>{delta}</span>}
      </div>

      <div className="mt-3">
        <span className="font-mono text-2xl md:text-3xl font-medium text-primary leading-none">
          <span className="text-secondary text-xl">{prefix}</span>
          {formatNumber(value)}
          {suffix}
        </span>
      </div>

      {subLabel && <p className="mt-1.5 text-xs text-muted">{subLabel}</p>}
    </motion.div>
  );
}
