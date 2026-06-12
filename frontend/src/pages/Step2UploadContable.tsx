import { useMutation } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { FileDropzone } from "../components/FileDropzone";
import { PageHeader } from "../components/PageHeader";
import { uploadContable } from "../api/client";
import { useWizard } from "../store/wizard";

export function Step2UploadContable() {
  const { sessionId, contableLoaded, contableRows, setContableLoaded, setStep } = useWizard();

  const mutation = useMutation({
    mutationFn: (file: File) => uploadContable(sessionId, file),
  });

  async function handleFile(file: File) {
    const result = await mutation.mutateAsync(file);
    if (!result.ok) {
      throw new Error(result.errors.join(" | "));
    }
    setContableLoaded(result.rows);
  }

  return (
    <div className="flex flex-col">
      <PageHeader
        badge="Paso 2 · Opcional"
        titleLead="Datos"
        titleAccent="Contables"
        subtitle="Referencia contable opcional, sólo para visualización. Podés saltarte este paso y avanzar directo a la configuración."
      />

      <div className="max-w-2xl">
        <FileDropzone
          onFile={handleFile}
          accept=".xlsx"
          label="Arrastrá el archivo Contable acá"
          successLabel={
            contableLoaded ? `${contableRows.toLocaleString("es-AR")} filas cargadas` : undefined
          }
        />

        {mutation.data?.errors?.length ? (
          <ul className="mt-4 bg-neg/[0.06] border border-neg/30 rounded-xl p-4 text-sm text-neg list-disc list-inside space-y-1">
            {mutation.data.errors.map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        ) : null}

        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex justify-between items-center mt-6"
        >
          <button
            className="px-5 py-2.5 text-sm font-medium text-secondary hover:text-primary transition-colors"
            onClick={() => setStep(0)}
          >
            ← Volver
          </button>
          <button
            className="px-7 py-3 rounded-full bg-accent text-base font-semibold text-sm
                       hover:shadow-glow transition-all duration-300 hover:scale-105 active:scale-95"
            onClick={() => setStep(2)}
          >
            {contableLoaded ? "Siguiente →" : "Saltar →"}
          </button>
        </motion.div>
      </div>
    </div>
  );
}
