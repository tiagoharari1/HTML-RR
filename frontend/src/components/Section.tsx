import { useRef } from "react";
import type { ReactNode } from "react";
import { motion, useInView } from "framer-motion";
import { EASE_LUX } from "../lib/motion";

interface SectionProps {
  children: ReactNode;
  className?: string;
  delay?: number;
}

/**
 * Sección que entra desde abajo al hacer scroll (patrón cielhomes.in).
 * Se anima una sola vez cuando entra en viewport.
 */
export function Section({ children, className, delay = 0 }: SectionProps) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <motion.section
      ref={ref}
      initial={{ opacity: 0, y: 40 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6, ease: EASE_LUX, delay }}
      className={className}
    >
      {children}
    </motion.section>
  );
}
