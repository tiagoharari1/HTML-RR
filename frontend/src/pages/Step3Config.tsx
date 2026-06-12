import { useMutation } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { setConfig as apiSetConfig } from "../api/client";
import { PageHeader } from "../components/PageHeader";
import { useWizard } from "../store/wizard";
import { fadeInUp, staggerContainer } from "../lib/motion";

const MESES_ES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

function mesFinHorizonte(pivot: number, horizonte: number): string {
  const idx = (pivot - 1 + horizonte - 1) % 12;
  return MESES_ES[idx];
}

const inputClass =
  "w-full bg-surface border border-[color:var(--border)] rounded-xl px-4 py-3 text-sm text-primary " +
  "placeholder:text-muted focus:outline-none focus:border-accent/60 focus:ring-2 focus:ring-accent/20 transition-all";

const labelClass = "text-[10px] font-medium uppercase tracking-widest text-secondary";

export function Step3Config() {
  const { sessionId, config, setConfig, setStep } = useWizard();

  const mutation = useMutation({
    mutationFn: () =>
      apiSetConfig({
        session_id: sessionId,
        mes_pivot: config.mesPivot,
        horizonte: config.horizonte,
        dia_corte: config.diaCorte,
        escenario: config.escenario || null,
      }),
  });

  async function handleSubmit() {
    await mutation.mutateAsync();
    setStep(3);
  }

  return (
    <div className="flex flex-col">
      <PageHeader
        badge="Paso 3 · Parámetros"
        titleLead="Configurá la"
        titleAccent="Proyección"
        subtitle="Definí el mes pivot, el horizonte y el día de corte MTD para calibrar el run rate."
      />

      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="max-w-xl bg-surface border border-[color:var(--border)] rounded-2xl p-6 md:p-8 shadow-card flex flex-col gap-6"
      >
        {/* Mes Pivot */}
        <motion.div variants={fadeInUp} className="flex flex-col gap-2">
          <label className={labelClass}>Mes pivot</label>
          <select
            className={inputClass}
            value={config.mesPivot}
            onChange={(e) => setConfig({ mesPivot: Number(e.target.value) })}
          >
            {MESES_ES.map((m, i) => (
              <option key={i + 1} value={i + 1} className="bg-surface text-primary">
                {m}
              </option>
            ))}
          </select>
        </motion.div>

        {/* Horizonte */}
        <motion.div variants={fadeInUp} className="flex flex-col gap-2">
          <label className={labelClass}>
            Horizonte ·{" "}
            <span className="font-mono text-accent normal-case tracking-normal">
              {config.horizonte} meses
            </span>
          </label>
          <input
            type="range"
            min={1}
            max={24}
            value={config.horizonte}
            onChange={(e) => setConfig({ horizonte: Number(e.target.value) })}
            className="w-full accent-[color:var(--accent)]"
          />
          <div className="flex justify-between text-[10px] uppercase tracking-widest text-muted">
            <span>1 mes</span>
            <span>24 meses</span>
          </div>
        </motion.div>

        {/* Preview */}
        <motion.div
          variants={fadeInUp}
          className="bg-accent/[0.06] border border-accent/20 rounded-xl px-4 py-3 text-sm text-secondary"
        >
          Proyectando desde{" "}
          <strong className="text-primary font-medium">{MESES_ES[config.mesPivot - 1]}</strong> hasta{" "}
          <strong className="text-primary font-medium">
            {mesFinHorizonte(config.mesPivot, config.horizonte)}
          </strong>{" "}
          <span className="font-mono text-accent">({config.horizonte} meses)</span>
        </motion.div>

        {/* Día de corte */}
        <motion.div variants={fadeInUp} className="flex flex-col gap-2">
          <label className={labelClass}>
            Día de corte MTD{" "}
            <span className="text-muted normal-case tracking-normal lowercase">
              (opcional — vacío si el mes está completo)
            </span>
          </label>
          <input
            type="number"
            min={1}
            max={31}
            placeholder="Ej: 15"
            value={config.diaCorte ?? ""}
            onChange={(e) => setConfig({ diaCorte: e.target.value ? Number(e.target.value) : null })}
            className={`${inputClass} font-mono`}
          />
        </motion.div>

        {/* Escenario */}
        <motion.div variants={fadeInUp} className="flex flex-col gap-2">
          <label className={labelClass}>
            Etiqueta de escenario{" "}
            <span className="text-muted normal-case tracking-normal lowercase">(opcional)</span>
          </label>
          <input
            type="text"
            placeholder="Ej: Caso Base"
            value={config.escenario}
            onChange={(e) => setConfig({ escenario: e.target.value })}
            className={inputClass}
          />
        </motion.div>
      </motion.div>

      <div className="flex justify-between items-center mt-6 max-w-xl">
        <button
          className="px-5 py-2.5 text-sm font-medium text-secondary hover:text-primary transition-colors"
          onClick={() => setStep(1)}
        >
          ← Volver
        </button>
        <button
          className="px-7 py-3 rounded-full bg-accent text-base font-semibold text-sm
                     hover:shadow-glow transition-all duration-300 hover:scale-105 active:scale-95
                     disabled:opacity-50 disabled:hover:scale-100"
          onClick={handleSubmit}
          disabled={mutation.isPending}
        >
          {mutation.isPending ? "Guardando…" : "Siguiente →"}
        </button>
      </div>
    </div>
  );
}
