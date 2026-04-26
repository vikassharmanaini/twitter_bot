import { motion, useReducedMotion } from "framer-motion";
import { GlassCard } from "../components/GlassCard";
import { GuideSection, TerminalGuide } from "../components/TerminalGuide";

const cliRows: [string, string][] = [
  ["Bootstrap / validate", "python bot.py bootstrap --config config.yaml"],
  ["Start scheduler loop", "python bot.py start --config config.yaml"],
  ["One cycle (no post)", "python bot.py dry-run --config config.yaml"],
  ["Pause", "python bot.py stop --config config.yaml"],
  ["Resume", "python bot.py resume --config config.yaml"],
  ["Status", "python bot.py status --config config.yaml"],
  ["Add target", 'python bot.py add-target Handle --category "AI" --config config.yaml'],
  ["Disable target", "python bot.py remove-target Handle --config config.yaml"],
  ["Weekly stats", "python bot.py stats --config config.yaml"],
  ["HTML report", "python bot.py report --out report.html --config config.yaml"],
];

export default function InstructionsPage() {
  const reduce = useReducedMotion();

  return (
    <div className="space-y-14 md:space-y-20 lg:space-y-24">
      <motion.header
        initial={reduce ? false : { opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-4xl border border-border/50 bg-gradient-to-br from-accent/15 via-card/80 to-accent-secondary/10 p-6 shadow-soft-lg backdrop-blur-xl sm:p-8 md:p-10"
      >
        <div
          className="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full bg-accent/20 blur-3xl"
          aria-hidden
        />
        <div
          className="pointer-events-none absolute -bottom-16 -left-16 h-48 w-48 rounded-full bg-accent-secondary/15 blur-3xl"
          aria-hidden
        />
        <p className="relative text-[10px] font-bold uppercase tracking-[0.25em] text-muted-foreground">
          Getting started
        </p>
        <h1 className="relative mt-3 font-display text-3xl font-extrabold tracking-tight text-gradient sm:text-4xl md:text-5xl">
          Instructions & terminal guide
        </h1>
        <p className="relative mt-4 max-w-3xl text-sm leading-relaxed text-muted-foreground sm:text-base">
          Run everything from zero to a live admin panel: Python env, config, bot CLI, and this UI.
          Each step has a <strong className="text-foreground">GitHub-style terminal</strong> you can
          copy into your shell. On other pages, use the floating <strong className="text-foreground">Guide</strong>{" "}
          button to return here anytime.
        </p>
      </motion.header>

      <div className="space-y-16 md:space-y-20">
        <GuideSection
          step={1}
          title="Python environment"
          description="Use a virtual environment so dependencies stay isolated. On Windows, activate with .venv\\Scripts\\activate."
        >
          <TerminalGuide
            step={1}
            title="venv + pip"
            lines={[
              { type: "comment", text: "# From repository root" },
              { type: "cmd", text: "python3 -m venv .venv" },
              { type: "cmd", text: "source .venv/bin/activate" },
              { type: "out", text: "# Windows PowerShell: .venv\\Scripts\\Activate.ps1" },
              { type: "cmd", text: "pip install -r requirements.txt" },
            ]}
          />
          <p className="mt-3 text-xs text-muted-foreground">
            Shortcut: <code className="rounded bg-muted px-1 font-mono">bash dev.sh setup</code>
          </p>
        </GuideSection>

        <GuideSection
          step={2}
          title="Configuration & targets"
          description="Never commit real secrets. Copy the example file, fill API keys, then list accounts to watch."
        >
          <TerminalGuide
            step={2}
            title="config + targets"
            lines={[
              { type: "comment", text: "# Copy template → edit with your keys" },
              { type: "cmd", text: "cp config.example.yaml config.yaml" },
              { type: "comment", text: "# Edit data/targets.yaml (handles to monitor)" },
              { type: "cmd", text: "# use your editor, e.g. nano data/targets.yaml" },
            ]}
          />
        </GuideSection>

        <GuideSection
          step={3}
          title="Verify with bootstrap"
          description="Confirms YAML loads and services can initialize (no full cycle yet)."
        >
          <TerminalGuide
            step={3}
            title="bootstrap"
            lines={[
              { type: "comment", text: "# Validate config (adjust path if needed)" },
              { type: "cmd", text: "python bot.py bootstrap --config config.yaml" },
            ]}
          />
        </GuideSection>

        <GuideSection
          step={4}
          title="Safe dry-run"
          description="Runs one cycle without posting. Prefer this until safety settings look right."
        >
          <TerminalGuide
            step={4}
            title="dry-run"
            lines={[
              { type: "cmd", text: "python bot.py dry-run --config config.yaml" },
              { type: "comment", text: "# Or: set bot.dry_run: true in config.yaml" },
            ]}
          />
        </GuideSection>

        <GuideSection
          step={5}
          title="Start the admin API (this panel)"
          description="Backend listens on 127.0.0.1:8080 by default. Build the SPA once so the same URL serves the UI."
        >
          <TerminalGuide
            step={5}
            title="run_admin + UI build"
            lines={[
              { type: "comment", text: "# Terminal A — API + WebSocket" },
              { type: "cmd", text: "source .venv/bin/activate && python run_admin.py" },
              { type: "comment", text: "# One-time: production-style single URL" },
              { type: "cmd", text: "cd admin-ui && npm ci && npm run build && cd .." },
              { type: "comment", text: "# Then open http://127.0.0.1:8080/  (restart run_admin if needed)" },
              { type: "comment", text: "# Dev: Terminal B → cd admin-ui && npm run dev  (proxies to 8080)" },
            ]}
          />
        </GuideSection>

        <GuideSection
          step={6}
          title="Optional: dev.sh helper"
          description="One script for setup, tests, bot commands, and admin from repo root."
        >
          <TerminalGuide
            step={6}
            title="dev.sh"
            lines={[
              { type: "cmd", text: "bash dev.sh help" },
              { type: "cmd", text: "bash dev.sh setup" },
              { type: "cmd", text: "bash dev.sh test" },
              { type: "cmd", text: "bash dev.sh admin" },
              { type: "cmd", text: "bash dev.sh admin-build" },
            ]}
          />
        </GuideSection>
      </div>

      <GlassCard delay={0} hover={false} className="!p-6 md:!p-8">
        <h2 className="font-display text-xl font-bold text-foreground md:text-2xl">
          Using this admin UI
        </h2>
        <ul className="mt-4 space-y-3 text-sm text-muted-foreground">
          <li className="flex gap-3">
            <span className="font-bold text-accent">•</span>
            <span>
              <strong className="text-foreground">Dashboard</strong> — runtime status, charts, start /
              stop / pause / resume / dry-run.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="font-bold text-accent-secondary">•</span>
            <span>
              <strong className="text-foreground">Configuration</strong> — edit YAML as JSON; secrets
              are masked on load; use Bootstrap if config is missing.
            </span>
          </li>
          <li className="flex gap-3">
            <span className="font-bold text-accent-tertiary">•</span>
            <span>
              <strong className="text-foreground">Activity</strong> — live logs via WebSocket (redacted).
            </span>
          </li>
          <li className="flex gap-3">
            <span className="font-bold text-success">•</span>
            <span>
              <strong className="text-foreground">Settings</strong> — if the server sets{" "}
              <code className="rounded bg-muted px-1 font-mono text-xs">ADMIN_TOKEN</code>, paste it here
              for API + WS auth.
            </span>
          </li>
        </ul>
      </GlassCard>

      <GlassCard delay={0.05} hover={false} className="!p-0 overflow-hidden">
        <div className="border-b border-border/50 bg-muted/30 px-5 py-4 backdrop-blur-sm">
          <h2 className="font-display text-lg font-bold text-foreground md:text-xl">
            CLI quick reference
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">
            All paths use <code className="font-mono">config.yaml</code>; change with{" "}
            <code className="font-mono">--config</code>.
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[600px] text-left text-sm">
            <thead>
              <tr className="border-b border-border/50 bg-card/50 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                <th className="px-5 py-3">Action</th>
                <th className="px-5 py-3">Command</th>
              </tr>
            </thead>
            <tbody>
              {cliRows.map(([action, cmd]) => (
                <tr
                  key={action}
                  className="border-b border-border/30 transition-colors hover:bg-muted/20"
                >
                  <td className="px-5 py-3 font-medium text-foreground">{action}</td>
                  <td className="px-5 py-3 font-mono text-xs text-accent sm:text-[13px]">{cmd}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </GlassCard>

      <div className="grid gap-6 md:grid-cols-2">
        <GlassCard delay={0.08} hover={false}>
          <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">
            Admin environment
          </h3>
          <ul className="mt-4 space-y-2 font-mono text-xs text-muted-foreground sm:text-sm">
            <li>
              <span className="text-accent">ADMIN_BIND</span> — default{" "}
              <span className="text-card-foreground">127.0.0.1</span>
            </li>
            <li>
              <span className="text-accent">ADMIN_PORT</span> — default{" "}
              <span className="text-card-foreground">8080</span>
            </li>
            <li>
              <span className="text-accent">ADMIN_TOKEN</span> — optional Bearer + WS{" "}
              <span className="text-card-foreground">?token=</span>
            </li>
            <li>
              <span className="text-accent">BOT_CONFIG</span> — path to yaml (admin + CLI)
            </li>
          </ul>
        </GlassCard>
        <GlassCard delay={0.1} hover={false}>
          <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">
            Troubleshooting
          </h3>
          <ul className="mt-4 list-inside list-disc space-y-2 text-sm text-muted-foreground">
            <li>Config errors → compare with <code className="font-mono">config.example.yaml</code>.</li>
            <li>UI 404 in prod → run <code className="font-mono">npm run build</code> in admin-ui.</li>
            <li>401 on API → set token in Settings or unset server ADMIN_TOKEN for local-only.</li>
            <li>Stale pytest coverage → <code className="font-mono">rm -f .coverage && pytest</code>.</li>
          </ul>
        </GlassCard>
      </div>

      <p className="pb-8 text-center text-xs text-muted-foreground">
        Automating X may violate platform rules. Use allowed accounts, rate limits, and dry-run until you
        trust behaviour.
      </p>
    </div>
  );
}
