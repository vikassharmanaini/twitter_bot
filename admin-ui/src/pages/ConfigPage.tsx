import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion, useReducedMotion } from "framer-motion";
import { useEffect, useState } from "react";
import { GlassCard } from "../components/GlassCard";
import { apiGet, apiSend } from "../lib/api";

type ConfigResponse = {
  config: Record<string, unknown>;
  secret_status: Record<string, boolean>;
};

export default function ConfigPage() {
  const qc = useQueryClient();
  const reduce = useReducedMotion();
  const { data, isLoading, error } = useQuery({
    queryKey: ["config"],
    queryFn: () => apiGet<ConfigResponse>("/api/config"),
  });
  const [text, setText] = useState("");
  const [allowIncomplete, setAllowIncomplete] = useState(false);

  useEffect(() => {
    if (data?.config) setText(JSON.stringify(data.config, null, 2));
  }, [data]);

  const bootstrap = useMutation({
    mutationFn: () => apiSend<{ status: string }>("/api/config/bootstrap", "POST"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["config"] }),
  });

  const save = useMutation({
    mutationFn: async () => {
      const parsed = JSON.parse(text) as Record<string, unknown>;
      const q = allowIncomplete ? "?allow_incomplete=true" : "";
      return apiSend<{ status: string }>(`/api/config${q}`, "PUT", parsed);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["config"] }),
  });

  const err =
    (error as Error)?.message ||
    save.error?.message ||
    bootstrap.error?.message ||
    (save.isError ? "Invalid JSON" : "");

  return (
    <div className="space-y-6 md:space-y-8">
      <motion.header
        initial={reduce ? false : { opacity: 0, y: -6 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between"
      >
        <div>
          <h1 className="font-display text-3xl font-extrabold tracking-tight text-gradient md:text-4xl">
            Configuration
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground md:text-base">
            Edits <code className="rounded-md bg-muted px-1.5 py-0.5 text-accent">config.yaml</code>.
            Secret fields load masked; leave blank on save to keep existing values.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <label className="flex cursor-pointer items-center gap-2 rounded-2xl border border-border/60 bg-card/50 px-3 py-2 text-xs font-medium text-muted-foreground backdrop-blur-sm">
            <input
              type="checkbox"
              checked={allowIncomplete}
              onChange={(e) => setAllowIncomplete(e.target.checked)}
              className="rounded border-border text-accent focus:ring-accent"
            />
            Allow incomplete
          </label>
          <motion.button
            type="button"
            onClick={() => bootstrap.mutate()}
            whileTap={reduce ? undefined : { scale: 0.97 }}
            className="rounded-2xl border border-border/80 bg-muted/60 px-4 py-2.5 text-sm font-semibold text-foreground shadow-soft backdrop-blur-sm hover:border-accent/40"
          >
            Bootstrap
          </motion.button>
          <motion.button
            type="button"
            disabled={save.isPending}
            onClick={() => save.mutate()}
            whileTap={reduce ? undefined : { scale: 0.97 }}
            className="rounded-2xl bg-gradient-to-r from-accent to-accent-secondary px-5 py-2.5 text-sm font-bold text-white shadow-glow disabled:opacity-50"
          >
            Save
          </motion.button>
        </div>
      </motion.header>

      {data?.secret_status && (
        <GlassCard delay={0} hover={false} className="!p-4">
          <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
            Secrets configured
          </span>
          <ul className="mt-3 flex flex-wrap gap-2">
            {Object.entries(data.secret_status).map(([k, v]) => (
              <li
                key={k}
                className={`rounded-full px-3 py-1 text-xs font-semibold transition-colors ${
                  v
                    ? "bg-success/20 text-success ring-1 ring-success/30"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                {k}
              </li>
            ))}
          </ul>
        </GlassCard>
      )}

      {err && (
        <div className="rounded-3xl border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-danger backdrop-blur-md">
          {String(err)}
        </div>
      )}

      {isLoading ? (
        <div className="space-y-3">
          <div className="h-8 w-1/3 animate-pulse rounded-2xl bg-muted" />
          <div className="h-96 animate-pulse rounded-4xl bg-muted/80" />
        </div>
      ) : (
        <textarea
          className="min-h-[420px] w-full rounded-4xl border border-border/60 bg-card/70 p-4 font-mono text-sm text-card-foreground shadow-soft backdrop-blur-xl placeholder:text-muted-foreground focus:border-accent/50 focus:outline-none focus:ring-2 focus:ring-accent/30 md:min-h-[520px] md:p-6"
          value={text}
          onChange={(e) => setText(e.target.value)}
          spellCheck={false}
        />
      )}
    </div>
  );
}
