import { useMutation } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { FileDropzone } from "../components/FileDropzone";
import { PageHeader } from "../components/PageHeader";
import { uploadBase2026 } from "../api/client";
import { useWizard } from "../store/wizard";
import { fadeInUp, staggerContainer } from "../lib/motion";

const MESES_ES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"];

const STATS = [
  { label: "Países", value: "10+" },
  { label: "Líneas P&L", value: "20+" },
  { label: "Meses proyectados", value: "24" },
];

export function Step1UploadBase() {
  const {
    sessionId,
    base2026Loaded,
    base2026Rows,
    base2026Meses,
    setBase2026Loaded,
    setStep,
  } = useWizard();

  const mutation = useMutation({
    mutationFn: (file: File) => uploadBase2026(sessionId, file),
  });

  async function handleFile(file: File) {
    const result = await mutation.mutateAsync(file);
    if (!result.ok) {
      throw new Error(result.errors.join(" | "));
    }
    setBase2026Loaded(result.rows, result.meses);
  }

  return (
    <div className="flex flex-col">
      <PageHeader
        badge="HTML · B2B · Canal"
        titleLead="Modelo"
        titleAccent="Run Rate"
        subtitle="Proyección inteligente del P&L con estacionalidad, actuals calibrados y export a Excel en segundos. Empezá subiendo la Base 2026."
      />

      <div className="max-w-2xl">
        <FileDropzone
          onFile={handleFile}
          accept=".xlsx"
          label="Arrastrá la Base 2026 acá"
          successLabel={
            base2026Loaded
              ? `${base2026Rows.toLocaleString("es-AR")} filas · ${base2026Meses
                  .map((m) => MESES_ES[m - 1])
                  .join(", ")}`
              : undefined
          }
        />

        {mutation.data?.errors?.length ? (
          <ul className="mt-4 bg-neg/[0.06] border border-neg/30 rounded-xl p-4 text-sm text-neg list-disc list-inside space-y-1">
            {mutation.data.errors.map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        ) : null}

        {base2026Loaded && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex justify-end mt-6"
          >
            <button
              className="px-7 py-3 rounded-full bg-accent text-base font-semibold text-sm
                         hover:shadow-glow transition-all duration-300 hover:scale-105 active:scale-95"
              onClick={() => setStep(1)}
            >
              Siguiente →
            </button>
          </motion.div>
        )}
      </div>

      {/* Stats row */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-3 gap-8 mt-16 pt-10 border-t border-[color:var(--border)] max-w-2xl"
      >
        {STATS.map((s) => (
          <motion.div key={s.label} variants={fadeInUp} className="flex flex-col gap-1.5">
            <span className="font-mono text-3xl font-medium text-accent">{s.value}</span>
            <span className="text-[10px] uppercase tracking-widest text-secondary">{s.label}</span>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
