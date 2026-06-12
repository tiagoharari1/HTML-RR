import {
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { CHART_COLORS, ChartContainer } from "../lib/chartTheme";

const MESES_ES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"];

interface ChartRow {
  mes: number;
  rr: number;
  budget?: number;
  actuals?: number;
}

interface RrVsBudgetChartProps {
  data: ChartRow[];
}

function fmt(v: number) {
  if (Math.abs(v) >= 1_000_000)
    return "$" + (v / 1_000_000).toLocaleString("es-AR", { maximumFractionDigits: 1 }) + "M";
  if (Math.abs(v) >= 1_000)
    return "$" + (v / 1_000).toLocaleString("es-AR", { maximumFractionDigits: 0 }) + "K";
  return "$" + v.toLocaleString("es-AR");
}

interface TooltipPayload {
  color?: string;
  name?: string;
  value?: number;
}

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: TooltipPayload[];
  label?: number;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div
      className="rounded-xl px-3.5 py-2.5 text-xs shadow-card"
      style={{ background: CHART_COLORS.tooltipBg, border: `1px solid ${CHART_COLORS.tooltipBorder}` }}
    >
      <p className="font-semibold text-primary mb-1.5">{MESES_ES[(label ?? 1) - 1]}</p>
      {payload.map((p, i) => (
        <p key={i} className="font-mono tabular-nums flex items-center gap-2" style={{ color: p.color }}>
          <span className="inline-block w-2 h-2 rounded-full" style={{ background: p.color }} />
          {p.name}: {fmt(p.value ?? 0)}
        </p>
      ))}
    </div>
  );
}

export function RrVsBudgetChart({ data }: RrVsBudgetChartProps) {
  const tickFormatter = (v: number) => MESES_ES[v - 1] ?? v;
  const hasBudget = data.some((d) => d.budget != null);
  const hasActuals = data.some((d) => d.actuals != null);

  return (
    <ChartContainer height={260}>
      <ComposedChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="gradRr" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={CHART_COLORS.primary} stopOpacity={0.28} />
            <stop offset="95%" stopColor={CHART_COLORS.primary} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={CHART_COLORS.grid} vertical={false} />
        <XAxis
          dataKey="mes"
          tickFormatter={tickFormatter}
          tick={{ fontSize: 11, fill: CHART_COLORS.axis }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tickFormatter={(v) => fmt(v)}
          tick={{ fontSize: 11, fill: CHART_COLORS.axis }}
          axisLine={false}
          tickLine={false}
          width={72}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ stroke: CHART_COLORS.grid, strokeWidth: 1 }} />
        <Legend wrapperStyle={{ fontSize: 12, color: CHART_COLORS.axis, paddingTop: 8 }} iconType="circle" />
        <Area
          type="monotone"
          dataKey="rr"
          name="Run Rate"
          stroke={CHART_COLORS.primary}
          strokeWidth={2.5}
          fill="url(#gradRr)"
          dot={false}
          activeDot={{ r: 5, fill: CHART_COLORS.primary, stroke: CHART_COLORS.tooltipBg, strokeWidth: 2 }}
        />
        {hasBudget && (
          <Line
            type="monotone"
            dataKey="budget"
            name="Budget"
            stroke={CHART_COLORS.secondary}
            strokeWidth={1.5}
            strokeDasharray="5 4"
            dot={false}
          />
        )}
        {hasActuals && (
          <Line
            type="monotone"
            dataKey="actuals"
            name="Actuals"
            stroke={CHART_COLORS.positive}
            strokeWidth={2}
            dot={{ r: 3, fill: CHART_COLORS.positive }}
          />
        )}
      </ComposedChart>
    </ChartContainer>
  );
}
