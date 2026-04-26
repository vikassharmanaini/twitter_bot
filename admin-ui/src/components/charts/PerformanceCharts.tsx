import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useTheme } from "../../context/ThemeContext";
import { GlassCard } from "../GlassCard";

export type DailyRow = {
  date: string;
  replies_posted: number;
  accounts_checked: number;
  tokens_used: number;
  errors: number;
};

function chartColors(isDark: boolean) {
  return {
    grid: isDark ? "hsl(240 18% 22% / 0.6)" : "hsl(260 18% 88% / 0.9)",
    axis: isDark ? "hsl(260 12% 55%)" : "hsl(240 10% 45%)",
    tooltipBg: isDark ? "hsl(240 28% 12% / 0.95)" : "hsl(0 0% 100% / 0.95)",
    tooltipBorder: isDark ? "hsl(240 18% 22%)" : "hsl(260 18% 88%)",
    replies: isDark ? "hsl(265 88% 68%)" : "hsl(262 83% 58%)",
    tokens: isDark ? "hsl(188 78% 55%)" : "hsl(188 85% 42%)",
    errors: isDark ? "hsl(350 78% 58%)" : "hsl(350 82% 52%)",
    accounts: isDark ? "hsl(328 78% 62%)" : "hsl(330 82% 58%)",
    bar: isDark ? "hsl(265 75% 60%)" : "hsl(262 75% 52%)",
  };
}

export function PerformanceCharts({
  daily,
  byAccount,
}: {
  daily: DailyRow[];
  byAccount: Record<string, number>;
}) {
  const { isDark } = useTheme();
  const c = chartColors(isDark);

  const lineData = useMemo(
    () =>
      daily.map((d) => ({
        ...d,
        day: d.date.slice(5),
      })),
    [daily]
  );

  const barData = useMemo(() => {
    return Object.entries(byAccount)
      .map(([name, value]) => ({
        name: name.startsWith("@") ? name : `@${name}`,
        replies: value,
      }))
      .sort((a, b) => b.replies - a.replies)
      .slice(0, 14);
  }, [byAccount]);

  const tooltipStyle = {
    backgroundColor: c.tooltipBg,
    border: `1px solid ${c.tooltipBorder}`,
    borderRadius: "12px",
    fontSize: "12px",
    padding: "8px 12px",
  };

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <GlassCard delay={0.06} className="min-h-[300px]">
        <h2 className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
          Daily activity
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Replies posted, accounts checked, tokens, errors (SQLite{" "}
          <code className="rounded bg-muted px-1 text-[11px]">daily_stats</code>)
        </p>
        <div className="mt-4 h-[260px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={lineData} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 6" stroke={c.grid} />
              <XAxis dataKey="day" tick={{ fill: c.axis, fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis yAxisId="left" tick={{ fill: c.axis, fontSize: 10 }} axisLine={false} width={36} />
              <YAxis
                yAxisId="right"
                orientation="right"
                tick={{ fill: c.axis, fontSize: 10 }}
                axisLine={false}
                width={36}
              />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: "11px" }} />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="replies_posted"
                name="Replies"
                stroke={c.replies}
                strokeWidth={2}
                dot={false}
                animationDuration={700}
              />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="accounts_checked"
                name="Accounts"
                stroke={c.accounts}
                strokeWidth={2}
                dot={false}
                animationDuration={700}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="tokens_used"
                name="Tokens"
                stroke={c.tokens}
                strokeWidth={2}
                dot={false}
                animationDuration={700}
              />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="errors"
                name="Errors"
                stroke={c.errors}
                strokeWidth={2}
                strokeDasharray="4 4"
                dot={false}
                animationDuration={700}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </GlassCard>

      <GlassCard delay={0.1} className="min-h-[300px]">
        <h2 className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
          Replies by account (7 days)
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">Where your bot replied most recently</p>
        <div className="mt-4 h-[260px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={barData}
              layout="vertical"
              margin={{ top: 8, right: 12, left: 4, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 6" stroke={c.grid} horizontal={false} />
              <XAxis type="number" tick={{ fill: c.axis, fontSize: 10 }} axisLine={false} />
              <YAxis
                type="category"
                dataKey="name"
                width={88}
                tick={{ fill: c.axis, fontSize: 10 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="replies" fill={c.bar} radius={[0, 8, 8, 0]} maxBarSize={22} animationDuration={650} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </GlassCard>
    </div>
  );
}
