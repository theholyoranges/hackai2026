"use client";

import clsx from "clsx";
import { Recommendation } from "@/types";

interface RecommendationCardProps {
  recommendation: Recommendation;
  onAccept?: (id: number) => void;
  onReject?: (id: number) => void;
  className?: string;
}

const urgencyColors: Record<string, string> = {
  low: "bg-slate-100 text-slate-700",
  medium: "bg-amber-100 text-amber-700",
  high: "bg-orange-100 text-orange-700",
  critical: "bg-red-100 text-red-700",
};

const confidenceColor = (confidence: number) => {
  if (confidence >= 0.8) return "bg-emerald-100 text-emerald-700";
  if (confidence >= 0.6) return "bg-blue-100 text-blue-700";
  if (confidence >= 0.4) return "bg-amber-100 text-amber-700";
  return "bg-slate-100 text-slate-700";
};

const statusColors: Record<string, string> = {
  pending: "bg-slate-100 text-slate-600",
  accepted: "bg-emerald-100 text-emerald-700",
  rejected: "bg-red-100 text-red-700",
  implemented: "bg-blue-100 text-blue-700",
};

export default function RecommendationCard({
  recommendation,
  onAccept,
  onReject,
  className,
}: RecommendationCardProps) {
  const { id, title, description, confidence, urgency, expected_impact, evidence, status, category } =
    recommendation;

  return (
    <div className={clsx("card", className)}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="badge bg-blue-50 text-blue-700 text-xs">
              {category}
            </span>
            <span className={clsx("badge text-xs", urgencyColors[urgency])}>
              {urgency}
            </span>
            <span className={clsx("badge text-xs", confidenceColor(confidence))}>
              {Math.round(confidence * 100)}% confidence
            </span>
          </div>
          <h3 className="text-base font-semibold text-slate-900">{title}</h3>
        </div>
        <span className={clsx("badge text-xs ml-2", statusColors[status])}>
          {status}
        </span>
      </div>

      {/* Description */}
      <p className="text-sm text-slate-600 mb-3">{description}</p>

      {/* Expected Impact */}
      {expected_impact && (
        <div className="bg-emerald-50 border border-emerald-100 rounded-lg px-3 py-2 mb-3">
          <p className="text-xs font-medium text-emerald-700">
            Expected Impact
          </p>
          <p className="text-sm text-emerald-800">{expected_impact}</p>
        </div>
      )}

      {/* Evidence */}
      {evidence && (
        <div className="bg-slate-50 rounded-lg px-3 py-2 mb-4">
          <p className="text-xs font-medium text-slate-500">Evidence</p>
          <p className="text-sm text-slate-600">{evidence}</p>
        </div>
      )}

      {/* Actions */}
      {status === "pending" && (onAccept || onReject) && (
        <div className="flex items-center gap-2 pt-2 border-t border-slate-100">
          {onAccept && (
            <button
              onClick={() => onAccept(id)}
              className="btn-success text-sm py-1.5 px-3"
            >
              Accept
            </button>
          )}
          {onReject && (
            <button
              onClick={() => onReject(id)}
              className="btn-danger text-sm py-1.5 px-3"
            >
              Reject
            </button>
          )}
        </div>
      )}
    </div>
  );
}
