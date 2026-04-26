import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { apiGet, apiSend } from "../lib/api";

type TargetsResp = { targets: Record<string, unknown>[] };

export default function TargetsPage() {
  const qc = useQueryClient();
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
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-white tracking-tight">Targets</h1>
        <p className="text-slate-400 mt-1 text-sm">Curated accounts from targets.yaml.</p>
      </header>

      {err && (
        <div className="rounded-xl border border-rose-500/40 bg-rose-950/40 px-4 py-3 text-sm text-rose-200">
          {err}
        </div>
      )}

      <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-4 flex flex-wrap gap-2 items-end">
        <div>
          <label className="block text-xs text-slate-500 mb-1">Username</label>
          <input
            className="rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm"
            value={user}
            onChange={(e) => setUser(e.target.value)}
            placeholder="handle"
          />
        </div>
        <div>
          <label className="block text-xs text-slate-500 mb-1">Category</label>
          <input
            className="rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            placeholder="AI"
          />
        </div>
        <button
          type="button"
          disabled={!user || add.isPending}
          onClick={() => add.mutate()}
          className="rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 px-4 py-2 text-sm text-white"
        >
          Add target
        </button>
      </div>

      {isLoading ? (
        <p className="text-slate-500">Loading…</p>
      ) : (
        <div className="rounded-2xl border border-slate-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-900/80 text-left text-slate-400">
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
                <tr key={i} className="border-t border-slate-800">
                  <td className="px-4 py-2 font-mono">@{String(row.username ?? "")}</td>
                  <td className="px-4 py-2">{String(row.category ?? "")}</td>
                  <td className="px-4 py-2">{String(row.priority ?? "")}</td>
                  <td className="px-4 py-2">{String(row.enabled ?? "")}</td>
                  <td className="px-4 py-2 text-right">
                    <button
                      type="button"
                      className="text-rose-300 hover:text-rose-200 text-xs"
                      onClick={() => disable.mutate(String(row.username ?? ""))}
                    >
                      Disable
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
