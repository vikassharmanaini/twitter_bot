import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion, useReducedMotion } from "framer-motion";
import { lazy, Suspense } from "react";
import { GlassCard } from "../components/GlassCard";
import { apiGet, apiSend } from "../lib/api";

const DashboardCharts = lazy(async () => {
  const m = await import("../components/charts/DashboardCharts");
  return { default: m.DashboardCharts };
});

type Status = Record<string, unknown>;
type WeeklyResp = { count?: number; items?: { posted_at?: string }[] };
type DbResp = { counts?: Record<string, number> };

const btnBase =
  "relative overflow-hidden rounded-2xl px-4 py-2.5 text-sm font-bold shadow-soft transition-shadow focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-canvas disabled:opacity-45";

export default function Dashboard() {
  const qc = useQueryClient();
  const reduce = useReducedMotion();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["status"],
    queryFn: () => apiGet<Status>("/api/runtime/status"),
    refetchInterval: 5000,
  });

  const { data: weekly } = useQuery({
    queryKey: ["weekly-stats"],
    queryFn: () => apiGet<WeeklyResp>("/api/stats/weekly"),
    refetchInterval: 60_000,
  });

  const { data: db } = useQuery({
    queryKey: ["db-summary"],
    queryFn: () => apiGet<DbResp>("/api/db/summary"),
    refetchInterval: 60_000,
  });

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["status"] });
    qc.invalidateQueries({ queryKey: ["weekly-stats"] });
    qc.invalidateQueries({ queryKey: ["db-summary"] });
  };

  const start = useMutation({
    mutationFn: () => apiSend<Record<string, string>>("/api/runtime/start", "POST"),
    onSuccess: invalidate,
  });
  const stop = useMutation({
    mutationFn: () => apiSend<Record<string, string>>("/api/runtime/stop", "POST"),
    onSuccess: invalidate,
  });
  const pause = useMutation({
    mutationFn: () => apiSend<Record<string, string>>("/api/runtime/pause", "POST"),
    onSuccess: invalidate,
  });
  const resume = useMutation({
    mutationFn: () => apiSend<Record<string, string>>("/api/runtime/resume", "POST"),
    onSuccess: invalidate,
  });
  const dryRun = useMutation({
    mutationFn: () => apiSend<Record<string, unknown>>("/api/runtime/dry-run", "POST"),
    onSuccess: invalidate,
  });

  const err =
    (error as Error)?.message ||
    start.error?.message ||
    stop.error?.message ||
    dryRun.error?.message;

  const runtime = data?.runtime != null ? String(data.runtime) : "—";
  const paused = data?.paused != null ? String(data.paused) : "—";
  const repliesToday = data?.replies_today != null ? String(data.replies_today) : "—";
  const dryRunCfg = data?.dry_run != null ? String(data.dry_run) : "—";

  const statTiles = [
    { label: "Runtime", value: runtime, accent: "text-accent" },
    { label: "Paused", value: paused, accent: "text-warning" },
    { label: "Replies today", value: repliesToday, accent: "text-accent-secondary" },
    { label: "Dry-run cfg", value: dryRunCfg, accent: "text-accent-tertiary" },
  ];

  return (
    <div className="space-y-8 md:space-y-10">
      <motion.header
        initial={reduce ? false : { opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <h1 className="font-display text-3xl font-extrabold tracking-tight text-gradient md:text-4xl">
          Dashboard
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground md:text-base">
          Live status, scheduler, charts from your store, and one-tap controls — optimized for quick
          checks on any screen size.
        </p>
      </motion.header>

      {err && (
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className="rounded-3xl border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-danger backdrop-blur-md"
        >
          {err}
        </motion.div>
      )}

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {statTiles.map((s, i) => (
          <motion.div
            key={s.label}
            initial={reduce ? false : { opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: reduce ? 0 : 0.05 * i, duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
            className="rounded-3xl border border-border/60 bg-card/60 p-4 shadow-soft backdrop-blur-md"
          >
            <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
              {s.label}
            </div>
            <div className={`mt-2 truncate font-mono text-lg font-bold ${s.accent}`}>{s.value}</div>
          </motion.div>
        ))}
      </div>

      <Suspense
        fallback={
          <div className="grid gap-6 lg:grid-cols-2">
            <div className="h-[320px] animate-pulse rounded-4xl bg-muted/60" />
            <div className="h-[320px] animate-pulse rounded-4xl bg-muted/60" />
          </div>
        }
      >
        <DashboardCharts weekly={weekly} db={db} />
      </Suspense>

      <div className="grid gap-6 lg:grid-cols-2">
        <GlassCard delay={0.06} hover={false}>
          <h2 className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
            Full status
          </h2>
          {isLoading ? (
            <div className="mt-6 space-y-3">
              {[1, 2, 3, 4].map((k) => (
                <div
                  key={k}
                  className="h-4 animate-pulse rounded-lg bg-muted/80"
                  style={{ width: `${70 + k * 5}%` }}
                />
              ))}
            </div>
          ) : (
            <dl className="mt-4 max-h-72 space-y-2 overflow-auto text-sm md:max-h-96">
              {Object.entries(data ?? {}).map(([k, v]) => (
                <div
                  key={k}
                  className="flex justify-between gap-4 rounded-xl bg-muted/30 px-3 py-2 border border-border/40"
                >
                  <dt className="text-muted-foreground">{k}</dt>
                  <dd className="max-w-[58%] truncate text-right font-mono text-card-foreground">
                    {typeof v === "object" ? JSON.stringify(v) : String(v)}
                  </dd>
                </div>
              ))}
            </dl>
          )}
          <button
            type="button"
            onClick={() => refetch()}
            className="mt-4 text-xs font-semibold text-accent hover:underline"
          >
            Refresh now
          </button>
        </GlassCard>

        <GlassCard delay={0.1} hover={false}>
          <h2 className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
            Actions
          </h2>
          <div className="mt-4 flex flex-wrap gap-2">
            <motion.button
              type="button"
              disabled={start.isPending}
              onClick={() => start.mutate()}
              whileHover={reduce ? undefined : { scale: 1.02 }}
              whileTap={reduce ? undefined : { scale: 0.97 }}
              className={`${btnBase} bg-gradient-to-br from-success to-emerald-600 text-white focus-visible:ring-success`}
            >
              Start loop
            </motion.button>
            <motion.button
              type="button"
              disabled={stop.isPending}
              onClick={() => stop.mutate()}
              whileHover={reduce ? undefined : { scale: 1.02 }}
              whileTap={reduce ? undefined : { scale: 0.97 }}
              className={`${btnBase} bg-gradient-to-br from-danger to-rose-600 text-white focus-visible:ring-danger`}
            >
              Stop
            </motion.button>
            <motion.button
              type="button"
              disabled={pause.isPending}
              onClick={() => pause.mutate()}
              whileHover={reduce ? undefined : { scale: 1.02 }}
              whileTap={reduce ? undefined : { scale: 0.97 }}
              className={`${btnBase} bg-gradient-to-br from-warning to-amber-500 text-slate-900 focus-visible:ring-warning`}
            >
              Pause
            </motion.button>
            <motion.button
              type="button"
              disabled={resume.isPending}
              onClick={() => resume.mutate()}
              whileHover={reduce ? undefined : { scale: 1.02 }}
              whileTap={reduce ? undefined : { scale: 0.97 }}
              className={`${btnBase} bg-gradient-to-br from-accent-secondary to-sky-500 text-white focus-visible:ring-accent-secondary`}
            >
              Resume
            </motion.button>
            <motion.button
              type="button"
              disabled={dryRun.isPending}
              onClick={() => dryRun.mutate()}
              whileHover={reduce ? undefined : { scale: 1.02 }}
              whileTap={reduce ? undefined : { scale: 0.97 }}
              className={`${btnBase} border border-border bg-muted/80 text-foreground backdrop-blur-sm focus-visible:ring-accent`}
            >
              Dry-run once
            </motion.button>
          </div>
          {dryRun.isSuccess && dryRun.data && (
            <pre className="mt-4 max-h-48 overflow-auto rounded-2xl border border-border/60 bg-muted/40 p-3 text-xs text-card-foreground">
              {JSON.stringify(dryRun.data, null, 2)}
            </pre>
          )}
        </GlassCard>
      </div>
    </div>
  );
}
