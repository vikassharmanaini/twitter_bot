import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiSend } from "../lib/api";

type Status = Record<string, unknown>;

export default function Dashboard() {
  const qc = useQueryClient();
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["status"],
    queryFn: () => apiGet<Status>("/api/runtime/status"),
    refetchInterval: 5000,
  });

  const invalidate = () => qc.invalidateQueries({ queryKey: ["status"] });

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

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-semibold text-white tracking-tight">Dashboard</h1>
        <p className="text-slate-400 mt-1 text-sm">
          Live status, scheduler, and one-click controls.
        </p>
      </header>

      {err && (
        <div className="rounded-xl border border-rose-500/40 bg-rose-950/40 px-4 py-3 text-sm text-rose-200">
          {err}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 shadow-soft">
          <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wide">
            Runtime
          </h2>
          {isLoading ? (
            <p className="mt-4 text-slate-500">Loading…</p>
          ) : (
            <dl className="mt-4 space-y-2 text-sm">
              {Object.entries(data ?? {}).map(([k, v]) => (
                <div key={k} className="flex justify-between gap-4">
                  <dt className="text-slate-500">{k}</dt>
                  <dd className="text-slate-200 font-mono text-right truncate max-w-[60%]">
                    {typeof v === "object" ? JSON.stringify(v) : String(v)}
                  </dd>
                </div>
              ))}
            </dl>
          )}
          <button
            type="button"
            onClick={() => refetch()}
            className="mt-4 text-xs text-indigo-300 hover:text-indigo-200"
          >
            Refresh now
          </button>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 shadow-soft">
          <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wide">
            Actions
          </h2>
          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="button"
              disabled={start.isPending}
              onClick={() => start.mutate()}
              className="rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 px-4 py-2 text-sm font-medium text-white transition"
            >
              Start loop
            </button>
            <button
              type="button"
              disabled={stop.isPending}
              onClick={() => stop.mutate()}
              className="rounded-lg bg-rose-600 hover:bg-rose-500 disabled:opacity-50 px-4 py-2 text-sm font-medium text-white transition"
            >
              Stop
            </button>
            <button
              type="button"
              disabled={pause.isPending}
              onClick={() => pause.mutate()}
              className="rounded-lg bg-amber-600 hover:bg-amber-500 disabled:opacity-50 px-4 py-2 text-sm font-medium text-white transition"
            >
              Pause
            </button>
            <button
              type="button"
              disabled={resume.isPending}
              onClick={() => resume.mutate()}
              className="rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-50 px-4 py-2 text-sm font-medium text-white transition"
            >
              Resume
            </button>
            <button
              type="button"
              disabled={dryRun.isPending}
              onClick={() => dryRun.mutate()}
              className="rounded-lg border border-slate-600 hover:bg-slate-800 disabled:opacity-50 px-4 py-2 text-sm font-medium text-slate-100 transition"
            >
              Dry-run once
            </button>
          </div>
          {dryRun.isSuccess && dryRun.data && (
            <pre className="mt-4 max-h-48 overflow-auto rounded-lg bg-slate-950 p-3 text-xs text-slate-300">
              {JSON.stringify(dryRun.data, null, 2)}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}
