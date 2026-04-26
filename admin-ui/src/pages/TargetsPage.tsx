import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion, useReducedMotion } from "framer-motion";
import { useState } from "react";
import { GlassCard } from "../components/GlassCard";
import { apiGet, apiSend } from "../lib/api";

type TargetsResp = { targets: Record<string, unknown>[] };

export default function TargetsPage() {
  const qc = useQueryClient();
  const reduce = useReducedMotion();
  const { data, isLoading, error } = useQuery({
    queryKey: ["targets"],
    queryFn: () => apiGet<TargetsResp>("/api/targets"),
  });
  const [user, setUser] = useState("");
  const [category, setCategory] = useState("");

  const add = useMutation({
    mutationFn: () =>
      apiSend("/api/targets", "POST", {
        username: user,
        category: category || "General",
        priority: 3,
        enabled: true,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["targets"] });
      setUser("");
    },
  });

  const disable = useMutation({
    mutationFn: (h: string) => apiSend(`/api/targets/${encodeURIComponent(h)}/disable`, "POST"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["targets"] }),
  });

  const err = (error as Error)?.message || add.error?.message;

  return (
    <div className="space-y-6 md:space-y-8">
      <motion.header
        initial={reduce ? false : { opacity: 0, y: -6 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="font-display text-3xl font-extrabold tracking-tight text-gradient md:text-4xl">
          Targets
        </h1>
        <p className="mt-2 text-sm text-muted-foreground md:text-base">
          Curated accounts from <code className="rounded bg-muted px-1">targets.yaml</code>.
        </p>
      </motion.header>

      {err && (
        <div className="rounded-3xl border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-danger">
          {err}
        </div>
      )}

      <GlassCard delay={0.04} className="!p-4 sm:!p-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end">
          <div className="min-w-0 flex-1 sm:max-w-xs">
            <label className="mb-1 block text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
              Username
            </label>
            <input
              className="w-full rounded-2xl border border-border/60 bg-canvas/80 px-4 py-2.5 text-sm text-foreground shadow-inner backdrop-blur-sm focus:border-accent/50 focus:outline-none focus:ring-2 focus:ring-accent/25"
              value={user}
              onChange={(e) => setUser(e.target.value)}
              placeholder="handle"
            />
          </div>
          <div className="min-w-0 flex-1 sm:max-w-xs">
            <label className="mb-1 block text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
              Category
            </label>
            <input
              className="w-full rounded-2xl border border-border/60 bg-canvas/80 px-4 py-2.5 text-sm focus:border-accent/50 focus:outline-none focus:ring-2 focus:ring-accent/25"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder="AI"
            />
          </div>
          <motion.button
            type="button"
            disabled={!user || add.isPending}
            onClick={() => add.mutate()}
            whileTap={reduce ? undefined : { scale: 0.97 }}
            className="rounded-2xl bg-gradient-to-r from-accent to-accent-tertiary px-6 py-2.5 text-sm font-bold text-white shadow-glow disabled:opacity-45"
          >
            Add target
          </motion.button>
        </div>
      </GlassCard>

      {isLoading ? (
        <div className="h-40 animate-pulse rounded-4xl bg-muted/80" />
      ) : (
        <div className="overflow-hidden rounded-4xl border border-border/60 bg-card/50 shadow-soft-lg backdrop-blur-xl">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[520px] text-sm">
              <thead className="bg-muted/50 text-left text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="px-4 py-3">User</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Priority</th>
                  <th className="px-4 py-3">Enabled</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {(data?.targets ?? []).map((row, i) => (
                  <motion.tr
                    key={i}
                    initial={reduce ? false : { opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: reduce ? 0 : 0.03 * Math.min(i, 12) }}
                    className="border-t border-border/40 transition-colors hover:bg-muted/30"
                  >
                    <td className="px-4 py-3 font-mono text-accent">@{String(row.username ?? "")}</td>
                    <td className="px-4 py-3">{String(row.category ?? "")}</td>
                    <td className="px-4 py-3">{String(row.priority ?? "")}</td>
                    <td className="px-4 py-3">{String(row.enabled ?? "")}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        className="text-xs font-semibold text-danger hover:underline"
                        onClick={() => disable.mutate(String(row.username ?? ""))}
                      >
                        Disable
                      </button>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
