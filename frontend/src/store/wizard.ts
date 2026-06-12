import { create } from "zustand";
import { persist } from "zustand/middleware";
import { v4 as uuidv4 } from "uuid";
import type { BuildResult } from "../api/client";

interface WizardConfig {
  mesPivot: number;
  horizonte: number;
  diaCorte: number | null;
  escenario: string;
}

interface WizardState {
  sessionId: string;
  step: number;
  base2026Loaded: boolean;
  base2026Rows: number;
  base2026Meses: number[];
  contableLoaded: boolean;
  contableRows: number;
  config: WizardConfig;
  pnlResult: BuildResult | null;

  setStep: (n: number) => void;
  setBase2026Loaded: (rows: number, meses: number[]) => void;
  setContableLoaded: (rows: number) => void;
  setConfig: (c: Partial<WizardConfig>) => void;
  setPnlResult: (r: BuildResult) => void;
  reset: () => void;
}

const DEFAULT_CONFIG: WizardConfig = {
  mesPivot: 5,
  horizonte: 12,
  diaCorte: null,
  escenario: "",
};

export const useWizard = create<WizardState>()(
  persist(
    (set) => ({
      sessionId: uuidv4(),
      step: 0,
      base2026Loaded: false,
      base2026Rows: 0,
      base2026Meses: [],
      contableLoaded: false,
      contableRows: 0,
      config: { ...DEFAULT_CONFIG },
      pnlResult: null,

      setStep: (n) => set({ step: n }),

      setBase2026Loaded: (rows, meses) =>
        set({ base2026Loaded: true, base2026Rows: rows, base2026Meses: meses }),

      setContableLoaded: (rows) =>
        set({ contableLoaded: true, contableRows: rows }),

      setConfig: (c) =>
        set((s) => ({ config: { ...s.config, ...c } })),

      setPnlResult: (r) => set({ pnlResult: r }),

      reset: () =>
        set({
          sessionId: uuidv4(),
          step: 0,
          base2026Loaded: false,
          base2026Rows: 0,
          base2026Meses: [],
          contableLoaded: false,
          contableRows: 0,
          config: { ...DEFAULT_CONFIG },
          pnlResult: null,
        }),
    }),
    {
      name: "rrai-wizard",
      partialize: (s) => ({
        sessionId: s.sessionId,
        step: s.step,
        base2026Loaded: s.base2026Loaded,
        base2026Rows: s.base2026Rows,
        base2026Meses: s.base2026Meses,
        contableLoaded: s.contableLoaded,
        config: s.config,
      }),
    }
  )
);
