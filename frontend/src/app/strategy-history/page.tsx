"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Target,
  CheckCircle2,
  XCircle,
  Clock,
  Archive,
  Activity,
  Zap,
  ChevronDown,
  ChevronRight,
  Sparkles,
  TrendingUp,
  Calendar,
  Eye,
  AlertTriangle,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

import { api } from "@/lib/api";
import { useRestaurant } from "@/context/RestaurantContext";

/* ------------------------------------------------------------------ */
/*  Animation variants                                                  */
/* ------------------------------------------------------------------ */
const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.06, duration: 0.4, ease: "easeOut" as const },
  }),
};

const staggerContainer = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.06 } },
};

/* ------------------------------------------------------------------ */
/*  Status config                                                       */
/* ------------------------------------------------------------------ */
const STATUS_CONFIG: Record<string, {
  label: string;
  color: string;
  bgColor: string;
  borderColor: string;
  icon: any;
  dotColor: string;
}> = {
  active: {
    label: "Active",
    color: "text-blue-700",
    bgColor: "bg-blue-50",
    borderColor: "border-blue-200",
    icon: Activity,
    dotColor: "bg-blue-500",
  },
  accepted: {
    label: "Accepted",
    color: "text-indigo-700",
    bgColor: "bg-indigo-50",
    borderColor: "border-indigo-200",
    icon: CheckCircle2,
    dotColor: "bg-indigo-500",
  },
  evaluating: {
    label: "Evaluating",
    color: "text-amber-700",
    bgColor: "bg-amber-50",
    borderColor: "border-amber-200",
    icon: Clock,
    dotColor: "bg-amber-500",
  },
  suggested: {
    label: "Suggested",
    color: "text-slate-600",
    bgColor: "bg-slate-50",
    borderColor: "border-slate-200",
    icon: Sparkles,
    dotColor: "bg-slate-400",
  },
  successful: {
    label: "Successful",
    color: "text-emerald-700",
    bgColor: "bg-emerald-50",
    borderColor: "border-emerald-200",
    icon: CheckCircle2,
    dotColor: "bg-emerald-500",
  },
  failed: {
    label: "Failed",
    color: "text-red-700",
    bgColor: "bg-red-50",
    borderColor: "border-red-200",
    icon: XCircle,
    dotColor: "bg-red-500",
  },
  archived: {
    label: "Archived",
    color: "text-slate-500",
    bgColor: "bg-slate-50",
    borderColor: "border-slate-200",
    icon: Archive,
    dotColor: "bg-slate-400",
  },
};

const FILTER_TABS = [
  { key: "All", label: "All" },
  { key: "active", label: "Active" },
  { key: "evaluating", label: "In Review" },
  { key: "successful", label: "Successful" },
  { key: "failed", label: "Failed" },
  { key: "archived", label: "Archived" },
];

/* ------------------------------------------------------------------ */
/*  Helpers                                                             */
/* ------------------------------------------------------------------ */
function formatDate(d: string | null | undefined): string {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function formatRelative(d: string | null | undefined): string {
  if (!d) return "";
  const diff = Math.floor((Date.now() - new Date(d).getTime()) / 86400000);
  if (diff === 0) return "Today";
  if (diff === 1) return "Yesterday";
  if (diff < 7) return `${diff} days ago`;
  if (diff < 30) return `${Math.floor(diff / 7)} weeks ago`;
  return formatDate(d);
}

function getSourceLabel(evidence: any): string | null {
  if (!evidence) return null;
  if (evidence.adopted_from === "menu_insights") return "Menu Insights";
  if (evidence.adopted_from === "recommendation") return "Recommendations";
  if (evidence.recommendation_id) return "Recommendations";
  return null;
}

function getEvidenceSummary(s: any): string {
  if (s.actual_impact) return s.actual_impact;
  if (s.notes) return s.notes;
  const ev = s.evidence;
  if (!ev) return "";
  if (ev.original_title) return ev.original_title;
  return "";
}

function getOutcomeMessage(s: any): { text: string; color: string } {
  const status = s.status;
  if (status === "successful") return { text: s.actual_impact || "Strategy worked well", color: "text-emerald-600" };
  if (status === "failed") return { text: s.actual_impact || "Did not achieve expected results", color: "text-red-600" };
  if (status === "evaluating") return { text: "Evaluating performance...", color: "text-amber-600" };
  if (status === "active") {
    const activated = s.activated_at;
    if (activated) {
      const days = Math.floor((Date.now() - new Date(activated).getTime()) / 86400000);
      return { text: `Running for ${days} day${days !== 1 ? "s" : ""} — still collecting results`, color: "text-blue-600" };
    }
    return { text: "Active — collecting results", color: "text-blue-600" };
  }
  if (status === "archived") return { text: "Archived", color: "text-slate-500" };
  return { text: "Awaiting activation", color: "text-slate-400" };
}

/* ------------------------------------------------------------------ */
/*  Evidence panel                                                      */
/* ------------------------------------------------------------------ */
function EvidencePanel({ evidence }: { evidence: any }) {
  const [expanded, setExpanded] = useState(false);
  if (!evidence) return null;

  const baseline = evidence.baseline_snapshot;
  const lastEval = evidence.last_evaluation;

  return (
    <div className="mt-3">
      <button
        onClick={() => setExpanded(!expanded)}
        className="text-xs font-medium text-indigo-600 hover:text-indigo-700 inline-flex items-center gap-1 transition-colors"
      >
        <Eye className="w-3 h-3" />
        {expanded ? "Hide Details" : "View Details"}
        <ChevronDown className={`w-3 h-3 transition-transform ${expanded ? "rotate-180" : ""}`} />
      </button>
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="mt-3 space-y-3">
              {/* Baseline snapshot */}
              {baseline && (
                <div className="rounded-lg bg-slate-50 border border-slate-100 p-3">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Baseline Snapshot</p>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {baseline.item_name && (
                      <div>
                        <p className="text-[10px] text-slate-400">Item</p>
                        <p className="text-xs font-semibold text-slate-700">{baseline.item_name}</p>
                      </div>
                    )}
                    {baseline.total_revenue_30d != null && (
                      <div>
                        <p className="text-[10px] text-slate-400">Revenue (30d)</p>
                        <p className="text-xs font-semibold text-slate-700">${Number(baseline.total_revenue_30d).toFixed(0)}</p>
                      </div>
                    )}
                    {baseline.total_orders_30d != null && (
                      <div>
                        <p className="text-[10px] text-slate-400">Orders (30d)</p>
                        <p className="text-xs font-semibold text-slate-700">{baseline.total_orders_30d}</p>
                      </div>
                    )}
                    {baseline.item_daily_avg_orders != null && (
                      <div>
                        <p className="text-[10px] text-slate-400">Daily Avg Orders</p>
                        <p className="text-xs font-semibold text-slate-700">{baseline.item_daily_avg_orders}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Last evaluation */}
              {lastEval?.ai_verdict && (
                <div className="rounded-lg bg-slate-50 border border-slate-100 p-3">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Last Evaluation</p>
                  <div className="space-y-1.5">
                    {lastEval.ai_verdict.verdict && (
                      <span className={`inline-block text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        lastEval.ai_verdict.verdict === "successful" ? "bg-emerald-100 text-emerald-700"
                        : lastEval.ai_verdict.verdict === "failed" ? "bg-red-100 text-red-700"
                        : "bg-amber-100 text-amber-700"
                      }`}>
                        {lastEval.ai_verdict.verdict === "too_early" ? "Too Early to Tell" : lastEval.ai_verdict.verdict}
                      </span>
                    )}
                    {lastEval.ai_verdict.summary && (
                      <p className="text-xs text-slate-600">{lastEval.ai_verdict.summary}</p>
                    )}
                    {lastEval.deltas && (
                      <div className="flex flex-wrap gap-2 mt-1">
                        {lastEval.deltas.item_daily_orders_change_pct != null && (
                          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                            lastEval.deltas.item_daily_orders_change_pct >= 0 ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"
                          }`}>
                            Orders: {lastEval.deltas.item_daily_orders_change_pct >= 0 ? "+" : ""}{lastEval.deltas.item_daily_orders_change_pct}%
                          </span>
                        )}
                        {lastEval.deltas.daily_revenue_change_pct != null && (
                          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                            lastEval.deltas.daily_revenue_change_pct >= 0 ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"
                          }`}>
                            Revenue: {lastEval.deltas.daily_revenue_change_pct >= 0 ? "+" : ""}{lastEval.deltas.daily_revenue_change_pct}%
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Raw evidence (collapsed) */}
              <details className="group">
                <summary className="text-[10px] font-medium text-slate-400 cursor-pointer hover:text-slate-600 transition-colors">
                  Raw Evidence Data
                </summary>
                <pre className="mt-2 text-[10px] text-slate-500 bg-slate-50 rounded-lg p-3 overflow-x-auto max-h-40 border border-slate-100">
                  {JSON.stringify(evidence, null, 2)}
                </pre>
              </details>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main page                                                           */
/* ------------------------------------------------------------------ */
export default function StrategyHistoryPage() {
  const { restaurantId } = useRestaurant();

  const [strategies, setStrategies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("All");

  useEffect(() => {
    (async () => {
      if (!restaurantId) {
        setLoading(false);
        setError("no_restaurant");
        return;
      }
      try {
        setLoading(true);
        const data = await api.getStrategyHistory(restaurantId);
        setStrategies(Array.isArray(data) ? data : data?.strategies ?? []);
      } catch (err: any) {
        setError(err.message ?? "Failed to load strategy history");
      } finally {
        setLoading(false);
      }
    })();
  }, [restaurantId]);

  const filtered =
    activeTab === "All"
      ? strategies
      : strategies.filter((s) => s.status === activeTab);

  // Status counts
  const counts: Record<string, number> = {};
  for (const s of strategies) {
    counts[s.status] = (counts[s.status] ?? 0) + 1;
  }
  const activeCount = (counts["active"] ?? 0) + (counts["accepted"] ?? 0);
  const completedCount = (counts["successful"] ?? 0);
  const failedCount = (counts["failed"] ?? 0);
  const reviewCount = (counts["evaluating"] ?? 0);

  /* ---------- loading ---------- */
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
          <p className="text-slate-400">Loading strategy history...</p>
        </div>
      </div>
    );
  }

  if (error && strategies.length === 0 && error !== "no_restaurant") {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-10 max-w-lg text-center">
          <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-5">
            <AlertTriangle className="w-8 h-8 text-red-400" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Something went wrong</h2>
          <p className="text-slate-500 mb-4">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-[1400px] mx-auto px-2 sm:px-3 py-10 space-y-8">
      {/* ═══════ HEADER ═══════ */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <h1 className="text-3xl font-bold text-slate-900">Strategy History</h1>
        <p className="text-slate-500 mt-1.5 max-w-xl">
          Track what actions were applied, what is active, and what is working.
        </p>
      </motion.div>

      {/* ═══════ SUMMARY BAR ═══════ */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.4 }}
        className="grid grid-cols-2 sm:grid-cols-4 gap-4"
      >
        {[
          { label: "Active", count: activeCount, icon: Activity, color: "text-blue-600", bg: "bg-blue-50", border: "border-blue-200" },
          { label: "Completed", count: completedCount, icon: CheckCircle2, color: "text-emerald-600", bg: "bg-emerald-50", border: "border-emerald-200" },
          { label: "Failed", count: failedCount, icon: XCircle, color: "text-red-600", bg: "bg-red-50", border: "border-red-200" },
          { label: "In Review", count: reviewCount, icon: Clock, color: "text-amber-600", bg: "bg-amber-50", border: "border-amber-200" },
        ].map((item, i) => {
          const Icon = item.icon;
          return (
            <motion.div
              key={item.label}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 + i * 0.05 }}
              className={`rounded-xl border ${item.border} ${item.bg} p-4 flex items-center gap-3`}
            >
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center bg-white/80 shadow-sm`}>
                <Icon className={`w-5 h-5 ${item.color}`} />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{item.count}</p>
                <p className="text-xs font-medium text-slate-500">{item.label}</p>
              </div>
            </motion.div>
          );
        })}
      </motion.div>

      {/* ═══════ FILTER PILLS ═══════ */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.25 }}
        className="flex flex-wrap gap-2"
      >
        {FILTER_TABS.map((tab) => {
          const count = tab.key === "All"
            ? strategies.length
            : strategies.filter((s) => s.status === tab.key).length;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                activeTab === tab.key
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50 hover:border-slate-300"
              }`}
            >
              {tab.label}
              <span className={`ml-1.5 text-xs ${activeTab === tab.key ? "opacity-80" : "opacity-50"}`}>
                {count}
              </span>
            </button>
          );
        })}
      </motion.div>

      {/* ═══════ EMPTY STATE ═══════ */}
      {strategies.length === 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-sm border border-slate-200 p-12 text-center"
        >
          <div className="w-16 h-16 bg-indigo-50 rounded-full flex items-center justify-center mx-auto mb-5">
            <Target className="w-8 h-8 text-indigo-400" />
          </div>
          <h2 className="text-xl font-bold text-slate-900 mb-2">No strategies tracked yet</h2>
          <p className="text-slate-500 max-w-md mx-auto leading-relaxed">
            When you apply recommendations from Menu Insights or the Recommendations page, they'll appear here so you can track their progress and results.
          </p>
          <div className="flex items-center justify-center gap-3 mt-6">
            <Link href="/menu-insights" className="inline-flex items-center gap-2 text-sm font-semibold text-indigo-600 hover:text-indigo-700 transition-colors">
              Menu Insights <ChevronRight className="w-4 h-4" />
            </Link>
            <Link href="/recommendations" className="inline-flex items-center gap-2 text-sm font-semibold text-indigo-600 hover:text-indigo-700 transition-colors">
              Recommendations <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
        </motion.div>
      )}

      {/* ═══════ NO MATCHES ═══════ */}
      {strategies.length > 0 && filtered.length === 0 && (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-10 text-center">
          <p className="text-slate-400">No strategies match this filter.</p>
        </div>
      )}

      {/* ═══════ STRATEGY CARDS ═══════ */}
      {filtered.length > 0 && (
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="space-y-4"
        >
          {filtered.map((strategy: any, i: number) => {
            const cfg = STATUS_CONFIG[strategy.status] ?? STATUS_CONFIG.suggested;
            const Icon = cfg.icon;
            const source = getSourceLabel(strategy.evidence);
            const summary = getEvidenceSummary(strategy);
            const outcome = getOutcomeMessage(strategy);

            return (
              <motion.div
                key={strategy.id ?? i}
                variants={fadeUp}
                custom={i}
                className={`bg-white rounded-2xl border shadow-sm hover:shadow-md transition-all overflow-hidden ${cfg.borderColor}`}
              >
                <div className="p-5">
                  {/* Top row: name + status */}
                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div className="flex items-start gap-3 min-w-0">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${cfg.bgColor}`}>
                        <Icon className={`w-5 h-5 ${cfg.color}`} />
                      </div>
                      <div className="min-w-0">
                        <h3 className="text-base font-bold text-slate-900 truncate">
                          {strategy.strategy_name ?? strategy.name ?? strategy.title ?? "Strategy"}
                        </h3>
                        <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                          {strategy.strategy_category && (
                            <span className="text-[10px] font-semibold text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">
                              {strategy.strategy_category}
                            </span>
                          )}
                          {strategy.menu_item_name && (
                            <span className="text-[10px] font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full">
                              {strategy.menu_item_name}
                            </span>
                          )}
                          {source && (
                            <span className="text-[10px] font-medium text-slate-400">
                              via {source}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <span className={`shrink-0 text-xs font-bold px-3 py-1 rounded-full ${cfg.bgColor} ${cfg.color}`}>
                      {cfg.label}
                    </span>
                  </div>

                  {/* Summary */}
                  {summary && (
                    <p className="text-sm text-slate-600 mb-3 line-clamp-2">{summary}</p>
                  )}

                  {/* Timeline bar */}
                  <div className="flex items-center gap-4 flex-wrap text-xs text-slate-400 mb-2">
                    {strategy.suggested_at && (
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" /> Suggested {formatRelative(strategy.suggested_at)}
                      </span>
                    )}
                    {strategy.activated_at && (
                      <span className="flex items-center gap-1">
                        <Zap className="w-3 h-3 text-blue-400" /> Activated {formatRelative(strategy.activated_at)}
                      </span>
                    )}
                    {strategy.evaluated_at && (
                      <span className="flex items-center gap-1">
                        <Eye className="w-3 h-3 text-amber-400" /> Evaluated {formatRelative(strategy.evaluated_at)}
                      </span>
                    )}
                    {strategy.completed_at && (
                      <span className="flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Completed {formatRelative(strategy.completed_at)}
                      </span>
                    )}
                    {!strategy.suggested_at && strategy.created_at && (
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" /> Created {formatRelative(strategy.created_at)}
                      </span>
                    )}
                  </div>

                  {/* Outcome */}
                  <div className={`text-sm font-medium ${outcome.color}`}>
                    {outcome.text}
                  </div>

                  {/* Evidence panel */}
                  <EvidencePanel evidence={strategy.evidence} />
                </div>

                {/* Progress bar for active strategies */}
                {(strategy.status === "active" || strategy.status === "evaluating") && strategy.activated_at && (
                  <div className="h-1 bg-slate-100">
                    <motion.div
                      className={`h-1 ${strategy.status === "evaluating" ? "bg-amber-400" : "bg-blue-400"}`}
                      initial={{ width: 0 }}
                      animate={{
                        width: `${Math.min(
                          (Math.floor((Date.now() - new Date(strategy.activated_at).getTime()) / 86400000) / 30) * 100,
                          100
                        )}%`,
                      }}
                      transition={{ delay: 0.3 + i * 0.06, duration: 0.8 }}
                    />
                  </div>
                )}
              </motion.div>
            );
          })}
        </motion.div>
      )}
    </div>
  );
}
