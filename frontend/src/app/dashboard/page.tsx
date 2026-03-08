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
  Activity,
  CheckCircle2,
  XCircle,
  Clock,
  BarChart3,
  Star,
  CloudRain,
  MapPin,
} from "lucide-react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
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
/*  Custom Tooltips                                                    */
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

function PeakTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-lg px-4 py-3 text-sm">
      <p className="font-semibold text-slate-700">{label}</p>
      <p className="text-lg font-bold text-slate-900">{payload[0].value} orders</p>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Hardcoded Google Reviews                                           */
/* ------------------------------------------------------------------ */
const GOOGLE_REVIEWS = [
  {
    name: "Priya S.",
    rating: 5,
    date: "2 days ago",
    text: "Amazing butter chicken! Best Indian food in Richardson. Will definitely come back.",
    source: "Google",
  },
  {
    name: "Mike T.",
    rating: 4,
    date: "4 days ago",
    text: "Great flavors and generous portions. Naan was fresh. Service was a little slow during peak hours but food made up for it.",
    source: "Google",
  },
  {
    name: "Sarah L.",
    rating: 5,
    date: "1 week ago",
    text: "My go-to spot for Indian food. The mango lassi is perfect and the biryani is incredible. Very clean restaurant too.",
    source: "Google",
  },
  {
    name: "David R.",
    rating: 3,
    date: "1 week ago",
    text: "Food was decent but took 40 minutes during lunch. They seem understaffed. The tikka masala was good though.",
    source: "Google",
  },
  {
    name: "Jessica K.",
    rating: 5,
    date: "2 weeks ago",
    text: "Ordered delivery in the rain and everything arrived hot and fresh. The paneer tikka is unreal. 10/10 recommend.",
    source: "Google",
  },
];

/* ------------------------------------------------------------------ */
/*  Hardcoded Peak Hours                                               */
/* ------------------------------------------------------------------ */
const PEAK_HOURS = [
  { hour: "10am", orders: 8 },
  { hour: "11am", orders: 22 },
  { hour: "12pm", orders: 45 },
  { hour: "1pm", orders: 52 },
  { hour: "2pm", orders: 28 },
  { hour: "3pm", orders: 12 },
  { hour: "4pm", orders: 9 },
  { hour: "5pm", orders: 18 },
  { hour: "6pm", orders: 38 },
  { hour: "7pm", orders: 55 },
  { hour: "8pm", orders: 48 },
  { hour: "9pm", orders: 30 },
  { hour: "10pm", orders: 15 },
];

/* ------------------------------------------------------------------ */
/*  Main Dashboard                                                     */
/* ------------------------------------------------------------------ */
export default function DashboardPage() {
  const { restaurantId } = useRestaurant();

  const [dashboard, setDashboard] = useState<any>(null);
  const [restaurantName, setRestaurantName] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
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
  }, [restaurantId]);

  const handleEvaluate = async (historyId: number) => {
    setEvaluatingId(historyId);
    try {
      await api.evaluateStrategy(historyId);
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
          <p className="text-slate-400 text-base">Loading your dashboard...</p>
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
            Hello! Welcome to BistroBrain.
          </h2>
          <p className="text-slate-500 mb-6 leading-relaxed text-base">
            We don&apos;t have any data for this restaurant yet. Upload your menu, inventory, and sales to unlock AI-powered insights.
          </p>
          <Link
            href="/upload"
            className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6 py-3 rounded-xl transition-colors text-base shadow-sm"
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

  const totalRevenue = revenueTrend.reduce(
    (sum: number, d: any) => sum + (d.revenue ?? 0), 0
  );

  const chartData =
    chartView === "weekly"
      ? aggregateWeekly(revenueTrend)
      : chartView === "monthly"
        ? aggregateMonthly(revenueTrend)
        : revenueTrend;

  const displayName = restaurantName
    ? restaurantName.charAt(0).toUpperCase() + restaurantName.slice(1)
    : "your restaurant";

  const avgRating = (GOOGLE_REVIEWS.reduce((s, r) => s + r.rating, 0) / GOOGLE_REVIEWS.length).toFixed(1);

  return (
    <div className="max-w-[1400px] mx-auto px-2 sm:px-3 py-8 space-y-8">
      {/* ═══════ Header ═══════ */}
      <div>
        <h1 className="text-4xl font-bold text-slate-900">
          Welcome back, {displayName}!
        </h1>
        <p className="text-slate-500 mt-1.5 text-base">
          Here is what your AI assistant is seeing today.
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-600 text-base">
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

        {/* Google Rating */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500">Google Rating</p>
              <p className="text-3xl font-bold text-slate-900 mt-2">{avgRating}</p>
              <p className="text-xs text-slate-400 mt-3">{GOOGLE_REVIEWS.length} recent reviews</p>
            </div>
            <div className="w-11 h-11 bg-yellow-50 rounded-xl flex items-center justify-center">
              <Star className="w-5 h-5 text-yellow-500" />
            </div>
          </div>
        </div>

        {/* Local Context */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500">Local Pulse</p>
              <p className="text-lg font-bold text-slate-900 mt-2 flex items-center gap-1.5">
                <CloudRain className="w-4 h-4 text-sky-500" /> Rainy Week
              </p>
              <p className="text-xs text-slate-400 mt-3 flex items-center gap-1">
                <MapPin className="w-3 h-3" /> Richardson, TX
              </p>
            </div>
            <div className="w-11 h-11 bg-sky-50 rounded-xl flex items-center justify-center">
              <CloudRain className="w-5 h-5 text-sky-500" />
            </div>
          </div>
        </div>
      </div>

      {/* ═══════ Sales Trend + Peak Hours ═══════ */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sales Trend - 2/3 width */}
        {revenueTrend.length > 0 && (
          <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-slate-900">Your Sales Trend</h2>
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
                    className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
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
                <XAxis dataKey="date" tick={{ fontSize: 12, fill: "#94a3b8" }} axisLine={{ stroke: "#e2e8f0" }} tickLine={false} />
                <YAxis tick={{ fontSize: 12, fill: "#94a3b8" }} axisLine={false} tickLine={false} tickFormatter={(v) => `$${v}`} />
                <Tooltip content={<SalesTooltip />} />
                <Line type="monotone" dataKey="revenue" stroke="#8b5cf6" strokeWidth={2.5} dot={chartView !== "daily"} activeDot={{ r: 6, fill: "#8b5cf6", stroke: "#fff", strokeWidth: 2 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Peak Hours - 1/3 width */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <h2 className="text-xl font-semibold text-slate-900 mb-1">Peak Hours</h2>
          <p className="text-sm text-slate-400 mb-5">Orders by hour of day</p>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={PEAK_HOURS} margin={{ top: 5, right: 5, left: -10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="hour" tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
              <Tooltip content={<PeakTooltip />} />
              <Bar dataKey="orders" radius={[6, 6, 0, 0]}>
                {PEAK_HOURS.map((entry, i) => (
                  <Cell key={i} fill={entry.orders >= 40 ? "#8b5cf6" : entry.orders >= 25 ? "#a78bfa" : "#ddd6fe"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="flex items-center gap-4 mt-3 text-xs text-slate-400">
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-[#8b5cf6]" /> Peak</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-[#a78bfa]" /> Busy</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-[#ddd6fe]" /> Quiet</span>
          </div>
        </div>
      </div>

      {/* ═══════ Google Reviews ═══════ */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">Recent Google Reviews</h2>
            <p className="text-sm text-slate-400 mt-0.5">What customers are saying about you</p>
          </div>
          <div className="flex items-center gap-1.5">
            <Star className="w-5 h-5 text-yellow-400 fill-yellow-400" />
            <span className="text-xl font-bold text-slate-900">{avgRating}</span>
            <span className="text-sm text-slate-400">/ 5</span>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {GOOGLE_REVIEWS.map((review, i) => (
            <div key={i} className="rounded-xl border border-slate-100 bg-slate-50/50 p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold text-slate-800">{review.name}</span>
                <span className="text-xs text-slate-400">{review.date}</span>
              </div>
              <div className="flex items-center gap-0.5 mb-2">
                {Array.from({ length: 5 }).map((_, j) => (
                  <Star key={j} className={`w-3.5 h-3.5 ${j < review.rating ? "text-yellow-400 fill-yellow-400" : "text-slate-200"}`} />
                ))}
              </div>
              <p className="text-sm text-slate-600 leading-relaxed">{review.text}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ═══════ Strategy Tracker ═══════ */}
      {activeStrategies.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center gap-2 mb-5">
            <Activity className="w-5 h-5 text-indigo-500" />
            <h2 className="text-xl font-semibold text-slate-900">Your Active Strategies</h2>
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
                    isSuccessful ? "border-emerald-200 bg-emerald-50/30"
                      : isFailed ? "border-red-200 bg-red-50/30"
                      : isEvaluating ? "border-amber-200 bg-amber-50/30"
                      : "border-slate-200 bg-slate-50/30"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        {isSuccessful && <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />}
                        {isFailed && <XCircle className="w-4 h-4 text-red-400 shrink-0" />}
                        {(isActive || isEvaluating) && <Clock className="w-4 h-4 text-indigo-400 shrink-0" />}
                        <span className="text-base font-semibold text-slate-800 truncate">{s.strategy_name}</span>
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                          isSuccessful ? "bg-emerald-100 text-emerald-700"
                            : isFailed ? "bg-red-100 text-red-700"
                            : isEvaluating ? "bg-amber-100 text-amber-700"
                            : "bg-indigo-100 text-indigo-700"
                        }`}>
                          {isSuccessful ? "Working" : isFailed ? "Didn't work" : isEvaluating ? "Evaluating" : `Active · ${s.days_active}d`}
                        </span>
                      </div>
                      {s.menu_item_name && (
                        <p className="text-sm text-indigo-600 font-semibold mt-1">Applied to: {s.menu_item_name}</p>
                      )}
                    </div>
                    <div className="shrink-0">
                      {(isActive || isEvaluating) && s.evaluation_ready && (
                        <button
                          onClick={() => handleEvaluate(s.id)}
                          disabled={isLoading}
                          className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white text-sm font-semibold px-3 py-1.5 rounded-lg transition-colors inline-flex items-center gap-1"
                        >
                          {isLoading ? <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white" /> : <BarChart3 className="w-3 h-3" />}
                          {isLoading ? "Analyzing..." : "Check Results"}
                        </button>
                      )}
                      {(isActive || isEvaluating) && !s.evaluation_ready && (
                        <span className="text-xs text-slate-400 italic">Evaluation ready in {Math.max(3 - s.days_active, 1)}d</span>
                      )}
                    </div>
                  </div>

                  {hasItemSales && (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3 pt-3 border-t border-slate-100">
                      <div>
                        <p className="text-xs uppercase tracking-wider text-slate-400 font-medium">Orders since</p>
                        <p className="text-xl font-bold text-slate-900">{s.total_orders_since}</p>
                      </div>
                      <div>
                        <p className="text-xs uppercase tracking-wider text-slate-400 font-medium">Revenue since</p>
                        <p className="text-xl font-bold text-slate-900">${s.total_revenue_since?.toLocaleString(undefined, { maximumFractionDigits: 0 })}</p>
                      </div>
                      <div>
                        <p className="text-xs uppercase tracking-wider text-slate-400 font-medium">Daily orders</p>
                        <div className="flex items-center gap-1.5">
                          <span className="text-xl font-bold text-slate-900">{s.current_daily_orders?.toFixed(1)}</span>
                          {ordersDelta && (
                            <span className={`text-xs font-semibold px-1.5 py-0.5 rounded-full ${Number(ordersDelta) >= 0 ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-600"}`}>
                              {Number(ordersDelta) >= 0 ? "+" : ""}{ordersDelta}%
                            </span>
                          )}
                        </div>
                        {s.baseline_daily_orders != null && <p className="text-xs text-slate-400">was {s.baseline_daily_orders.toFixed(1)}/day</p>}
                      </div>
                      <div>
                        <p className="text-xs uppercase tracking-wider text-slate-400 font-medium">Daily revenue</p>
                        <div className="flex items-center gap-1.5">
                          <span className="text-xl font-bold text-slate-900">${s.current_daily_revenue?.toFixed(0)}</span>
                          {revDelta && (
                            <span className={`text-xs font-semibold px-1.5 py-0.5 rounded-full ${Number(revDelta) >= 0 ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-600"}`}>
                              {Number(revDelta) >= 0 ? "+" : ""}{revDelta}%
                            </span>
                          )}
                        </div>
                        {s.baseline_daily_revenue != null && <p className="text-xs text-slate-400">was ${s.baseline_daily_revenue.toFixed(0)}/day</p>}
                      </div>
                    </div>
                  )}

                  {s.actual_impact && (
                    <div className="mt-3 pt-3 border-t border-slate-100">
                      <p className="text-sm text-slate-600 leading-relaxed">{s.actual_impact}</p>
                      {s.notes && <p className="text-xs text-slate-400 mt-1">{s.notes}</p>}
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
