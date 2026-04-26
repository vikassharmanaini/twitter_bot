import { motion, useReducedMotion } from "framer-motion";
import { useCallback, useState, type ReactNode } from "react";

type Line = { type: "comment" | "cmd" | "out"; text: string };

type Props = {
  title?: string;
  lines: Line[];
  step?: number;
  className?: string;
};

export function TerminalGuide({ title = "terminal", lines, step, className = "" }: Props) {
  const reduce = useReducedMotion();
  const [copied, setCopied] = useState(false);

  const commandsOnly = lines
    .filter((l) => l.type === "cmd")
    .map((l) => l.text)
    .join("\n");

  const copyCommands = useCallback(() => {
    void navigator.clipboard.writeText(commandsOnly);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [commandsOnly]);

  const copyAllAnnotated = useCallback(() => {
    const text = lines
      .map((l) =>
        l.type === "comment" ? l.text : l.type === "cmd" ? `$ ${l.text}` : l.text
      )
      .join("\n");
    void navigator.clipboard.writeText(text);
  }, [lines]);

  return (
    <motion.div
      initial={reduce ? false : { opacity: 0, y: 10 }}
      whileInView={reduce ? undefined : { opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
      className={`overflow-hidden rounded-3xl border border-border/50 bg-[#0d1117] shadow-[0_20px_50px_-20px_rgba(0,0,0,0.5),inset_0_1px_0_0_rgba(255,255,255,0.06)] ring-1 ring-white/5 ${className}`}
    >
      {/* Title bar */}
      <div className="flex items-center justify-between gap-3 border-b border-white/10 bg-[#161b22] px-4 py-2.5">
        <div className="flex items-center gap-2">
          <span className="flex gap-1.5" aria-hidden>
            <span className="h-3 w-3 rounded-full bg-[#ff5f57]" />
            <span className="h-3 w-3 rounded-full bg-[#febc2e]" />
            <span className="h-3 w-3 rounded-full bg-[#28c840]" />
          </span>
          <span className="ml-2 truncate font-mono text-[11px] text-white/45">
            {step != null ? `step-${step} — ${title}` : title}
          </span>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <button
            type="button"
            onClick={copyAllAnnotated}
            className="rounded-lg border border-white/10 bg-white/5 px-2.5 py-1 font-mono text-[10px] font-semibold uppercase tracking-wider text-[#8b949e] transition hover:bg-white/10"
            title="Copy full snippet (with comments)"
          >
            Copy all
          </button>
          <button
            type="button"
            onClick={copyCommands}
            className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 font-mono text-[10px] font-semibold uppercase tracking-wider text-emerald-300 transition hover:bg-emerald-500/20"
          >
            {copied ? "Copied ✓" : "Commands"}
          </button>
        </div>
      </div>
      {/* Body */}
      <div className="max-h-[min(420px,55vh)] overflow-auto p-4 font-mono text-[13px] leading-relaxed sm:text-sm sm:leading-relaxed">
        {lines.map((line, i) => (
          <div key={i} className="whitespace-pre-wrap break-all">
            {line.type === "comment" && (
              <span className="text-[#8b949e]">{line.text}</span>
            )}
            {line.type === "cmd" && (
              <>
                <span className="select-none text-[#58a6ff]">❯ </span>
                <span className="text-[#79c0ff]">{line.text}</span>
              </>
            )}
            {line.type === "out" && (
              <span className="text-[#7ee787]/90">{line.text}</span>
            )}
          </div>
        ))}
      </div>
    </motion.div>
  );
}

export function GuideSection({
  step,
  title,
  description,
  children,
}: {
  step: number;
  title: string;
  description: string;
  children: ReactNode;
}) {
  const reduce = useReducedMotion();
  return (
    <motion.section
      initial={reduce ? false : { opacity: 0, y: 16 }}
      whileInView={reduce ? undefined : { opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.45 }}
      className="grid gap-5 md:grid-cols-[auto_1fr] md:gap-8"
    >
      <div className="flex md:flex-col md:items-start md:gap-2">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-accent/30 via-accent-secondary/25 to-accent-tertiary/20 text-lg font-black text-foreground shadow-glow ring-1 ring-accent/20">
          {step}
        </div>
        <div className="ml-4 md:ml-0 md:mt-0">
          <h2 className="font-display text-xl font-bold text-foreground md:text-2xl">{title}</h2>
          <p className="mt-1 max-w-prose text-sm text-muted-foreground">{description}</p>
        </div>
      </div>
      <div className="min-w-0 md:pt-1">{children}</div>
    </motion.section>
  );
}
