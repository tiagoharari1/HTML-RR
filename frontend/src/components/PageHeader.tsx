import type { ReactNode } from "react";
import { motion } from "framer-motion";
import { fadeInUp, staggerContainer } from "../lib/motion";

interface PageHeaderProps {
  badge?: string;
  /** Texto antes de la(s) palabra(s) en serif italic */
  titleLead?: string;
  /** Palabra(s) clave con tratamiento serif italic acento */
  titleAccent: string;
  /** Texto después del acento */
  titleTail?: string;
  subtitle?: ReactNode;
  /** Contenido alineado a la derecha (ej: botón Volver) */
  aside?: ReactNode;
}

export function PageHeader({
  badge,
  titleLead,
  titleAccent,
  titleTail,
  subtitle,
  aside,
}: PageHeaderProps) {
  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="flex items-start justify-between gap-6 mb-10"
    >
      <div className="flex flex-col gap-4">
        {badge && (
          <motion.span
            variants={fadeInUp}
            className="self-start px-3 py-1 rounded-full border border-accent/30 bg-accent/10
                       text-accent text-[10px] font-medium tracking-widest uppercase"
          >
            {badge}
          </motion.span>
        )}
        <motion.h1
          variants={fadeInUp}
          className="text-4xl md:text-5xl font-sans font-light text-primary leading-tight"
        >
          {titleLead && <span>{titleLead} </span>}
          <span className="font-serif italic text-accent">{titleAccent}</span>
          {titleTail && <span> {titleTail}</span>}
        </motion.h1>
        {subtitle && (
          <motion.p variants={fadeInUp} className="text-base text-secondary max-w-xl">
            {subtitle}
          </motion.p>
        )}
      </div>
      {aside && (
        <motion.div variants={fadeInUp} className="flex-shrink-0">
          {aside}
        </motion.div>
      )}
    </motion.div>
  );
}
