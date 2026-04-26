import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import ConfigPage from "./pages/ConfigPage";
import ActivityPage from "./pages/ActivityPage";
import TargetsPage from "./pages/TargetsPage";
import ToolsPage from "./pages/ToolsPage";
import SettingsPage from "./pages/SettingsPage";

const navCls = ({ isActive }: { isActive: boolean }) =>
  `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
    isActive
      ? "bg-indigo-500/20 text-indigo-200"
      : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
  }`;

export default function App() {
  return (
    <div className="min-h-screen flex">
      <aside className="w-56 shrink-0 border-r border-slate-800/80 bg-slate-900/50 backdrop-blur-sm p-4 flex flex-col gap-6">
        <div>
          <div className="text-xs uppercase tracking-widest text-slate-500 font-semibold">
            Control
          </div>
          <div className="mt-1 text-lg font-semibold text-white">Twitter Bot</div>
          <p className="text-xs text-slate-500 mt-1">Local admin</p>
        </div>
        <nav className="flex flex-col gap-1">
          <NavLink to="/" end className={navCls}>
            Dashboard
          </NavLink>
          <NavLink to="/config" className={navCls}>
            Configuration
          </NavLink>
          <NavLink to="/targets" className={navCls}>
            Targets
          </NavLink>
          <NavLink to="/activity" className={navCls}>
            Activity
          </NavLink>
          <NavLink to="/tools" className={navCls}>
            Tools
          </NavLink>
          <NavLink to="/settings" className={navCls}>
            Settings
          </NavLink>
        </nav>
      </aside>
      <main className="flex-1 overflow-auto">
        <div className="max-w-6xl mx-auto p-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/config" element={<ConfigPage />} />
            <Route path="/targets" element={<TargetsPage />} />
            <Route path="/activity" element={<ActivityPage />} />
            <Route path="/tools" element={<ToolsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}
