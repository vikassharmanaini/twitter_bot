import { motion, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";

type Props = {
  children: ReactNode;
  className?: string;
  delay?: number;
  hover?: boolean;
};

export function GlassCard({ children, className = "", delay = 0, hover = true }: Props) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      initial={reduce ? false : { opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: reduce ? 0 : 0.45,
        delay: reduce ? 0 : delay,
        ease: [0.22, 1, 0.36, 1],
      }}
      whileHover={
        reduce || !hover
          ? undefined
          : { y: -2, transition: { type: "spring", stiffness: 400, damping: 25 } }
      }
      className={`rounded-4xl glass-strong p-6 md:p-7 ${className}`}
    >
      {children}
    </motion.div>
  );
}
