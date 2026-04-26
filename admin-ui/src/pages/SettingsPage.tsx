import { motion, useReducedMotion } from "framer-motion";
import { useState } from "react";
import { GlassCard } from "../components/GlassCard";
import { getToken, setToken } from "../lib/api";

export default function SettingsPage() {
  const [t, setT] = useState(getToken());
  const reduce = useReducedMotion();

  return (
    <div className="mx-auto max-w-lg space-y-6 md:space-y-8">
      <motion.header
        initial={reduce ? false : { opacity: 0, y: -6 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="font-display text-3xl font-extrabold tracking-tight text-gradient md:text-4xl">
          Settings
        </h1>
        <p className="mt-2 text-sm text-muted-foreground md:text-base">
          Optional <code className="rounded bg-muted px-1 text-accent">ADMIN_TOKEN</code>. Stored in
          localStorage and sent as Bearer for API and WebSocket.
        </p>
      </motion.header>

      <GlassCard delay={0.06} hover={false} className="space-y-4 !p-6">
        <label className="block text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
          Admin token
        </label>
        <input
          type="password"
          className="w-full rounded-2xl border border-border/60 bg-canvas/80 px-4 py-3 text-sm focus:border-accent/50 focus:outline-none focus:ring-2 focus:ring-accent/25"
          value={t}
          onChange={(e) => setT(e.target.value)}
          placeholder="Paste token if server has ADMIN_TOKEN set"
        />
        <div className="flex flex-wrap gap-2">
          <motion.button
            type="button"
            onClick={() => setToken(t)}
            whileTap={reduce ? undefined : { scale: 0.97 }}
            className="rounded-2xl bg-gradient-to-r from-accent to-accent-secondary px-5 py-2.5 text-sm font-bold text-white shadow-glow"
          >
            Save token
          </motion.button>
          <motion.button
            type="button"
            onClick={() => {
              setToken("");
              setT("");
            }}
            whileTap={reduce ? undefined : { scale: 0.97 }}
            className="rounded-2xl border border-border/80 bg-muted/50 px-5 py-2.5 text-sm font-semibold text-muted-foreground"
          >
            Clear
          </motion.button>
        </div>
      </GlassCard>
    </div>
  );
}
