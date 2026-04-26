import { useMemo } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useTheme } from "../../context/ThemeContext";
import { GlassCard } from "../GlassCard";

type WeeklyItem = { posted_at?: string; account?: string };

type WeeklyResp = { count?: number; items?: WeeklyItem[] };
type DbResp = { counts?: Record<string, number> };

function aggregateByDay(items: WeeklyItem[]): { day: string; replies: number }[] {
  const labels: string[] = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setUTCDate(d.getUTCDate() - i);
    labels.push(d.toISOString().slice(0, 10));
  }
  const map = new Map(labels.map((d) => [d, 0]));
  for (const it of items) {
    const day = it.posted_at?.slice(0, 10);
    if (day && map.has(day)) map.set(day, (map.get(day) ?? 0) + 1);
  }
  return labels.map((day) => ({
    day: day.slice(5),
    replies: map.get(day) ?? 0,
  }));
}

function chartColors(isDark: boolean) {
  return {
    grid: isDark ? "hsl(240 18% 22% / 0.6)" : "hsl(260 18% 88% / 0.9)",
    axis: isDark ? "hsl(260 12% 55%)" : "hsl(240 10% 45%)",
    tooltipBg: isDark ? "hsl(240 28% 12% / 0.95)" : "hsl(0 0% 100% / 0.95)",
    tooltipBorder: isDark ? "hsl(240 18% 22%)" : "hsl(260 18% 88%)",
    area: isDark ? "hsl(265 88% 68%)" : "hsl(262 83% 58%)",
    area2: isDark ? "hsl(188 78% 52%)" : "hsl(188 85% 42%)",
    bar: isDark ? "hsl(328 78% 62%)" : "hsl(330 82% 58%)",
  };
}

export function DashboardCharts({ weekly, db }: { weekly?: WeeklyResp; db?: DbResp }) {
  const { isDark } = useTheme();
  const c = chartColors(isDark);

  const areaData = useMemo(
    () => aggregateByDay(weekly?.items ?? []),
    [weekly?.items]
  );

  const barData = useMemo(() => {
    const counts = db?.counts ?? {};
    return Object.entries(counts).map(([name, value]) => ({
      name: name.replace(/_/g, " "),
      value: Number(value) || 0,
    }));
  }, [db?.counts]);

  const tooltipStyle = {
    backgroundColor: c.tooltipBg,
    border: `1px solid ${c.tooltipBorder}`,
    borderRadius: "12px",
    fontSize: "12px",
    padding: "8px 12px",
    boxShadow: "0 12px 40px -12px hsl(0 0% 0% / 0.25)",
  };

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <GlassCard delay={0.08} className="min-h-[320px]">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          Replies (7 days)
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Activity from your knowledge store
        </p>
        <div className="mt-4 h-[240px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={areaData} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
              <defs>
                <linearGradient id="fillReplies" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={c.area} stopOpacity={0.45} />
                  <stop offset="100%" stopColor={c.area2} stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 6" stroke={c.grid} vertical={false} />
              <XAxis
                dataKey="day"
                tick={{ fill: c.axis, fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                allowDecimals={false}
                tick={{ fill: c.axis, fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                width={36}
              />
              <Tooltip contentStyle={tooltipStyle} labelStyle={{ color: c.axis }} />
              <Area
                type="monotone"
                dataKey="replies"
                stroke={c.area}
                strokeWidth={2.5}
                fill="url(#fillReplies)"
                animationDuration={900}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </GlassCard>

      <GlassCard delay={0.12} className="min-h-[320px]">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          Database tables
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">Row counts by table</p>
        <div className="mt-4 h-[240px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={barData}
              layout="vertical"
              margin={{ top: 8, right: 16, left: 8, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 6" stroke={c.grid} horizontal={false} />
              <XAxis type="number" tick={{ fill: c.axis, fontSize: 11 }} axisLine={false} />
              <YAxis
                type="category"
                dataKey="name"
                width={100}
                tick={{ fill: c.axis, fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar
                dataKey="value"
                fill={c.bar}
                radius={[0, 8, 8, 0]}
                animationDuration={800}
                maxBarSize={28}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </GlassCard>
    </div>
  );
}
