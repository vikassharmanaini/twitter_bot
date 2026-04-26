import { useState } from "react";
import { getToken, setToken } from "../lib/api";

export default function SettingsPage() {
  const [t, setT] = useState(getToken());

  return (
    <div className="space-y-6 max-w-lg">
      <header>
        <h1 className="text-2xl font-semibold text-white tracking-tight">Settings</h1>
        <p className="text-slate-400 mt-1 text-sm">
          Optional <code className="text-indigo-300">ADMIN_TOKEN</code>. Stored in browser localStorage
          as Bearer token for API and WebSocket.
        </p>
      </header>
      <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 space-y-3">
        <label className="block text-xs text-slate-500">Admin token</label>
        <input
          type="password"
          className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm"
          value={t}
          onChange={(e) => setT(e.target.value)}
          placeholder="paste token if ADMIN_TOKEN is set on server"
        />
        <button
          type="button"
          onClick={() => setToken(t)}
          className="rounded-lg bg-indigo-600 hover:bg-indigo-500 px-4 py-2 text-sm text-white"
        >
          Save token
        </button>
        <button
          type="button"
          onClick={() => {
            setToken("");
            setT("");
          }}
          className="ml-2 rounded-lg border border-slate-600 px-4 py-2 text-sm text-slate-300"
        >
          Clear
        </button>
      </div>
    </div>
  );
}
