import { Fragment } from "react";
import { motion } from "framer-motion";
import { clsx } from "clsx";

interface StepperProps {
  steps: string[];
  currentStep: number;
  onStepClick?: (i: number) => void;
}

/**
 * Stepper horizontal minimal (patrón skill — dark dashboard).
 * Los pasos ya recorridos son clicables si se provee onStepClick.
 */
export function Stepper({ steps, currentStep, onStepClick }: StepperProps) {
  return (
    <div className="flex items-center gap-0 w-full select-none">
      {steps.map((step, i) => {
        const done = i < currentStep;
        const active = i === currentStep;
        const clickable = onStepClick && i <= currentStep;
        return (
          <Fragment key={step}>
            <button
              type="button"
              disabled={!clickable}
              onClick={() => clickable && onStepClick(i)}
              className={clsx(
                "flex items-center gap-2 flex-shrink-0 group",
                clickable ? "cursor-pointer" : "cursor-default"
              )}
            >
              <span className="relative flex items-center justify-center">
                {active && (
                  <motion.span
                    className="absolute inset-0 rounded-full border border-accent/40"
                    initial={{ scale: 1, opacity: 0.7 }}
                    animate={{ scale: 1.6, opacity: 0 }}
                    transition={{ duration: 1.4, repeat: Infinity, ease: "easeOut" }}
                  />
                )}
                <span
                  className={clsx(
                    "w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold transition-all duration-300",
                    done && "bg-accent text-base",
                    active && "bg-accent text-base shadow-glow",
                    !done && !active && "bg-surface border border-[color:var(--border)] text-secondary"
                  )}
                >
                  {done ? (
                    <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none">
                      <path
                        d="M3 8l4 4 6-7"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  ) : (
                    i + 1
                  )}
                </span>
              </span>
              <span
                className={clsx(
                  "text-xs font-medium tracking-wide whitespace-nowrap hidden sm:inline transition-colors",
                  active ? "text-accent" : done ? "text-secondary group-hover:text-primary" : "text-muted"
                )}
              >
                {step}
              </span>
            </button>

            {i < steps.length - 1 && (
              <div
                className={clsx(
                  "flex-1 h-px mx-2 sm:mx-3 transition-colors duration-500 min-w-[16px]",
                  done ? "bg-accent/50" : "bg-[color:var(--border)]"
                )}
              />
            )}
          </Fragment>
        );
      })}
    </div>
  );
}
