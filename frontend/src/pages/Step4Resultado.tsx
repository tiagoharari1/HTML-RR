import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { buildPnl, exportPnlUrl, exportEvolutionUrl } from "../api/client";
import { useWizard } from "../store/wizard";
import { MetricCard } from "../components/MetricCard";
import { RrVsBudgetChart } from "../components/RrVsBudgetChart";
import { PnlTable } from "../components/PnlTable";
import { PageHeader } from "../components/PageHeader";
import { Section } from "../components/Section";
import { staggerContainer } from "../lib/motion";

function Accordion({
  title,
  children,
  tone = "info",
  defaultOpen = false,
}: {
  title: string;
  children: React.ReactNode;
  tone?: "info" | "warn";
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const accent = tone === "warn" ? "text-warn" : "text-accent";
  return (
    <div className="border border-[color:var(--border)] rounded-2xl overflow-hidden bg-surface">
      <button
        className="w-full flex justify-between items-center px-5 py-3.5 text-sm font-medium text-primary hover:bg-surface2 transition-colors"
        onClick={() => setOpen(!open)}
      >
        <span className={accent}>{title}</span>
        <span className="text-muted text-xs">{open ? "▲" : "▼"}</span>
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-4 pt-1">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function Step4Resultado() {
  const { sessionId, pnlResult, setPnlResult, setStep } = useWizard();

  const mutation = useMutation({
    mutationFn: () => buildPnl(sessionId),
    onSuccess: (data) => setPnlResult(data),
  });

  // Preparar datos del gráfico: net_revenue por mes
  const chartData = pnlResult?.pnl
    ? (() => {
        const byMes: Record<number, number> = {};
        pnlResult.pnl.forEach((row) => {
          const mes = Number(row["numero_mes_proyectado"]);
          byMes[mes] = (byMes[mes] ?? 0) + Number(row["net_revenue"] ?? 0);
        });
        return Object.entries(byMes)
          .sort(([a], [b]) => Number(a) - Number(b))
          .map(([mes, rr]) => ({ mes: Number(mes), rr }));
      })()
    : [];

  return (
    <div className="flex flex-col">
      <PageHeader
        badge="Paso 4 · Output"
        titleLead="P&L"
        titleAccent="Proyectado"
        subtitle="Run rate calibrado con actuals y estacionalidad, listo para exportar a Excel."
        aside={
          <button
            className="px-5 py-2.5 text-sm font-medium text-secondary hover:text-primary transition-colors"
            onClick={() => setStep(2)}
          >
            ← Volver
          </button>
        }
      />

      {!pnlResult && (
        <div className="flex flex-col items-center gap-5 py-20 bg-surface rounded-2xl border border-[color:var(--border)] shadow-card">
          <p className="text-secondary text-sm">
            Ejecutá el cálculo para generar la proyección Run Rate.
          </p>
          <button
            className="px-8 py-3 rounded-full bg-accent text-base font-semibold text-sm
                       hover:shadow-glow transition-all duration-300 hover:scale-105 active:scale-95
                       disabled:opacity-50 disabled:hover:scale-100 flex items-center gap-2"
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
          >
            {mutation.isPending && (
              <div className="w-4 h-4 rounded-full border-2 border-base border-t-transparent animate-spin" />
            )}
            {mutation.isPending ? "Calculando P&L…" : "Ejecutar proyección"}
          </button>
          {mutation.isError && (
            <p className="text-neg text-sm">
              {(mutation.error as Error)?.message ?? "Error desconocido"}
            </p>
          )}
        </div>
      )}

      {pnlResult && (
        <div className="flex flex-col gap-10">
          {/* Metric cards */}
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-2 gap-4 lg:grid-cols-4"
          >
            <MetricCard label="Net Revenue" value={pnlResult.totales.net_revenue} accent="var(--accent)" />
            <MetricCard label="NPV" value={pnlResult.totales.npv} accent="var(--accent2)" />
            <MetricCard label="BIMO" value={pnlResult.totales.bimo} accent="var(--warning)" />
            <MetricCard
              label="Revenue Margin"
              value={pnlResult.totales.revenue_margin}
              accent="var(--positive)"
            />
          </motion.div>

          {/* Chart */}
          <Section className="bg-surface rounded-2xl border border-[color:var(--border)] p-6 shadow-card">
            <h3 className="font-sans text-lg font-semibold text-primary mb-1">
              Net Revenue · <span className="font-serif italic text-accent">mensual</span>
            </h3>
            <p className="text-xs text-secondary mb-5">Run rate proyectado por mes</p>
            <RrVsBudgetChart data={chartData} />
          </Section>

          {/* Accordions */}
          {(pnlResult.info_calibracion?.length > 0 ||
            pnlResult.warnings_continuidad?.length > 0) && (
            <Section className="flex flex-col gap-3">
              {pnlResult.info_calibracion?.length > 0 && (
                <Accordion
                  title={`Calibración aplicada (${pnlResult.info_calibracion.length})`}
                  defaultOpen
                >
                  <ul className="text-xs text-secondary space-y-1 list-disc list-inside">
                    {pnlResult.info_calibracion.map((msg, i) => (
                      <li key={i}>{msg}</li>
                    ))}
                  </ul>
                </Accordion>
              )}
              {pnlResult.warnings_continuidad?.length > 0 && (
                <Accordion
                  title={`Avisos de continuidad (${pnlResult.warnings_continuidad.length})`}
                  tone="warn"
                >
                  <ul className="text-xs text-warn space-y-1 list-disc list-inside">
                    {pnlResult.warnings_continuidad.map((msg, i) => (
                      <li key={i}>{msg}</li>
                    ))}
                  </ul>
                </Accordion>
              )}
            </Section>
          )}

          {/* P&L Table */}
          <Section>
            <h3 className="font-sans text-lg font-semibold text-primary mb-4">
              P&L <span className="font-serif italic text-accent">Proyectado</span>{" "}
              <span className="text-secondary text-sm font-normal font-sans">· totales por mes</span>
            </h3>
            <PnlTable rows={pnlResult.pnl} />
          </Section>

          {/* Export buttons */}
          <Section className="flex flex-wrap gap-3 items-center">
            <a
              href={exportPnlUrl(sessionId)}
              download="pnl.xlsx"
              className="flex items-center gap-2 bg-accent text-base px-6 py-3 rounded-full text-sm font-semibold
                         hover:shadow-glow transition-all duration-300 hover:scale-105 active:scale-95"
            >
              Descargar P&L (.xlsx)
            </a>
            <a
              href={exportEvolutionUrl(sessionId)}
              download="pnl_evolution.xlsx"
              className="flex items-center gap-2 bg-surface2 border border-[color:var(--border)] text-primary px-6 py-3 rounded-full text-sm font-medium
                         hover:border-[color:var(--border-hover)] transition-all duration-200"
            >
              Descargar Evolution (.xlsx)
            </a>
            <button
              className="ml-auto text-sm text-secondary hover:text-primary underline transition-colors"
              onClick={() => mutation.mutate()}
              disabled={mutation.isPending}
            >
              Recalcular
            </button>
          </Section>
        </div>
      )}
    </div>
  );
}
