import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { apiGet, apiSend } from "../lib/api";

type ConfigResponse = {
  config: Record<string, unknown>;
  secret_status: Record<string, boolean>;
};

export default function ConfigPage() {
  const qc = useQueryClient();
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
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">Configuration</h1>
          <p className="text-slate-400 mt-1 text-sm">
            Edits <code className="text-indigo-300">config.yaml</code>. Secret fields load empty;
            leave blank to keep existing values on save.
          </p>
        </div>
        <div className="flex flex-wrap gap-2 items-center">
          <label className="flex items-center gap-2 text-xs text-slate-400">
            <input
              type="checkbox"
              checked={allowIncomplete}
              onChange={(e) => setAllowIncomplete(e.target.checked)}
            />
            Allow incomplete (onboarding)
          </label>
          <button
            type="button"
            onClick={() => bootstrap.mutate()}
            className="rounded-lg border border-slate-600 px-3 py-2 text-sm hover:bg-slate-800"
          >
            Bootstrap from example
          </button>
          <button
            type="button"
            disabled={save.isPending}
            onClick={() => save.mutate()}
            className="rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 px-4 py-2 text-sm font-medium text-white"
          >
            Save
          </button>
        </div>
      </header>

      {data?.secret_status && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-4 text-xs text-slate-400">
          <span className="text-slate-500 font-medium uppercase tracking-wide">Secrets set</span>
          <ul className="mt-2 flex flex-wrap gap-2">
            {Object.entries(data.secret_status).map(([k, v]) => (
              <li
                key={k}
                className={`rounded-full px-2 py-0.5 ${v ? "bg-emerald-500/20 text-emerald-200" : "bg-slate-800 text-slate-500"}`}
              >
                {k}
              </li>
            ))}
          </ul>
        </div>
      )}

      {err && (
        <div className="rounded-xl border border-rose-500/40 bg-rose-950/40 px-4 py-3 text-sm text-rose-200">
          {String(err)}
        </div>
      )}

      {isLoading ? (
        <p className="text-slate-500">Loading…</p>
      ) : (
        <textarea
          className="w-full min-h-[480px] rounded-2xl border border-slate-800 bg-slate-950/80 p-4 font-mono text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
          value={text}
          onChange={(e) => setText(e.target.value)}
          spellCheck={false}
        />
      )}
    </div>
  );
}
