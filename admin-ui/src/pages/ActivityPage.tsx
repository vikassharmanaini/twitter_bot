import { useEffect, useRef, useState } from "react";
import { connectEvents } from "../lib/ws";

type LogEvt = {
  type?: string;
  ts?: string;
  level?: string;
  message?: string;
  metadata?: unknown;
};

export default function ActivityPage() {
  const [lines, setLines] = useState<LogEvt[]>([]);
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ws = connectEvents((raw) => {
      const e = raw as LogEvt;
      setLines((prev) => {
        const next = [...prev, e];
        return next.slice(-500);
      });
    });
    return () => ws.close();
  }, []);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  return (
    <div className="space-y-4 h-[calc(100vh-8rem)] flex flex-col">
      <header>
        <h1 className="text-2xl font-semibold text-white tracking-tight">Activity</h1>
        <p className="text-slate-400 mt-1 text-sm">Live logs and status events (WebSocket).</p>
      </header>
      <div className="flex-1 overflow-auto rounded-2xl border border-slate-800 bg-slate-950/80 p-4 font-mono text-xs">
        {lines.map((e, i) => {
          const row = e as LogEvt & { data?: unknown };
          if (row.type === "status") {
            return (
              <div key={i} className="border-b border-slate-800/50 py-1 text-amber-200/90">
                [status] {JSON.stringify(row.data)}
              </div>
            );
          }
          return (
            <div
              key={i}
              className={`border-b border-slate-800/50 py-1 ${
                e.level === "ERROR" ? "text-rose-300" : "text-slate-300"
              }`}
            >
              <span className="text-slate-500">{e.ts}</span>{" "}
              <span className="text-indigo-300">{e.level}</span> {e.message}{" "}
              {e.metadata !== undefined && (
                <span className="text-slate-500">{JSON.stringify(e.metadata)}</span>
              )}
            </div>
          );
        })}
        <div ref={bottom} />
      </div>
    </div>
  );
}
