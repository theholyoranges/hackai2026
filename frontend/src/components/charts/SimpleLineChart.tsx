"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

interface SimpleLineChartProps {
  data: Record<string, unknown>[];
  xKey: string;
  yKey?: string;
  color?: string;
  lines?: {
    dataKey: string;
    color: string;
    name?: string;
  }[];
  title?: string;
  height?: number;
  className?: string;
}

export default function SimpleLineChart({
  data,
  xKey,
  yKey,
  color = "#4f46e5",
  lines,
  title,
  height = 300,
  className,
}: SimpleLineChartProps) {
  const resolvedLines = lines ?? (yKey ? [{ dataKey: yKey, color, name: yKey }] : []);

  return (
    <div className={className}>
      {title && (
        <h3 className="text-sm font-semibold text-slate-700 mb-4">{title}</h3>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
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
          {resolvedLines.length > 1 && <Legend />}
          {resolvedLines.map((line) => (
            <Line
              key={line.dataKey}
              type="monotone"
              dataKey={line.dataKey}
              stroke={line.color}
              name={line.name || line.dataKey}
              strokeWidth={2}
              dot={{ r: 3, fill: line.color }}
              activeDot={{ r: 5 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
