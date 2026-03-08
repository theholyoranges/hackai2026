"use client";

import clsx from "clsx";
import { AlertTriangle, AlertCircle, Info } from "lucide-react";

interface AlertCardProps {
  title: string;
  message: string;
  severity: "warning" | "danger" | "info";
  className?: string;
}

const severityConfig = {
  warning: {
    bg: "bg-amber-50 border-amber-200",
    icon: AlertTriangle,
    iconColor: "text-amber-500",
    titleColor: "text-amber-800",
    textColor: "text-amber-700",
  },
  danger: {
    bg: "bg-red-50 border-red-200",
    icon: AlertCircle,
    iconColor: "text-red-500",
    titleColor: "text-red-800",
    textColor: "text-red-700",
  },
  info: {
    bg: "bg-blue-50 border-blue-200",
    icon: Info,
    iconColor: "text-blue-500",
    titleColor: "text-blue-800",
    textColor: "text-blue-700",
  },
};

export default function AlertCard({
  title,
  message,
  severity,
  className,
}: AlertCardProps) {
  const config = severityConfig[severity];
  const Icon = config.icon;

  return (
    <div
      className={clsx(
        "rounded-xl border p-4 flex items-start gap-3",
        config.bg,
        className
      )}
    >
      <Icon className={clsx("w-5 h-5 flex-shrink-0 mt-0.5", config.iconColor)} />
      <div>
        <h4 className={clsx("text-sm font-semibold", config.titleColor)}>
          {title}
        </h4>
        <p className={clsx("text-sm mt-0.5", config.textColor)}>{message}</p>
      </div>
    </div>
  );
}
