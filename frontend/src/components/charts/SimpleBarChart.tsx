"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

interface SimpleBarChartProps {
  data: Record<string, unknown>[];
  xKey: string;
  yKey?: string;
  color?: string;
  bars?: {
    dataKey: string;
    color: string;
    name?: string;
  }[];
  title?: string;
  height?: number;
  className?: string;
}

export default function SimpleBarChart({
  data,
  xKey,
  yKey,
  color = "#4f46e5",
  bars,
  title,
  height = 300,
  className,
}: SimpleBarChartProps) {
  const resolvedBars = bars ?? (yKey ? [{ dataKey: yKey, color, name: yKey }] : []);

  return (
    <div className={className}>
      {title && (
        <h3 className="text-sm font-semibold text-slate-700 mb-4">{title}</h3>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey={xKey}
            tick={{ fontSize: 12, fill: "#64748b" }}
            axisLine={{ stroke: "#e2e8f0" }}
          />
          <YAxis
            tick={{ fontSize: 12, fill: "#64748b" }}
            axisLine={{ stroke: "#e2e8f0" }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#fff",
              border: "1px solid #e2e8f0",
              borderRadius: "8px",
              fontSize: "12px",
            }}
          />
          {resolvedBars.length > 1 && <Legend />}
          {resolvedBars.map((bar) => (
            <Bar
              key={bar.dataKey}
              dataKey={bar.dataKey}
              fill={bar.color}
              name={bar.name || bar.dataKey}
              radius={[4, 4, 0, 0]}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
