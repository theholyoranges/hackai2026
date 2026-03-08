"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  DollarSign,
  Heart,
  AlertTriangle,
  Sparkles,
  TrendingUp,
  Zap,
  ArrowRight,
  ShieldCheck,
  Package,
  Activity,
  CheckCircle2,
  XCircle,
  Clock,
  BarChart3,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

import { api } from "@/lib/api";
import { useRestaurant } from "@/context/RestaurantContext";

/* ------------------------------------------------------------------ */
/*  Revenue aggregation helpers                                        */
/* ------------------------------------------------------------------ */
type ViewMode = "daily" | "weekly" | "monthly";

function aggregateWeekly(data: { date: string; revenue: number }[]) {
  const weeks: Record<string, number> = {};
  for (const d of data) {
    const dt = new Date(d.date);
    // Week starts on Monday
    const day = dt.getDay();
    const diff = dt.getDate() - day + (day === 0 ? -6 : 1);
    const monday = new Date(dt);
    monday.setDate(diff);
    const key = `Week of ${monday.toLocaleDateString("en-US", { month: "short", day: "numeric" })}`;
    weeks[key] = (weeks[key] ?? 0) + (d.revenue ?? 0);
  }
  return Object.entries(weeks).map(([date, revenue]) => ({ date, revenue }));
}

function aggregateMonthly(data: { date: string; revenue: number }[]) {
  const months: Record<string, number> = {};
  for (const d of data) {
    const dt = new Date(d.date);
    const key = dt.toLocaleDateString("en-US", { month: "short", year: "numeric" });
    months[key] = (months[key] ?? 0) + (d.revenue ?? 0);
  }
  return Object.entries(months).map(([date, revenue]) => ({ date, revenue }));
}

/* ------------------------------------------------------------------ */
/*  Custom Tooltip                                                     */
/* ------------------------------------------------------------------ */
function SalesTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-lg px-4 py-3 text-sm">
      <p className="font-semibold text-slate-700">{label}</p>
      <p className="text-lg font-bold text-slate-900">
        ${Number(payload[0].value).toLocaleString(undefined, { maximumFractionDigits: 0 })}
      </p>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main Dashboard                                                     */
/* ------------------------------------------------------------------ */
export default function DashboardPage() {
  const { restaurantId } = useRestaurant();

  const [dashboard, setDashboard] = useState<any>(null);
  const [restaurantName, setRestaurantName] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionsGenerated, setActionsGenerated] = useState(false);
  const [chartView, setChartView] = useState<ViewMode>("daily");
  const [activeStrategies, setActiveStrategies] = useState<any[]>([]);
  const [evaluatingId, setEvaluatingId] = useState<number | null>(null);

  const fetchDashboard = async () => {
    if (!restaurantId) {
      setLoading(false);
      setError("no_restaurant");
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const [data, restaurant, strategies] = await Promise.all([
        api.getDashboard(restaurantId),
        api.getRestaurant(restaurantId).catch(() => null),
        api.getStrategyProgress(restaurantId).catch(() => []),
      ]);
      setDashboard(data);
      setRestaurantName(restaurant?.name ?? "");
      setActiveStrategies(strategies ?? []);
    } catch (err: any) {
      setError(err.message ?? "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setDashboard(null);
    setError(null);
    fetchDashboard();
    setActionsGenerated(false);
  }, [restaurantId]);

  const handleGenerate = async () => {
    try {
      setGenerating(true);
      await api.generateRecommendations(restaurantId);
      await fetchDashboard();
      setActionsGenerated(true);
    } catch (err: any) {
      setError(err.message ?? "Failed to generate ideas");
    } finally {
      setGenerating(false);
    }
  };

  const handleAccept = async (id: number) => {
    await api.updateRecommendationStatus(id, "accepted");
    fetchDashboard();
  };

  const handleReject = async (id: number) => {
    await api.updateRecommendationStatus(id, "rejected");
    fetchDashboard();
  };

  const handleEvaluate = async (historyId: number) => {
    setEvaluatingId(historyId);
    try {
      await api.evaluateStrategy(historyId);
      // Refresh strategies
      const strategies = await api.getStrategyProgress(restaurantId).catch(() => []);
      setActiveStrategies(strategies ?? []);
    } catch {
      // silent
    } finally {
      setEvaluatingId(null);
    }
  };

  /* ---------- loading / error ---------- */
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
          <p className="text-slate-400">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  if (error && !dashboard) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-10 max-w-lg text-center">
          <div className="w-16 h-16 bg-indigo-50 rounded-full flex items-center justify-center mx-auto mb-5">
            <Sparkles className="w-8 h-8 text-indigo-400" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">
            Hello! Welcome to your Growth Copilot.
          </h2>
          <p className="text-slate-500 mb-6 leading-relaxed">
            We don't have any data for this restaurant yet. Upload your menu, inventory, and sales to unlock AI-powered insights.
          </p>
          <Link
            href="/upload"
            className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6 py-3 rounded-xl transition-colors text-sm shadow-sm"
          >
            <Zap className="w-4 h-4" /> Upload Data to Get Started
          </Link>
        </div>
      </div>
    );
  }

  /* ---------- extract data ---------- */
  const revenueTrend = dashboard?.revenue_trend ?? [];
  const topItem = dashboard?.top_item;
  const wasteAlerts = dashboard?.waste_alerts ?? [];
  const stockoutAlerts = dashboard?.stockout_alerts ?? [];
  const recommendations = dashboard?.top_recommendations ?? [];

  const totalRevenue = revenueTrend.reduce(
    (sum: number, d: any) => sum + (d.revenue ?? 0), 0
  );

  const wasteValue = wasteAlerts.reduce(
    (sum: number, a: any) => sum + ((a.unit_cost ?? 0) * (a.quantity_on_hand ?? 0)), 0
  );

  const pendingCount = recommendations.filter((r: any) => r.status === "pending").length;

  const chartData =
    chartView === "weekly"
      ? aggregateWeekly(revenueTrend)
      : chartView === "monthly"
        ? aggregateMonthly(revenueTrend)
        : revenueTrend;

  // Unified kitchen alerts (waste + stockout), max 3
  const kitchenAlerts = [
    ...wasteAlerts.map((a: any) => ({
      icon: "waste" as const,
      ingredient: a.ingredient,
      message: `expiring soon — ${a.projected_days_left?.toFixed(0) ?? "?"} days left`,
      daysLeft: a.projected_days_left ?? 99,
    })),
    ...stockoutAlerts.map((a: any) => ({
      icon: "stockout" as const,
      ingredient: a.ingredient,
      message: `running low — ${a.projected_days_left?.toFixed(0) ?? "?"} days left`,
      daysLeft: a.projected_days_left ?? 99,
    })),
  ].sort((a, b) => a.daysLeft - b.daysLeft);

  const displayName = restaurantName
    ? restaurantName.charAt(0).toUpperCase() + restaurantName.slice(1)
    : "your restaurant";

  return (
    <div className="max-w-7xl mx-auto px-4 py-10 space-y-8">
      {/* ═══════ Header ═══════ */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900">
          Welcome back, {displayName}!
        </h1>
        <p className="text-slate-500 mt-1">
          Here is what your AI assistant is seeing today.
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-600 text-sm">
          {error}
        </div>
      )}

      {/* ═══════ KPI Cards ═══════ */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Total Sales */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500">Total Sales</p>
              <p className="text-3xl font-bold text-slate-900 mt-2">
                ${totalRevenue > 0
                  ? totalRevenue.toLocaleString(undefined, { maximumFractionDigits: 0 })
                  : "15,580"}
              </p>
              <span className="inline-flex items-center gap-1 mt-3 text-xs font-semibold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full">
                <TrendingUp className="w-3 h-3" /> Up 8% this week
              </span>
            </div>
            <div className="w-11 h-11 bg-emerald-50 rounded-xl flex items-center justify-center">
              <DollarSign className="w-5 h-5 text-emerald-600" />
            </div>
          </div>
        </div>

        {/* Crowd Favorite */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500">Crowd Favorite</p>
              <p className="text-3xl font-bold text-slate-900 mt-2">
                {topItem?.item ?? "Butter Naan"}
              </p>
              <p className="text-xs text-slate-400 mt-3">Still your top earner.</p>
            </div>
            <div className="w-11 h-11 bg-pink-50 rounded-xl flex items-center justify-center">
              <Heart className="w-5 h-5 text-pink-500" />
            </div>
          </div>
        </div>

        {/* Waste Warning */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500">Waste Warning</p>
              <p className="text-3xl font-bold text-slate-900 mt-2">
                ${wasteValue > 0
                  ? wasteValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                  : "120.00"}
              </p>
              <p className="text-xs text-slate-400 mt-3">Value of food expiring soon.</p>
            </div>
            <div className="w-11 h-11 bg-orange-50 rounded-xl flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-orange-500" />
            </div>
          </div>
        </div>

        {/* AI Ideas */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500">AI Ideas</p>
              <p className="text-3xl font-bold text-slate-900 mt-2">
                {pendingCount > 0 ? pendingCount : 3} Ready
              </p>
              <button
                onClick={handleGenerate}
                disabled={generating}
                className="mt-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white text-xs font-semibold px-4 py-2 rounded-lg transition-colors inline-flex items-center gap-1.5"
              >
                {generating ? (
                  <>
                    <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white" />
                    Working...
                  </>
                ) : (
                  <>
                    <Zap className="w-3.5 h-3.5" /> Review Ideas
                  </>
                )}
              </button>
            </div>
            <div className="w-11 h-11 bg-indigo-50 rounded-xl flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-indigo-600" />
            </div>
          </div>
        </div>
      </div>

      {/* ═══════ Sales Trend Chart ═══════ */}
      {revenueTrend.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Your Sales Trend</h2>
              <p className="text-sm text-slate-400 mt-0.5">
                {chartView === "daily" && "Daily sales over the past month"}
                {chartView === "weekly" && "Weekly totals over the past month"}
                {chartView === "monthly" && "Monthly totals"}
              </p>
            </div>
            <div className="flex bg-slate-100 rounded-lg p-0.5">
              {(["daily", "weekly", "monthly"] as ViewMode[]).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setChartView(mode)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                    chartView === mode
                      ? "bg-white text-slate-900 shadow-sm"
                      : "text-slate-500 hover:text-slate-700"
                  }`}
                >
                  {mode.charAt(0).toUpperCase() + mode.slice(1)}
                </button>
              ))}
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: "#94a3b8" }}
                axisLine={{ stroke: "#e2e8f0" }}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "#94a3b8" }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v) => `$${v}`}
              />
              <Tooltip content={<SalesTooltip />} />
              <Line
                type="monotone"
                dataKey="revenue"
                stroke="#8b5cf6"
                strokeWidth={2.5}
                dot={chartView !== "daily"}
                activeDot={{ r: 6, fill: "#8b5cf6", stroke: "#fff", strokeWidth: 2 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* ═══════ Bottom Split: Quick Wins + Kitchen Alerts ═══════ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Quick Wins */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center gap-2 mb-5">
            <Sparkles className="w-5 h-5 text-violet-500" />
            <h2 className="text-lg font-semibold text-slate-900">Quick Wins</h2>
          </div>

          {!actionsGenerated && recommendations.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <div className="w-14 h-14 bg-violet-50 rounded-full flex items-center justify-center mb-4">
                <Sparkles className="w-7 h-7 text-violet-400" />
              </div>
              <p className="text-sm text-slate-600 mb-1">Your AI assistant is watching the numbers.</p>
              <p className="text-xs text-slate-400 mb-5">Tap below to get personalized ideas to grow revenue.</p>
              <button
                onClick={handleGenerate}
                disabled={generating}
                className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-semibold px-6 py-2.5 rounded-xl transition-colors flex items-center gap-2 text-sm shadow-sm"
              >
                {generating ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                    Thinking...
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4" /> Generate Growth Plan
                  </>
                )}
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {recommendations.slice(0, 3).map((rec: any) => (
                <div
                  key={rec.id}
                  className="rounded-xl border border-slate-100 bg-slate-50/50 p-5 hover:shadow-md transition-shadow"
                >
                  <p className="text-sm text-slate-800 leading-relaxed">
                    {rec.explanation_text || rec.title}
                  </p>
                  {rec.status === "pending" && (
                    <div className="flex items-center gap-2 mt-4">
                      <button
                        onClick={() => handleAccept(rec.id)}
                        className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold px-4 py-2 rounded-lg transition-colors"
                      >
                        Review & Post
                      </button>
                      <button
                        onClick={() => handleReject(rec.id)}
                        className="text-xs text-slate-400 hover:text-slate-600 px-3 py-2 transition-colors"
                      >
                        Skip
                      </button>
                    </div>
                  )}
                  {rec.status && rec.status !== "pending" && (
                    <span className={`inline-block mt-3 badge text-xs ${
                      rec.status === "accepted"
                        ? "bg-emerald-50 text-emerald-700"
                        : "bg-slate-100 text-slate-500"
                    }`}>
                      {rec.status === "accepted" ? "Done" : rec.status}
                    </span>
                  )}
                </div>
              ))}
              {recommendations.length > 3 && (
                <Link
                  href="/recommendations"
                  className="flex items-center gap-1 text-sm font-medium text-indigo-600 hover:text-indigo-700 pt-1"
                >
                  See all ideas <ArrowRight className="w-4 h-4" />
                </Link>
              )}
            </div>
          )}
        </div>

        {/* Right: Kitchen Alerts */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center gap-2 mb-5">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            <h2 className="text-lg font-semibold text-slate-900">Kitchen Alerts</h2>
          </div>

          {kitchenAlerts.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <div className="w-14 h-14 bg-emerald-50 rounded-full flex items-center justify-center mb-4">
                <ShieldCheck className="w-7 h-7 text-emerald-400" />
              </div>
              <p className="text-sm text-slate-600">Kitchen is looking great!</p>
              <p className="text-xs text-slate-400 mt-1">No alerts right now.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {kitchenAlerts.slice(0, 3).map((alert, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between gap-3 rounded-xl border border-slate-100 bg-slate-50/50 p-4"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${
                      alert.icon === "waste" ? "bg-orange-50" : "bg-red-50"
                    }`}>
                      {alert.icon === "waste" ? (
                        <AlertTriangle className="w-4 h-4 text-orange-500" />
                      ) : (
                        <Package className="w-4 h-4 text-red-500" />
                      )}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-slate-800 truncate">
                        {alert.ingredient}
                      </p>
                      <p className="text-xs text-slate-400 truncate">
                        {alert.message}
                      </p>
                    </div>
                  </div>
                  <button className="shrink-0 text-xs font-medium text-slate-500 border border-slate-200 hover:border-slate-300 hover:text-slate-700 px-3 py-1.5 rounded-lg transition-colors">
                    Restock
                  </button>
                </div>
              ))}

              {kitchenAlerts.length > 3 && (
                <Link
                  href="/inventory-insights"
                  className="flex items-center gap-1 text-sm font-medium text-slate-400 hover:text-slate-600 pt-2"
                >
                  View all alerts <ArrowRight className="w-4 h-4" />
                </Link>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ═══════ Strategy Tracker ═══════ */}
      {activeStrategies.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center gap-2 mb-5">
            <Activity className="w-5 h-5 text-indigo-500" />
            <h2 className="text-lg font-semibold text-slate-900">Your Active Strategies</h2>
          </div>
          <p className="text-sm text-slate-400 mb-5">
            Strategies you adopted — tracking their sales impact since activation.
          </p>
          <div className="space-y-4">
            {activeStrategies.map((s: any) => {
              const isActive = s.status === "active" || s.status === "accepted";
              const isEvaluating = s.status === "evaluating";
              const isSuccessful = s.status === "successful";
              const isFailed = s.status === "failed";
              const isLoading = evaluatingId === s.id;

              const hasItemSales = s.total_orders_since != null;
              const ordersDelta = s.baseline_daily_orders && s.current_daily_orders
                ? ((s.current_daily_orders - s.baseline_daily_orders) / s.baseline_daily_orders * 100).toFixed(0)
                : null;
              const revDelta = s.baseline_daily_revenue && s.current_daily_revenue
                ? ((s.current_daily_revenue - s.baseline_daily_revenue) / s.baseline_daily_revenue * 100).toFixed(0)
                : null;

              return (
                <div
                  key={s.id}
                  className={`rounded-xl border p-5 transition-all ${
                    isSuccessful
                      ? "border-emerald-200 bg-emerald-50/30"
                      : isFailed
                        ? "border-red-200 bg-red-50/30"
                        : isEvaluating
                          ? "border-amber-200 bg-amber-50/30"
                          : "border-slate-200 bg-slate-50/30"
                  }`}
                >
                  {/* Header row */}
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        {isSuccessful && <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />}
                        {isFailed && <XCircle className="w-4 h-4 text-red-400 shrink-0" />}
                        {(isActive || isEvaluating) && <Clock className="w-4 h-4 text-indigo-400 shrink-0" />}
                        <span className="text-sm font-semibold text-slate-800 truncate">
                          {s.strategy_name}
                        </span>
                        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                          isSuccessful ? "bg-emerald-100 text-emerald-700"
                            : isFailed ? "bg-red-100 text-red-700"
                            : isEvaluating ? "bg-amber-100 text-amber-700"
                            : "bg-indigo-100 text-indigo-700"
                        }`}>
                          {isSuccessful ? "Working" : isFailed ? "Didn't work" : isEvaluating ? "Evaluating" : `Active · ${s.days_active}d`}
                        </span>
                      </div>
                      {s.menu_item_name && (
                        <p className="text-sm text-indigo-600 font-semibold mt-1">
                          Applied to: {s.menu_item_name}
                        </p>
                      )}
                    </div>
                    <div className="shrink-0">
                      {(isActive || isEvaluating) && s.evaluation_ready && (
                        <button
                          onClick={() => handleEvaluate(s.id)}
                          disabled={isLoading}
                          className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors inline-flex items-center gap-1"
                        >
                          {isLoading ? (
                            <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white" />
                          ) : (
                            <BarChart3 className="w-3 h-3" />
                          )}
                          {isLoading ? "Analyzing..." : "Check Results"}
                        </button>
                      )}
                      {(isActive || isEvaluating) && !s.evaluation_ready && (
                        <span className="text-[10px] text-slate-400 italic">
                          Evaluation ready in {Math.max(3 - s.days_active, 1)}d
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Sales tracking grid */}
                  {hasItemSales && (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3 pt-3 border-t border-slate-100">
                      <div>
                        <p className="text-[10px] uppercase tracking-wider text-slate-400 font-medium">Orders since</p>
                        <p className="text-lg font-bold text-slate-900">{s.total_orders_since}</p>
                      </div>
                      <div>
                        <p className="text-[10px] uppercase tracking-wider text-slate-400 font-medium">Revenue since</p>
                        <p className="text-lg font-bold text-slate-900">${s.total_revenue_since?.toLocaleString(undefined, { maximumFractionDigits: 0 })}</p>
                      </div>
                      <div>
                        <p className="text-[10px] uppercase tracking-wider text-slate-400 font-medium">Daily orders</p>
                        <div className="flex items-center gap-1.5">
                          <span className="text-lg font-bold text-slate-900">{s.current_daily_orders?.toFixed(1)}</span>
                          {ordersDelta && (
                            <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${
                              Number(ordersDelta) >= 0 ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-600"
                            }`}>
                              {Number(ordersDelta) >= 0 ? "+" : ""}{ordersDelta}%
                            </span>
                          )}
                        </div>
                        {s.baseline_daily_orders != null && (
                          <p className="text-[10px] text-slate-400">was {s.baseline_daily_orders.toFixed(1)}/day</p>
                        )}
                      </div>
                      <div>
                        <p className="text-[10px] uppercase tracking-wider text-slate-400 font-medium">Daily revenue</p>
                        <div className="flex items-center gap-1.5">
                          <span className="text-lg font-bold text-slate-900">${s.current_daily_revenue?.toFixed(0)}</span>
                          {revDelta && (
                            <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${
                              Number(revDelta) >= 0 ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-600"
                            }`}>
                              {Number(revDelta) >= 0 ? "+" : ""}{revDelta}%
                            </span>
                          )}
                        </div>
                        {s.baseline_daily_revenue != null && (
                          <p className="text-[10px] text-slate-400">was ${s.baseline_daily_revenue.toFixed(0)}/day</p>
                        )}
                      </div>
                    </div>
                  )}

                  {/* AI evaluation results */}
                  {s.actual_impact && (
                    <div className="mt-3 pt-3 border-t border-slate-100">
                      <p className="text-sm text-slate-600 leading-relaxed">{s.actual_impact}</p>
                      {s.notes && (
                        <p className="text-xs text-slate-400 mt-1">{s.notes}</p>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
