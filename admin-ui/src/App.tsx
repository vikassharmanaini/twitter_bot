import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useState } from "react";
import { NavLink, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { BackgroundOrbs } from "./components/BackgroundOrbs";
import { FloatingInstructionButton } from "./components/FloatingInstructionButton";
import { ThemeToggle } from "./components/ThemeToggle";
import ActivityPage from "./pages/ActivityPage";
import ConfigPage from "./pages/ConfigPage";
import Dashboard from "./pages/Dashboard";
import SettingsPage from "./pages/SettingsPage";
import TargetsPage from "./pages/TargetsPage";
import ToolsPage from "./pages/ToolsPage";
import InstructionsPage from "./pages/InstructionsPage";
import PerformancePage from "./pages/PerformancePage";

const links = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/config", label: "Configuration" },
  { to: "/targets", label: "Targets" },
  { to: "/activity", label: "Activity" },
  { to: "/tools", label: "Tools" },
  { to: "/performance", label: "Performance" },
  { to: "/instructions", label: "Instructions" },
  { to: "/settings", label: "Settings" },
] as const;

/** Bottom bar: floating Guide button replaces a tab; Activity in drawer/sidebar. */
const mobileBarLinks = [
  { to: "/", label: "Home", end: true as const },
  { to: "/config", label: "Config" },
  { to: "/targets", label: "Targets" },
  { to: "/performance", label: "Stats" },
  { to: "/tools", label: "Tools" },
] as const;

function navCls({ isActive }: { isActive: boolean }): string {
  return `group flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-semibold transition-all duration-300 ${
    isActive
      ? "bg-gradient-to-r from-accent/25 via-accent-secondary/15 to-accent-tertiary/20 text-foreground shadow-glow border border-accent/30"
      : "text-muted-foreground hover:bg-muted/80 hover:text-foreground border border-transparent"
  }`;
}

function NavList({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <>
      {links.map(({ to, label, ...rest }) => (
        <NavLink key={to} to={to} className={navCls} onClick={onNavigate} {...rest}>
          <span className="h-2 w-2 rounded-full bg-current opacity-60 group-hover:opacity-100" />
          {label}
        </NavLink>
      ))}
    </>
  );
}

const routeTitles: Record<string, string> = {
  "/": "Dashboard",
  "/config": "Configuration",
  "/targets": "Targets",
  "/activity": "Activity",
  "/tools": "Tools",
  "/performance": "Performance",
  "/instructions": "Instructions",
  "/settings": "Settings",
};

function DesktopAppBar({ pathname }: { pathname: string }) {
  const title = routeTitles[pathname] ?? "Admin";
  return (
    <header className="sticky top-0 z-20 hidden shrink-0 border-b border-border/50 bg-card/55 px-6 py-3 backdrop-blur-xl lg:block xl:px-8">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground">
            Twitter Bot
          </p>
          <h2 className="font-display text-lg font-bold text-foreground">{title}</h2>
        </div>
      </div>
    </header>
  );
}

function MobileBottomNav() {
  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-30 flex border-t border-border/60 bg-card/85 px-0.5 pb-[max(0.5rem,env(safe-area-inset-bottom))] pt-2 backdrop-blur-2xl lg:hidden"
      aria-label="Primary"
    >
      {mobileBarLinks.map(({ to, label, ...rest }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) =>
            `flex min-w-0 flex-1 flex-col items-center justify-center gap-0.5 rounded-lg py-2 text-[10px] font-semibold transition-colors sm:text-xs ${
              isActive ? "text-accent" : "text-muted-foreground"
            }`
          }
          {...rest}
        >
          <span className="truncate px-0.5 text-center">{label}</span>
        </NavLink>
      ))}
      <NavLink
        to="/settings"
        className={({ isActive }) =>
          `flex min-w-0 flex-1 flex-col items-center justify-center gap-0.5 rounded-xl py-2 text-[10px] font-semibold sm:text-xs ${
            isActive ? "text-accent" : "text-muted-foreground"
          }`
        }
      >
        <span className="truncate">More</span>
      </NavLink>
    </nav>
  );
}

export default function App() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const location = useLocation();
  const reduce = useReducedMotion();

  return (
    <div className="relative min-h-screen">
      <BackgroundOrbs />

      {/* Mobile header */}
      <header className="sticky top-0 z-30 flex items-center justify-between gap-3 border-b border-border/50 bg-card/75 px-4 py-3 backdrop-blur-xl lg:hidden">
        <button
          type="button"
          className="flex h-10 w-10 items-center justify-center rounded-xl border border-border/80 bg-muted/50 text-lg"
          onClick={() => setDrawerOpen(true)}
          aria-expanded={drawerOpen}
          aria-label="Open menu"
        >
          ☰
        </button>
        <div className="min-w-0 text-center">
          <div className="truncate font-display text-sm font-bold text-gradient">Twitter Bot</div>
          <div className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground">
            Admin
          </div>
        </div>
        <ThemeToggle />
      </header>

      {/* Drawer overlay */}
      <AnimatePresence>
        {drawerOpen && (
          <motion.button
            type="button"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: reduce ? 0 : 0.2 }}
            className="fixed inset-0 z-40 bg-canvas/60 backdrop-blur-sm lg:hidden"
            aria-label="Close menu"
            onClick={() => setDrawerOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Slide drawer */}
      <AnimatePresence>
        {drawerOpen && (
          <motion.aside
            initial={{ x: reduce ? 0 : -300 }}
            animate={{ x: 0 }}
            exit={{ x: reduce ? 0 : -300 }}
            transition={{ type: "spring", damping: 28, stiffness: 320 }}
            className="fixed inset-y-0 left-0 z-50 flex w-[min(20rem,88vw)] flex-col gap-6 border-r border-border/60 bg-card/95 p-5 shadow-soft-lg backdrop-blur-2xl lg:hidden"
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="font-display text-lg font-bold text-gradient">Twitter Bot</div>
                <p className="text-xs text-muted-foreground">Local admin</p>
              </div>
              <button
                type="button"
                className="rounded-xl border border-border px-3 py-1.5 text-sm text-muted-foreground"
                onClick={() => setDrawerOpen(false)}
              >
                ✕
              </button>
            </div>
            <nav className="flex flex-col gap-1">
              <NavList onNavigate={() => setDrawerOpen(false)} />
            </nav>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Desktop: viewport-tall shell; sidebar fixed height; only main scrolls */}
      <div className="flex min-h-[100dvh] lg:h-[100dvh] lg:max-h-[100dvh] lg:overflow-hidden">
        <aside className="relative hidden h-auto w-64 shrink-0 flex-col overflow-hidden border-r border-border/50 bg-card/40 p-6 backdrop-blur-xl lg:flex lg:h-[100dvh] lg:max-h-[100dvh] xl:w-72">
          <div className="pointer-events-none absolute inset-0 bg-mesh opacity-50" aria-hidden />
          <div className="relative shrink-0">
            <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground">
              Control
            </div>
            <h1 className="mt-2 font-display text-xl font-bold text-gradient">Twitter Bot</h1>
            <p className="mt-1 text-xs text-muted-foreground">Local admin · full visibility</p>
          </div>
          <nav className="relative mt-6 flex min-h-0 flex-1 flex-col gap-1 overflow-x-hidden overflow-y-hidden overscroll-y-contain">
            <NavList />
          </nav>
          <div className="relative mt-4 flex shrink-0 items-center justify-between gap-2 border-t border-border/40 pt-4">
            <ThemeToggle />
            <span className="text-[10px] text-muted-foreground">Theme</span>
          </div>
        </aside>

        <main className="flex min-h-0 min-w-0 flex-1 flex-col pb-20 lg:h-[100dvh] lg:max-h-[100dvh] lg:overflow-hidden lg:pb-0">
          <DesktopAppBar pathname={location.pathname} />
          <div className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden overscroll-y-contain lg:min-h-0">
            <AnimatePresence mode="wait">
              <motion.div
                key={location.pathname}
                initial={reduce ? false : { opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={reduce ? undefined : { opacity: 0, y: -6 }}
                transition={{ duration: reduce ? 0 : 0.28, ease: [0.22, 1, 0.36, 1] }}
              >
                <div className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8 lg:py-10">
                  <Routes location={location}>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/config" element={<ConfigPage />} />
                    <Route path="/targets" element={<TargetsPage />} />
                    <Route path="/activity" element={<ActivityPage />} />
                    <Route path="/tools" element={<ToolsPage />} />
                    <Route path="/performance" element={<PerformancePage />} />
                    <Route path="/instructions" element={<InstructionsPage />} />
                    <Route path="/settings" element={<SettingsPage />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                  </Routes>
                </div>
              </motion.div>
            </AnimatePresence>
          </div>
        </main>
      </div>

      <MobileBottomNav />
      <FloatingInstructionButton />
    </div>
  );
}
