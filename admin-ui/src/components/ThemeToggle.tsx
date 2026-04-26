import { motion, useReducedMotion } from "framer-motion";
import { useTheme } from "../context/ThemeContext";

export function ThemeToggle() {
  const { theme, toggleTheme, isDark } = useTheme();
  const reduce = useReducedMotion();

  return (
    <motion.button
      type="button"
      onClick={toggleTheme}
      whileTap={reduce ? undefined : { scale: 0.94 }}
      whileHover={reduce ? undefined : { scale: 1.04 }}
      className="relative flex h-11 w-11 items-center justify-center rounded-2xl border border-border/80 bg-card/80 text-foreground shadow-soft backdrop-blur-md transition-colors hover:border-accent/40 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/50"
      title={isDark ? "Switch to light theme" : "Switch to dark theme"}
      aria-label={`Switch to ${isDark ? "light" : "dark"} theme`}
      aria-pressed={isDark}
    >
      <span className="sr-only">Theme: {theme}</span>
      <motion.span
        className="text-lg leading-none"
        initial={false}
        animate={{ rotate: isDark ? 0 : 180 }}
        transition={{ type: "spring", stiffness: 260, damping: 22 }}
      >
        {isDark ? "🌙" : "☀️"}
      </motion.span>
    </motion.button>
  );
}
