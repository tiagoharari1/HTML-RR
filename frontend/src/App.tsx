import { AnimatePresence, motion } from "framer-motion";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Stepper } from "./components/Stepper";
import { Step1UploadBase } from "./pages/Step1UploadBase";
import { Step2UploadContable } from "./pages/Step2UploadContable";
import { Step3Config } from "./pages/Step3Config";
import { Step4Resultado } from "./pages/Step4Resultado";
import { useWizard } from "./store/wizard";

const qc = new QueryClient();

const STEPS = ["Base 2026", "Contable", "Configuración", "Resultado"];

const PAGES = [
  <Step1UploadBase key="s1" />,
  <Step2UploadContable key="s2" />,
  <Step3Config key="s3" />,
  <Step4Resultado key="s4" />,
];

function Navbar() {
  const { step, setStep } = useWizard();
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-base/80 backdrop-blur-xl border-b border-[color:var(--border)]">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center gap-6">
        {/* Logo */}
        <div className="flex items-center gap-2.5 flex-shrink-0">
          <div className="w-8 h-8 rounded-lg bg-accent/10 border border-accent/30 flex items-center justify-center">
            <span className="font-mono text-accent text-sm font-medium">RR</span>
          </div>
          <div className="leading-none hidden md:block">
            <span className="font-serif italic text-accent text-lg">Run Rate</span>
            <p className="text-[10px] uppercase tracking-widest text-muted mt-0.5">HTML · B2B</p>
          </div>
        </div>

        {/* Stepper */}
        <div className="flex-1 max-w-2xl ml-auto">
          <Stepper steps={STEPS} currentStep={step} onStepClick={setStep} />
        </div>
      </div>
    </nav>
  );
}

function Layout() {
  const { step } = useWizard();

  return (
    <div className="relative min-h-screen bg-base overflow-x-hidden">
      {/* Fondo mesh fijo */}
      <div className="fixed inset-0 bg-hero-mesh pointer-events-none" />

      <Navbar />

      <main className="relative z-10 max-w-6xl mx-auto px-6 pt-28 pb-24">
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ y: 16, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -12, opacity: 0 }}
            transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
          >
            {PAGES[step]}
          </motion.div>
        </AnimatePresence>
      </main>

      <footer className="relative z-10 max-w-6xl mx-auto px-6 pb-10">
        <p className="text-[10px] text-muted tracking-widest uppercase">
          Despegar · HTML B2B · v2.0 FastAPI + React
        </p>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <Layout />
    </QueryClientProvider>
  );
}
