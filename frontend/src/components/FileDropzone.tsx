import { useCallback, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { clsx } from "clsx";

type DropzoneState = "idle" | "dragging" | "uploading" | "success" | "error";

interface FileDropzoneProps {
  onFile: (file: File) => Promise<void>;
  accept?: string;
  label?: string;
  successLabel?: string;
  disabled?: boolean;
}

export function FileDropzone({
  onFile,
  accept = ".xlsx",
  label = "Arrastrá o hacé click para subir el archivo",
  successLabel,
  disabled = false,
}: FileDropzoneProps) {
  const [state, setState] = useState<DropzoneState>("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setState("uploading");
      try {
        await onFile(file);
        setState("success");
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Error al cargar el archivo";
        setErrorMsg(msg);
        setState("error");
      }
    },
    [onFile]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      if (disabled) return;
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [disabled, handleFile]
  );

  const onClick = () => {
    if (!disabled && state !== "uploading") inputRef.current?.click();
  };

  const bgClass = clsx(
    "relative flex flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed p-12 cursor-pointer transition-all duration-200",
    state === "dragging" && "border-accent bg-accent/10 scale-[1.02]",
    state === "idle" && "border-[color:var(--border)] hover:border-accent/40 hover:bg-surface2",
    state === "uploading" && "border-accent/30 bg-accent/[0.04] cursor-wait",
    state === "success" && "border-accent/60 bg-accent/[0.06] cursor-default",
    state === "error" && "border-neg/50 bg-neg/[0.06]",
    disabled && "opacity-50 cursor-not-allowed"
  );

  return (
    <div
      className={bgClass}
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setState("dragging");
      }}
      onDragLeave={() => setState(state === "dragging" ? "idle" : state)}
      onDrop={onDrop}
      onClick={onClick}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />

      <AnimatePresence mode="wait">
        {state === "success" && (
          <motion.div
            key="success"
            initial={{ scale: 0.6, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="flex flex-col items-center gap-2 text-center"
          >
            <motion.div
              className="w-12 h-12 rounded-full bg-accent flex items-center justify-center text-base shadow-glow"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", stiffness: 400 }}
            >
              <svg viewBox="0 0 24 24" className="w-6 h-6" fill="none">
                <path
                  d="M5 13l4 4L19 7"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </motion.div>
            <p className="text-sm font-medium text-accent">
              {successLabel ?? "Archivo cargado correctamente"}
            </p>
            <button
              type="button"
              className="text-xs text-secondary hover:text-primary underline transition-colors"
              onClick={(e) => {
                e.stopPropagation();
                setState("idle");
              }}
            >
              Reemplazar
            </button>
          </motion.div>
        )}

        {state === "uploading" && (
          <motion.div
            key="uploading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center gap-3"
          >
            <div className="w-8 h-8 rounded-full border-2 border-accent border-t-transparent animate-spin" />
            <p className="text-sm text-secondary">Procesando…</p>
          </motion.div>
        )}

        {state === "error" && (
          <motion.div
            key="error"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center gap-2 text-center"
          >
            <div className="w-10 h-10 rounded-full bg-neg/15 flex items-center justify-center text-neg text-xl font-bold">
              !
            </div>
            <p className="text-sm text-neg max-w-sm">{errorMsg}</p>
            <button
              type="button"
              className="text-xs text-neg/80 hover:text-neg underline transition-colors"
              onClick={(e) => {
                e.stopPropagation();
                setState("idle");
              }}
            >
              Reintentar
            </button>
          </motion.div>
        )}

        {(state === "idle" || state === "dragging") && (
          <motion.div
            key="idle"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center gap-3 text-center"
          >
            <div className="w-12 h-12 rounded-2xl bg-accent/10 border border-accent/20 flex items-center justify-center text-accent">
              <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none">
                <path
                  d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M12 4v12M8 8l4-4 4 4"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
            <p className="text-sm font-medium text-primary">{label}</p>
            <p className="text-xs text-muted uppercase tracking-widest">Formato · {accept}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
