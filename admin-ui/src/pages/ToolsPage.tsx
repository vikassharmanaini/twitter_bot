import { useMutation } from "@tanstack/react-query";
import { motion, useReducedMotion } from "framer-motion";
import { GlassCard } from "../components/GlassCard";
import { apiSend } from "../lib/api";

const tools = [
  {
    key: "ku",
    title: "Knowledge update",
    desc: "Refresh knowledge_snippets from hot topics.",
    gradient: "from-accent/30 via-accent-secondary/20 to-transparent",
    icon: "◆",
  },
  {
    key: "perf",
    title: "Performance analysis",
    desc: "Writes data/performance_insights.md",
    gradient: "from-accent-secondary/30 via-accent/15 to-transparent",
    icon: "◇",
  },
  {
    key: "sug",
    title: "Suggest targets",
    desc: "Writes data/suggested_targets.md",
    gradient: "from-accent-tertiary/30 via-accent/15 to-transparent",
    icon: "○",
  },
  {
    key: "rep",
    title: "HTML report",
    desc: "Generates report.html",
    gradient: "from-success/25 via-accent-secondary/15 to-transparent",
    icon: "▣",
  },
] as const;

export default function ToolsPage() {
  const reduce = useReducedMotion();
  const ku = useMutation({
    mutationFn: () => apiSend<Record<string, unknown>>("/api/jobs/knowledge-update", "POST"),
  });
  const perf = useMutation({
    mutationFn: () => apiSend<Record<string, unknown>>("/api/jobs/performance", "POST"),
  });
  const sug = useMutation({
    mutationFn: () => apiSend<Record<string, unknown>>("/api/jobs/suggest-targets", "POST"),
  });
  const rep = useMutation({
    mutationFn: () =>
      apiSend<Record<string, unknown>>("/api/jobs/report", "POST", { out: "report.html" }),
  });

  const err =
    ku.error?.message || perf.error?.message || sug.error?.message || rep.error?.message;

  const mutations = { ku, perf, sug, rep };

  return (
    <div className="space-y-6 md:space-y-8">
      <motion.header
        initial={reduce ? false : { opacity: 0, y: -6 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="font-display text-3xl font-extrabold tracking-tight text-gradient md:text-4xl">
          Tools
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground md:text-base">
          Maintenance jobs (same as CLI). Requires valid API credentials in config.
        </p>
      </motion.header>

      {err && (
        <div className="rounded-3xl border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-danger">
          {err}
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        {tools.map((t, i) => {
          const m = mutations[t.key as keyof typeof mutations];
          return (
            <ToolCard
              key={t.key}
              title={t.title}
              desc={t.desc}
              icon={t.icon}
              gradient={t.gradient}
              delay={0.05 * i}
              loading={m.isPending}
              onClick={() => m.mutate()}
              result={m.data}
            />
          );
        })}
      </div>
    </div>
  );
}

function ToolCard({
  title,
  desc,
  icon,
  gradient,
  delay,
  loading,
  onClick,
  result,
}: {
  title: string;
  desc: string;
  icon: string;
  gradient: string;
  delay: number;
  loading: boolean;
  onClick: () => void;
  result?: Record<string, unknown>;
}) {
  const reduce = useReducedMotion();
  return (
    <GlassCard delay={delay} className="relative overflow-hidden !p-5">
      <div
        className={`pointer-events-none absolute -right-8 -top-8 h-32 w-32 rounded-full bg-gradient-to-br ${gradient} blur-2xl`}
        aria-hidden
      />
      <div className="relative flex flex-col gap-4">
        <div className="flex items-start gap-3">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-muted/80 text-lg text-accent shadow-inner">
            {icon}
          </span>
          <div>
            <h2 className="font-display text-lg font-bold text-foreground">{title}</h2>
            <p className="mt-1 text-sm text-muted-foreground">{desc}</p>
          </div>
        </div>
        <motion.button
          type="button"
          disabled={loading}
          onClick={onClick}
          whileHover={reduce ? undefined : { scale: 1.02 }}
          whileTap={reduce ? undefined : { scale: 0.97 }}
          className="w-fit rounded-2xl border border-border/80 bg-muted/70 px-5 py-2.5 text-sm font-bold text-foreground shadow-soft backdrop-blur-sm hover:border-accent/40 disabled:opacity-45"
        >
          {loading ? "Running…" : "Run"}
        </motion.button>
        {result && (
          <pre className="max-h-36 overflow-auto rounded-2xl border border-border/50 bg-canvas/60 p-3 text-xs text-muted-foreground backdrop-blur-sm">
            {JSON.stringify(result, null, 2)}
          </pre>
        )}
      </div>
    </GlassCard>
  );
}
