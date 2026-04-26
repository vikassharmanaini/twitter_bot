import { motion, useReducedMotion } from "framer-motion";
import { Link, useLocation } from "react-router-dom";

/** Persistent shortcut to the guide; hidden on the instructions page itself. */
export function FloatingInstructionButton() {
  const { pathname } = useLocation();
  const reduce = useReducedMotion();

  if (pathname === "/instructions") return null;

  return (
    <motion.div
      initial={reduce ? false : { scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: "spring", stiffness: 400, damping: 28 }}
      className="fixed bottom-[calc(4.75rem+env(safe-area-inset-bottom,0px))] right-4 z-[45] lg:bottom-8 lg:right-8"
    >
      <Link
        to="/instructions"
        className="group flex items-center gap-2 rounded-full border border-accent/40 bg-gradient-to-r from-accent/90 via-accent-secondary/85 to-accent-tertiary/90 px-4 py-3 text-sm font-bold text-white shadow-glow ring-2 ring-white/10 backdrop-blur-md transition hover:scale-[1.03] hover:shadow-soft-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-canvas sm:px-5 sm:py-3.5"
        aria-label="Open instructions and terminal guide"
      >
        <span className="text-lg leading-none drop-shadow-md" aria-hidden>
          📘
        </span>
        <span className="hidden max-w-[7rem] truncate sm:inline">Guide</span>
      </Link>
    </motion.div>
  );
}
