import type { ReactElement } from "react";
import { ResponsiveContainer } from "recharts";

export const CHART_COLORS = {
  primary: "#00E5A0",
  secondary: "#6C63FF",
  tertiary: "#FFD740",
  positive: "#00E676",
  negative: "#FF5252",
  grid: "rgba(255,255,255,0.06)",
  axis: "#4A5568",
  tooltipBg: "#1A2235",
  tooltipBorder: "rgba(255,255,255,0.1)",
  textPrimary: "#F0F4FF",
} as const;

interface ChartContainerProps {
  children: ReactElement;
  height?: number;
}

export function ChartContainer({ children, height = 280 }: ChartContainerProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      {children}
    </ResponsiveContainer>
  );
}
