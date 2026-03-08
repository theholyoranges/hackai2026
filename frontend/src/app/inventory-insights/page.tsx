"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Package,
  AlertTriangle,
  Clock,
  TrendingDown,
  ShieldCheck,
  Flame,
  RotateCcw,
  Trash2,
  BarChart3,
  ChevronDown,
  Zap,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
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
    transition: { delay: i * 0.08, duration: 0.45, ease: "easeOut" as const },
  }),
};

const staggerContainer = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
};

/* ------------------------------------------------------------------ */
/*  Helpers                                                             */
/* ------------------------------------------------------------------ */
function daysLeftColor(days: number) {
  if (days <= 2) return "text-red-600 bg-red-50 border-red-200";
  if (days <= 5) return "text-amber-600 bg-amber-50 border-amber-200";
  if (days <= 10) return "text-yellow-700 bg-yellow-50 border-yellow-200";
  return "text-emerald-600 bg-emerald-50 border-emerald-200";
}

function daysLeftBadge(days: number) {
  if (days <= 2) return { label: "Critical", color: "bg-red-100 text-red-700" };
  if (days <= 5) return { label: "Low", color: "bg-amber-100 text-amber-700" };
  if (days <= 10) return { label: "Watch", color: "bg-yellow-100 text-yellow-700" };
  return { label: "Healthy", color: "bg-emerald-100 text-emerald-700" };
}

function statusIcon(days: number | null) {
  if (days === null) return <Clock className="w-4 h-4 text-slate-400" />;
  if (days <= 2) return <XCircle className="w-4 h-4 text-red-500" />;
  if (days <= 5) return <AlertTriangle className="w-4 h-4 text-amber-500" />;
  return <CheckCircle2 className="w-4 h-4 text-emerald-500" />;
}

/* ------------------------------------------------------------------ */
/*  Custom chart tooltip                                                */
/* ------------------------------------------------------------------ */
function UsageTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-lg px-4 py-3 text-sm">
      <p className="font-semibold text-slate-700">{label}</p>
      <p className="text-slate-900 font-bold">{payload[0].value?.toFixed(2)} {payload[0].payload?.unit ?? ""}/day</p>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main page                                                           */
/* ------------------------------------------------------------------ */
export default function InventoryInsightsPage() {
  const { restaurantId } = useRestaurant();

  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tableSort, setTableSort] = useState<"days" | "usage" | "stock">("days");
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    (async () => {
      if (!restaurantId) {
        setLoading(false);
        setError("no_restaurant");
        return;
      }
      try {
        setLoading(true);
        setError(null);
        const data = await api.getInventoryAnalytics(restaurantId);
        setAnalytics(data);
      } catch (err: any) {
        setError(err.message ?? "Failed to load inventory analytics");
      } finally {
        setLoading(false);
      }
    })();
  }, [restaurantId]);

  /* ---------- loading / empty ---------- */
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
          <p className="text-slate-400">Loading inventory insights...</p>
        </div>
      </div>
    );
  }

  if (error && !analytics) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-10 max-w-lg text-center">
          <div className="w-16 h-16 bg-indigo-50 rounded-full flex items-center justify-center mx-auto mb-5">
            <Package className="w-8 h-8 text-indigo-400" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">
            No inventory data yet
          </h2>
          <p className="text-slate-500 mb-6 leading-relaxed">
            Upload your inventory data to see stock levels, usage projections, and smart reorder alerts.
          </p>
          <Link
            href="/upload"
            className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6 py-3 rounded-xl transition-colors text-sm shadow-sm"
          >
            <Zap className="w-4 h-4" /> Upload Data
          </Link>
        </div>
      </div>
    );
  }

  /* ---------- extract data ---------- */
  const stockoutRisks = analytics?.stockout_risks ?? [];
  const expiryRisks = analytics?.expiry_risks ?? [];
  const ingredients = analytics?.usage_projections ?? [];
  const usageRates = (analytics?.usage_projections ?? [])
    .filter((i: any) => i.daily_usage > 0)
    .sort((a: any, b: any) => b.daily_usage - a.daily_usage)
    .slice(0, 10);
  const wasteProne = analytics?.waste_prone ?? [];
  const reorderAlerts = analytics?.reorder_alerts ?? [];
  const overstockRisks = analytics?.overstock_risks ?? [];

  // KPI calculations
  const totalItems = ingredients.length;
  const criticalCount = ingredients.filter((i: any) => i.projected_days_left != null && i.projected_days_left <= 2).length;
  const lowCount = ingredients.filter((i: any) => i.projected_days_left != null && i.projected_days_left > 2 && i.projected_days_left <= 7).length;
  const healthyCount = ingredients.filter((i: any) => i.projected_days_left == null || i.projected_days_left > 7).length;
  const healthPct = totalItems > 0 ? Math.round((healthyCount / totalItems) * 100) : 0;

  // Sort the table
  const sortedIngredients = [...ingredients].sort((a: any, b: any) => {
    if (tableSort === "days") {
      const aDays = a.projected_days_left ?? 9999;
      const bDays = b.projected_days_left ?? 9999;
      return aDays - bDays;
    }
    if (tableSort === "usage") return (b.daily_usage ?? 0) - (a.daily_usage ?? 0);
    return (a.quantity_on_hand ?? 0) - (b.quantity_on_hand ?? 0);
  });
  const displayedIngredients = showAll ? sortedIngredients : sortedIngredients.slice(0, 12);

  const hasAlerts = stockoutRisks.length > 0 || expiryRisks.length > 0;

  return (
    <div className="max-w-7xl mx-auto px-4 py-10 space-y-10">
      {/* ═══════ HEADER ═══════ */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <h1 className="text-3xl font-bold text-slate-900">
          Inventory Insights
        </h1>
        <p className="text-slate-500 mt-1.5 max-w-xl">
          Real-time stock levels, usage projections, and smart alerts to prevent waste and stockouts.
        </p>
      </motion.div>

      {/* ═══════ KPI CARDS ═══════ */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5"
      >
        {/* Total Tracked */}
        <motion.div variants={fadeUp} custom={0}
          className="group bg-white rounded-2xl border border-slate-200 shadow-sm p-6 hover:shadow-md hover:border-slate-300 transition-all"
        >
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500">Tracked Items</p>
              <p className="text-3xl font-bold text-slate-900 mt-2">{totalItems}</p>
              <p className="text-sm text-slate-400 mt-2">ingredients in stock</p>
            </div>
            <div className="w-11 h-11 bg-indigo-50 rounded-xl flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
              <Package className="w-5 h-5 text-indigo-500" />
            </div>
          </div>
        </motion.div>

        {/* Stock Health */}
        <motion.div variants={fadeUp} custom={1}
          className="group bg-white rounded-2xl border border-slate-200 shadow-sm p-6 hover:shadow-md hover:border-slate-300 transition-all"
        >
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500">Stock Health</p>
              <p className="text-3xl font-bold text-slate-900 mt-2">{healthPct}%</p>
              <p className="text-sm text-slate-400 mt-2">{healthyCount} items above 7-day supply</p>
            </div>
            <div className="w-11 h-11 bg-emerald-50 rounded-xl flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
              <ShieldCheck className="w-5 h-5 text-emerald-500" />
            </div>
          </div>
          {healthPct >= 80 && (
            <div className="mt-3">
              <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full">
                <CheckCircle2 className="w-3 h-3" /> Good shape
              </span>
            </div>
          )}
        </motion.div>

        {/* Critical Items */}
        <motion.div variants={fadeUp} custom={2}
          className="group bg-white rounded-2xl border border-slate-200 shadow-sm p-6 hover:shadow-md hover:border-slate-300 transition-all"
        >
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500">Critical Items</p>
              <p className="text-3xl font-bold text-slate-900 mt-2">{criticalCount}</p>
              <p className="text-sm text-slate-400 mt-2">{criticalCount === 0 ? "No urgent restocks" : "need restocking ASAP"}</p>
            </div>
            <div className={`w-11 h-11 ${criticalCount > 0 ? "bg-red-50" : "bg-slate-50"} rounded-xl flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform`}>
              <AlertTriangle className={`w-5 h-5 ${criticalCount > 0 ? "text-red-500" : "text-slate-400"}`} />
            </div>
          </div>
          {criticalCount > 0 && (
            <div className="mt-3">
              <span className="inline-flex items-center gap-1 text-xs font-semibold text-red-600 bg-red-50 px-2.5 py-1 rounded-full">
                <Flame className="w-3 h-3" /> Urgent
              </span>
            </div>
          )}
        </motion.div>

        {/* Reorder Queue */}
        <motion.div variants={fadeUp} custom={3}
          className="group bg-white rounded-2xl border border-slate-200 shadow-sm p-6 hover:shadow-md hover:border-slate-300 transition-all"
        >
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500">Reorder Queue</p>
              <p className="text-3xl font-bold text-slate-900 mt-2">{reorderAlerts.length}</p>
              <p className="text-sm text-slate-400 mt-2">{reorderAlerts.length === 0 ? "All stocked up" : "items to reorder soon"}</p>
            </div>
            <div className="w-11 h-11 bg-amber-50 rounded-xl flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
              <RotateCcw className="w-5 h-5 text-amber-500" />
            </div>
          </div>
          {reorderAlerts.length > 0 && (
            <div className="mt-3">
              <span className="inline-flex items-center gap-1 text-xs font-semibold text-amber-600 bg-amber-50 px-2.5 py-1 rounded-full">
                <Clock className="w-3 h-3" /> Action needed
              </span>
            </div>
          )}
        </motion.div>
      </motion.div>

      {/* ═══════ RISK ALERTS BANNER ═══════ */}
      {hasAlerts && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
          className="space-y-3"
        >
          <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-500" />
            Active Alerts
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {stockoutRisks.map((alert: any, i: number) => (
              <motion.div
                key={`stockout-${i}`}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.35 + i * 0.05 }}
                className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl p-4"
              >
                <div className="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center shrink-0 mt-0.5">
                  <XCircle className="w-4 h-4 text-red-600" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-red-900">Stockout Risk — {alert.ingredient}</p>
                  <p className="text-xs text-red-700 mt-0.5">
                    ~{alert.projected_days_left != null ? alert.projected_days_left.toFixed(1) : "?"} days remaining at current usage
                    {alert.quantity_on_hand != null && ` · ${Number(alert.quantity_on_hand).toFixed(1)} ${alert.unit ?? ""} left`}
                  </p>
                </div>
              </motion.div>
            ))}
            {expiryRisks.map((alert: any, i: number) => (
              <motion.div
                key={`expiry-${i}`}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.35 + (stockoutRisks.length + i) * 0.05 }}
                className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl p-4"
              >
                <div className="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center shrink-0 mt-0.5">
                  <Clock className="w-4 h-4 text-amber-600" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-amber-900">Expiry Warning — {alert.ingredient}</p>
                  <p className="text-xs text-amber-700 mt-0.5">
                    Expires in {alert.days_until_expiry ?? "?"} days
                    {alert.quantity_on_hand != null && ` · ${Number(alert.quantity_on_hand).toFixed(1)} ${alert.unit ?? ""} on hand`}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* ═══════ USAGE RATE CHART ═══════ */}
      {usageRates.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.5 }}
          className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6"
        >
          <div className="mb-6">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-indigo-500" />
              <h2 className="text-lg font-semibold text-slate-900">Daily Usage Rate</h2>
            </div>
            <p className="text-sm text-slate-400 mt-0.5">Top ingredients by consumption — know what moves fastest</p>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={usageRates} margin={{ top: 5, right: 10, left: 0, bottom: 5 }} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
              <YAxis dataKey="ingredient" type="category" tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} width={130} />
              <Tooltip content={<UsageTooltip />} />
              <Bar dataKey="daily_usage" radius={[0, 6, 6, 0]}>
                {usageRates.map((_: any, idx: number) => (
                  <Cell key={idx} fill={idx === 0 ? "#818cf8" : idx < 3 ? "#a5b4fc" : "#e2e8f0"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      )}

      {/* ═══════ INGREDIENT TABLE ═══════ */}
      {ingredients.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.5 }}
          className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden"
        >
          <div className="p-6 pb-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <Package className="w-5 h-5 text-indigo-500" />
                  <h2 className="text-lg font-semibold text-slate-900">Ingredient Status</h2>
                </div>
                <p className="text-sm text-slate-400 mt-0.5">Full inventory overview sorted by urgency</p>
              </div>
              <div className="flex items-center gap-2">
                {(["days", "usage", "stock"] as const).map((key) => (
                  <button
                    key={key}
                    onClick={() => setTableSort(key)}
                    className={`text-xs font-medium px-3 py-1.5 rounded-lg transition-colors ${
                      tableSort === key
                        ? "bg-indigo-100 text-indigo-700"
                        : "bg-slate-100 text-slate-500 hover:bg-slate-200"
                    }`}
                  >
                    {key === "days" ? "Days Left" : key === "usage" ? "Usage" : "Stock"}
                  </button>
                ))}
              </div>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-t border-b border-slate-100 bg-slate-50/50">
                  <th className="text-left py-3 px-6 font-medium text-slate-500 text-xs uppercase tracking-wider">Ingredient</th>
                  <th className="text-right py-3 px-6 font-medium text-slate-500 text-xs uppercase tracking-wider">On Hand</th>
                  <th className="text-right py-3 px-6 font-medium text-slate-500 text-xs uppercase tracking-wider">Daily Usage</th>
                  <th className="text-right py-3 px-6 font-medium text-slate-500 text-xs uppercase tracking-wider">Days Left</th>
                  <th className="text-center py-3 px-6 font-medium text-slate-500 text-xs uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody>
                {displayedIngredients.map((ing: any, i: number) => {
                  const daysLeft = ing.projected_days_left;
                  const hasDays = daysLeft != null;
                  const badge = hasDays ? daysLeftBadge(daysLeft) : null;
                  return (
                    <motion.tr
                      key={i}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.02 }}
                      className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors"
                    >
                      <td className="py-3.5 px-6">
                        <div className="flex items-center gap-2.5">
                          {statusIcon(daysLeft)}
                          <span className="font-medium text-slate-800">{ing.ingredient}</span>
                        </div>
                      </td>
                      <td className="py-3.5 px-6 text-right text-slate-600">
                        {ing.quantity_on_hand != null
                          ? `${Number(ing.quantity_on_hand).toFixed(1)} ${ing.unit ?? ""}`
                          : "—"}
                      </td>
                      <td className="py-3.5 px-6 text-right text-slate-600">
                        {ing.daily_usage != null && ing.daily_usage > 0
                          ? `${Number(ing.daily_usage).toFixed(2)}/day`
                          : <span className="text-slate-400">No usage</span>}
                      </td>
                      <td className="py-3.5 px-6 text-right">
                        {hasDays ? (
                          <span className={`inline-block px-2.5 py-1 rounded-full text-xs font-semibold border ${daysLeftColor(daysLeft)}`}>
                            {daysLeft.toFixed(0)} days
                          </span>
                        ) : (
                          <span className="inline-block px-2.5 py-1 rounded-full text-xs font-medium bg-slate-50 text-slate-400 border border-slate-200">
                            N/A
                          </span>
                        )}
                      </td>
                      <td className="py-3.5 px-6 text-center">
                        {badge ? (
                          <span className={`inline-block px-2.5 py-1 rounded-full text-[10px] font-bold ${badge.color}`}>
                            {badge.label}
                          </span>
                        ) : (
                          <span className="inline-block px-2.5 py-1 rounded-full text-[10px] font-bold bg-slate-100 text-slate-500">
                            No data
                          </span>
                        )}
                      </td>
                    </motion.tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {sortedIngredients.length > 12 && (
            <div className="p-4 text-center border-t border-slate-100">
              <button
                onClick={() => setShowAll(!showAll)}
                className="text-sm font-medium text-indigo-600 hover:text-indigo-700 inline-flex items-center gap-1 transition-colors"
              >
                {showAll ? "Show less" : `Show all ${sortedIngredients.length} items`}
                <ChevronDown className={`w-4 h-4 transition-transform ${showAll ? "rotate-180" : ""}`} />
              </button>
            </div>
          )}
        </motion.div>
      )}

      {/* ═══════ REORDER ALERTS + WASTE PRONE SIDE BY SIDE ═══════ */}
      {(reorderAlerts.length > 0 || wasteProne.length > 0) && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.5 }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-6"
        >
          {/* Reorder Alerts */}
          {reorderAlerts.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
              <div className="flex items-center gap-2 mb-5">
                <RotateCcw className="w-5 h-5 text-amber-500" />
                <h2 className="text-base font-semibold text-slate-900">Reorder Soon</h2>
              </div>
              <p className="text-sm text-slate-400 mb-4">Items approaching minimum stock levels</p>
              <div className="space-y-2.5">
                {reorderAlerts.map((alert: any, i: number) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.65 + i * 0.05 }}
                    className="flex items-center justify-between rounded-xl border border-amber-100 bg-gradient-to-r from-amber-50/60 to-transparent p-3.5"
                  >
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-slate-800 truncate">{alert.ingredient}</p>
                      <p className="text-xs text-slate-500 mt-0.5">
                        {alert.quantity_on_hand?.toFixed(1) ?? "?"} on hand
                        {alert.projected_days_left != null && ` · ~${alert.projected_days_left.toFixed(0)} days left`}
                      </p>
                    </div>
                    <span className="shrink-0 bg-amber-100 text-amber-700 text-[10px] font-bold px-2.5 py-1 rounded-full">
                      Reorder
                    </span>
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {/* Waste-Prone Items */}
          {wasteProne.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
              <div className="flex items-center gap-2 mb-5">
                <Trash2 className="w-5 h-5 text-red-500" />
                <h2 className="text-base font-semibold text-slate-900">Waste Risk</h2>
              </div>
              <p className="text-sm text-slate-400 mb-4">Items at risk of going to waste — use or repurpose</p>
              <div className="space-y-2.5">
                {wasteProne.map((item: any, i: number) => {
                  const reason = item.waste_reasons?.includes("zero_usage_with_stock")
                    ? "In stock but not being used"
                    : item.waste_reasons?.includes("overstocked_and_near_expiry")
                      ? "Overstocked & near expiry"
                      : item.waste_reasons?.includes("extremely_low_usage_rate")
                        ? "Very low usage rate"
                        : "High waste risk";
                  return (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: 10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.65 + i * 0.05 }}
                      className="flex items-center justify-between rounded-xl border border-red-100 bg-gradient-to-r from-red-50/60 to-transparent p-3.5"
                    >
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-slate-800 truncate">{item.ingredient}</p>
                        <p className="text-xs text-slate-500 mt-0.5">
                          {item.quantity_on_hand?.toFixed(1)} {item.unit} on hand
                          {item.projected_days_left != null && ` · ~${item.projected_days_left.toFixed(0)} days supply`}
                        </p>
                      </div>
                      <span className="shrink-0 text-[10px] font-bold px-2.5 py-1 rounded-full bg-red-100 text-red-700 max-w-[120px] text-center">
                        {reason}
                      </span>
                    </motion.div>
                  );
                })}
              </div>
            </div>
          )}
        </motion.div>
      )}

      {/* ═══════ OVERSTOCK SECTION ═══════ */}
      {overstockRisks.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7, duration: 0.5 }}
          className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6"
        >
          <div className="flex items-center gap-2 mb-2">
            <TrendingDown className="w-5 h-5 text-blue-500" />
            <h2 className="text-lg font-semibold text-slate-900">Overstocked Items</h2>
          </div>
          <p className="text-sm text-slate-400 mb-5">60+ days of supply — consider reducing next order</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {overstockRisks.map((item: any, i: number) => (
              <div
                key={i}
                className="rounded-xl border border-blue-100 bg-blue-50/50 p-3.5"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-sm font-semibold text-slate-800 truncate">{item.ingredient}</span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 shrink-0">
                    {item.projected_days_left?.toFixed(0)}d supply
                  </span>
                </div>
                <div className="text-xs text-slate-500">
                  {item.quantity_on_hand?.toFixed(1)} {item.unit} on hand
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}
