"use client";

import clsx from "clsx";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
  icon?: React.ReactNode;
  className?: string;
}

export default function StatCard({
  title,
  value,
  subtitle,
  trend,
  trendValue,
  icon,
  className,
}: StatCardProps) {
  return (
    <div className={clsx("card", className)}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-slate-500">{title}</p>
          <p className="text-2xl font-bold text-slate-900 mt-1">{value}</p>
          {(subtitle || trendValue) && (
            <div className="flex items-center gap-2 mt-2">
              {trend && (
                <span
                  className={clsx(
                    "flex items-center gap-1 text-xs font-medium",
                    trend === "up" && "text-emerald-600",
                    trend === "down" && "text-red-500",
                    trend === "neutral" && "text-slate-400"
                  )}
                >
                  {trend === "up" && <TrendingUp className="w-3 h-3" />}
                  {trend === "down" && <TrendingDown className="w-3 h-3" />}
                  {trend === "neutral" && <Minus className="w-3 h-3" />}
                  {trendValue}
                </span>
              )}
              {subtitle && (
                <span className="text-xs text-slate-400">{subtitle}</span>
              )}
            </div>
          )}
        </div>
        {icon && (
          <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center text-blue-600">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
