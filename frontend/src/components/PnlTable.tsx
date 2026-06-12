import { useMemo } from "react";
import { clsx } from "clsx";

// Grupos de columnas → mismo esquema que el export Excel
const SUBTOTALES = new Set(["net_revenue", "npv", "bimo", "revenue_margin"]);
const METRICAS_ORDEN = [
  "orders", "gross_bookings",
  "up_front_incentives", "fees", "commercial_discounts",
  "cost_of_installments", "credit_card_processing", "affiliates",
  "other_incentives", "errors", "revenue_tax", "other_transactional_taxes",
  "cancellations", "breakage_revenue", "customer_claims", "customer_service",
  "media_revenue", "frauds", "efecto_financiero", "dif_fx", "currency_hedge",
  "vendor_commissions", "intercompany", "white_labels_api", "operations",
  "back_end_incentives", "income_from_outsourced_services",
  "net_revenue", "npv", "bimo", "revenue_margin",
];

const MESES_ES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"];

function fmt(v: unknown): string {
  if (v == null || v === "") return "—";
  const n = Number(v);
  if (isNaN(n)) return String(v);
  return n.toLocaleString("es-AR", { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function prettyLabel(col: string): string {
  return col.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

interface PnlTableProps {
  rows: Record<string, unknown>[];
}

export function PnlTable({ rows }: PnlTableProps) {
  // Agrupar por numero_mes_proyectado → columnas
  const meses = useMemo(() => {
    const set = new Set<number>();
    rows.forEach((r) => set.add(Number(r["numero_mes_proyectado"])));
    return [...set].sort((a, b) => a - b);
  }, [rows]);

  // Mes calendario del primer mes proyectado (para etiquetas)
  const mesPivot = useMemo(() => {
    const v = rows[0]?.["mes_pivot"];
    return v != null ? Number(v) : null;
  }, [rows]);

  // Calcular totales por metrica × mes
  const totals = useMemo(() => {
    const map: Record<string, Record<number, number>> = {};
    rows.forEach((r) => {
      const mes = Number(r["numero_mes_proyectado"]);
      METRICAS_ORDEN.forEach((col) => {
        if (!(col in r)) return;
        if (!map[col]) map[col] = {};
        map[col][mes] = (map[col][mes] ?? 0) + Number(r[col] ?? 0);
      });
    });
    return map;
  }, [rows]);

  if (!rows.length) return null;

  const colLabel = (m: number) => {
    if (mesPivot == null) return `Mes ${m}`;
    return MESES_ES[(mesPivot - 1 + m - 1) % 12];
  };

  return (
    <div className="overflow-x-auto rounded-2xl border border-[color:var(--border)] shadow-card">
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr className="bg-surface2">
            <th className="sticky left-0 z-10 bg-surface2 text-left px-4 py-3 font-medium text-secondary uppercase tracking-widest text-[10px] whitespace-nowrap min-w-[200px] border-b border-[color:var(--border)]">
              Línea P&amp;L
            </th>
            {meses.map((m) => (
              <th
                key={m}
                className="px-4 py-3 font-medium text-right text-secondary uppercase tracking-widest text-[10px] whitespace-nowrap border-b border-[color:var(--border)]"
              >
                {colLabel(m)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {METRICAS_ORDEN.filter((col) => col in totals).map((col) => {
            const isSubtotal = SUBTOTALES.has(col);
            return (
              <tr
                key={col}
                className={clsx(
                  "border-b border-[color:var(--border)] transition-colors group",
                  isSubtotal ? "bg-accent/5 font-semibold" : "hover:bg-surface2"
                )}
              >
                <td
                  className={clsx(
                    "sticky left-0 z-10 px-4 py-2.5 whitespace-nowrap transition-colors",
                    isSubtotal
                      ? "bg-[color:var(--bg-surface-2)] text-accent"
                      : "bg-surface text-primary group-hover:bg-surface2"
                  )}
                >
                  {prettyLabel(col)}
                </td>
                {meses.map((m) => {
                  const v = totals[col]?.[m] ?? 0;
                  return (
                    <td
                      key={m}
                      className={clsx(
                        "px-4 py-2.5 text-right font-mono tabular-nums",
                        v < 0 ? "text-neg" : v > 0 ? "text-primary" : "text-muted"
                      )}
                    >
                      {fmt(v)}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
