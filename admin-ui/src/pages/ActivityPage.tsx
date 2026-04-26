import { motion, useReducedMotion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { connectEvents } from "../lib/ws";

type LogEvt = {
  type?: string;
  ts?: string;
  level?: string;
  message?: string;
  metadata?: unknown;
};

export default function ActivityPage() {
  const [lines, setLines] = useState<LogEvt[]>([]);
  const bottom = useRef<HTMLDivElement>(null);
  const reduce = useReducedMotion();

  useEffect(() => {
    const ws = connectEvents((raw) => {
      const e = raw as LogEvt;
      setLines((prev) => {
        const next = [...prev, e];
        return next.slice(-500);
      });
    });
    return () => ws.close();
  }, []);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: reduce ? "auto" : "smooth" });
  }, [lines, reduce]);

  return (
    <div className="flex min-h-[70dvh] flex-col space-y-5 md:min-h-[calc(100dvh-8rem)]">
      <motion.header
        initial={reduce ? false : { opacity: 0, y: -6 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="font-display text-3xl font-extrabold tracking-tight text-gradient md:text-4xl">
          Activity
        </h1>
        <p className="mt-2 text-sm text-muted-foreground md:text-base">
          Live logs and status events over WebSocket — tail stays pinned to the latest line.
        </p>
      </motion.header>

      <motion.div
        initial={reduce ? false : { opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-4xl border border-border/60 bg-card/50 shadow-soft-lg backdrop-blur-xl"
      >
        <div className="flex-1 overflow-auto p-4 font-mono text-[11px] leading-relaxed sm:text-xs md:p-5">
          {lines.map((e, i) => {
            const row = e as LogEvt & { data?: unknown };
            if (row.type === "status") {
              return (
                <div
                  key={i}
                  className="border-b border-border/40 py-2 text-warning"
                >
                  <span className="font-semibold text-accent-secondary">[status]</span>{" "}
                  {JSON.stringify(row.data)}
                </div>
              );
            }
            return (
              <div
                key={i}
                className={`border-b border-border/30 py-2 transition-colors ${
                  e.level === "ERROR" ? "text-danger bg-danger/5" : "text-card-foreground"
                }`}
              >
                <span className="text-muted-foreground">{e.ts}</span>{" "}
                <span className="font-semibold text-accent">{e.level}</span> {e.message}{" "}
                {e.metadata !== undefined && (
                  <span className="text-muted-foreground">{JSON.stringify(e.metadata)}</span>
                )}
              </div>
            );
          })}
          <div ref={bottom} />
        </div>
      </motion.div>
    </div>
  );
}
