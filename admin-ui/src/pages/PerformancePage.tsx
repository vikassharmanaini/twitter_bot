import { useQuery } from "@tanstack/react-query";
import { motion, useReducedMotion } from "framer-motion";
import { lazy, Suspense } from "react";
import { Link } from "react-router-dom";
import { GlassCard } from "../components/GlassCard";
import type { DailyRow } from "../components/charts/PerformanceCharts";
import { apiGet } from "../lib/api";

const PerformanceCharts = lazy(async () => {
  const m = await import("../components/charts/PerformanceCharts");
  return { default: m.PerformanceCharts };
});

type RecentReply = {
  tweet_id: string;
  account: string;
  reply_text: string;
  posted_at: string;
  engagement_score?: number | null;
  engagement_received?: Record<string, unknown> | null;
};

type PerformancePayload = {
  daily: DailyRow[];
  replies_by_account_week: Record<string, number>;
  weekly_reply_count: number;
  recent_replies: RecentReply[];
};

function formatEngagement(rec: Record<string, unknown> | null | undefined): string {
  if (!rec || Object.keys(rec).length === 0) return "—";
  const parts: string[] = [];
  const keys = [
    "like_count",
    "retweet_count",
    "reply_count",
    "quote_count",
    "impression_count",
    "bookmark_count",
  ];
  for (const k of keys) {
    if (k in rec && rec[k] != null) parts.push(`${k.replace(/_count/g, "")}: ${String(rec[k])}`);
  }
  if (parts.length) return parts.join(" · ");
  return Object.entries(rec)
    .slice(0, 4)
    .map(([k, v]) => `${k}: ${String(v)}`)
    .join(" · ");
}

function tweetUrl(id: string) {
  return `https://x.com/i/web/status/${encodeURIComponent(id)}`;
}

export default function PerformancePage() {
  const reduce = useReducedMotion();
  const { data, isLoading, error } = useQuery({
    queryKey: ["performance-stats"],
    queryFn: () => apiGet<PerformancePayload>("/api/stats/performance"),
    refetchInterval: 120_000,
  });

  const err = (error as Error)?.message;

  return (
    <div className="space-y-8 md:space-y-10">
      <motion.header
        initial={reduce ? false : { opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between"
      >
        <div>
          <h1 className="font-display text-3xl font-extrabold tracking-tight text-gradient md:text-4xl">
            Performance & engagement
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground md:text-base">
            Aggregates from your SQLite store: daily bot totals, reply distribution by account, and
            per-reply engagement when the bot has stored metrics (
            <code className="rounded bg-muted px-1 text-xs">engagement_received</code>).
          </p>
        </div>
        <Link
          to="/tools"
          className="inline-flex w-fit items-center rounded-2xl border border-border/60 bg-muted/50 px-4 py-2.5 text-sm font-semibold text-foreground backdrop-blur-sm transition hover:border-accent/40"
        >
          Run analysis job →
        </Link>
      </motion.header>

      {err && (
        <div className="rounded-3xl border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-danger">
          {err}
        </div>
      )}

      {isLoading || !data ? (
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="h-[300px] animate-pulse rounded-4xl bg-muted/60" />
          <div className="h-[300px] animate-pulse rounded-4xl bg-muted/60" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            {[
              { label: "Replies (7d)", value: String(data.weekly_reply_count), c: "text-accent" },
              {
                label: "Days of stats",
                value: String(data.daily.length),
                c: "text-accent-secondary",
              },
              {
                label: "Accounts (7d)",
                value: String(Object.keys(data.replies_by_account_week).length),
                c: "text-accent-tertiary",
              },
              {
                label: "Recent rows",
                value: String(data.recent_replies.length),
                c: "text-success",
              },
            ].map((s, i) => (
              <motion.div
                key={s.label}
                initial={reduce ? false : { opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: reduce ? 0 : 0.04 * i }}
                className="rounded-3xl border border-border/60 bg-card/60 p-4 shadow-soft backdrop-blur-md"
              >
                <div className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                  {s.label}
                </div>
                <div className={`mt-2 font-mono text-2xl font-bold ${s.c}`}>{s.value}</div>
              </motion.div>
            ))}
          </div>

          <Suspense
            fallback={
              <div className="grid gap-6 lg:grid-cols-2">
                <div className="h-[300px] animate-pulse rounded-4xl bg-muted/60" />
                <div className="h-[300px] animate-pulse rounded-4xl bg-muted/60" />
              </div>
            }
          >
            <PerformanceCharts daily={data.daily} byAccount={data.replies_by_account_week} />
          </Suspense>

          <GlassCard delay={0} hover={false} className="!p-0 overflow-hidden">
            <div className="border-b border-border/50 bg-muted/30 px-5 py-4">
              <h2 className="font-display text-lg font-bold text-foreground">Recent replies & metrics</h2>
              <p className="mt-1 text-xs text-muted-foreground">
                Open a post on X · Engagement fills when your pipeline stores API metrics on the reply tweet
              </p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] text-left text-sm">
                <thead>
                  <tr className="border-b border-border/50 bg-card/50 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                    <th className="px-4 py-3">When</th>
                    <th className="px-4 py-3">Account</th>
                    <th className="px-4 py-3">Reply</th>
                    <th className="px-4 py-3">Score</th>
                    <th className="px-4 py-3">Engagement</th>
                    <th className="px-4 py-3">Post</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_replies.map((row, i) => (
                    <motion.tr
                      key={`${row.tweet_id}-${i}`}
                      initial={reduce ? false : { opacity: 0, x: -6 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: reduce ? 0 : 0.015 * Math.min(i, 20) }}
                      className="border-b border-border/30 transition-colors hover:bg-muted/25"
                    >
                      <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-muted-foreground">
                        {row.posted_at?.slice(0, 16) ?? "—"}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-accent">
                        @{String(row.account ?? "").replace(/^@/, "")}
                      </td>
                      <td className="max-w-xs truncate px-4 py-3 text-card-foreground" title={row.reply_text}>
                        {row.reply_text}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs">
                        {row.engagement_score != null ? String(row.engagement_score) : "—"}
                      </td>
                      <td className="max-w-[200px] truncate px-4 py-3 text-xs text-muted-foreground">
                        {formatEngagement(row.engagement_received ?? undefined)}
                      </td>
                      <td className="px-4 py-3">
                        <a
                          href={tweetUrl(row.tweet_id)}
                          target="_blank"
                          rel="noreferrer"
                          className="text-xs font-semibold text-accent-secondary hover:underline"
                        >
                          View
                        </a>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </GlassCard>
        </>
      )}
    </div>
  );
}
