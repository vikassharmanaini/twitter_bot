import { useMutation } from "@tanstack/react-query";
import { apiSend } from "../lib/api";

export default function ToolsPage() {
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
    mutationFn: () => apiSend<Record<string, unknown>>("/api/jobs/report", "POST", { out: "report.html" }),
  });

  const err =
    ku.error?.message || perf.error?.message || sug.error?.message || rep.error?.message;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-white tracking-tight">Tools</h1>
        <p className="text-slate-400 mt-1 text-sm">
          Maintenance jobs (same as CLI). Requires valid API credentials in config.
        </p>
      </header>

      {err && (
        <div className="rounded-xl border border-rose-500/40 bg-rose-950/40 px-4 py-3 text-sm text-rose-200">
          {err}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <ToolCard
          title="Knowledge update"
          desc="Refresh knowledge_snippets from hot topics."
          loading={ku.isPending}
          onClick={() => ku.mutate()}
          result={ku.data}
        />
        <ToolCard
          title="Performance analysis"
          desc="Writes data/performance_insights.md"
          loading={perf.isPending}
          onClick={() => perf.mutate()}
          result={perf.data}
        />
        <ToolCard
          title="Suggest targets"
          desc="Writes data/suggested_targets.md"
          loading={sug.isPending}
          onClick={() => sug.mutate()}
          result={sug.data}
        />
        <ToolCard
          title="HTML report"
          desc="Generates report.html"
          loading={rep.isPending}
          onClick={() => rep.mutate()}
          result={rep.data}
        />
      </div>
    </div>
  );
}

function ToolCard({
  title,
  desc,
  loading,
  onClick,
  result,
}: {
  title: string;
  desc: string;
  loading: boolean;
  onClick: () => void;
  result?: Record<string, unknown>;
}) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 shadow-soft flex flex-col gap-3">
      <div>
        <h2 className="text-white font-medium">{title}</h2>
        <p className="text-slate-500 text-sm mt-1">{desc}</p>
      </div>
      <button
        type="button"
        disabled={loading}
        onClick={onClick}
        className="rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-50 px-4 py-2 text-sm text-slate-100 w-fit"
      >
        Run
      </button>
      {result && (
        <pre className="text-xs bg-slate-950 rounded-lg p-2 overflow-auto max-h-32 text-slate-300">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}
