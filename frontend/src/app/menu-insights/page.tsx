"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Crown,

  TrendingDown,
  Clock,
  Sparkles,
  Zap,
  ArrowRight,
  Star,
  ShoppingBag,
  Plus,
  Megaphone,
  DollarSign,
  Trash2,
  AlertTriangle,
  Flame,
  BarChart3,
  Lightbulb,
  CheckCircle2,
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
import { motion } from "framer-motion";

import { api } from "@/lib/api";
import { useRestaurant } from "@/context/RestaurantContext";

/* ------------------------------------------------------------------ */
/*  Inline markdown renderer                                            */
/* ------------------------------------------------------------------ */

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
/*  Custom chart tooltip                                                */
/* ------------------------------------------------------------------ */
function DemandTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-lg px-4 py-3 text-sm">
      <p className="font-semibold text-slate-700">{label}</p>
      <p className="text-slate-900 font-bold">{payload[0].value} orders</p>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Helper: format hour                                                 */
/* ------------------------------------------------------------------ */
function formatHour(h: number): string {
  if (h === 0) return "12 AM";
  if (h === 12) return "12 PM";
  return h > 12 ? `${h - 12} PM` : `${h} AM`;
}

/* ------------------------------------------------------------------ */
/*  Main page                                                           */
/* ------------------------------------------------------------------ */
export default function MenuInsightsPage() {
  const { restaurantId } = useRestaurant();

  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [openCategories, setOpenCategories] = useState<Record<string, boolean>>({});
  const router = useRouter();

  const handleReview = (rec: { title: string; reason: string; target: string; type: string }) => {
    const params = new URLSearchParams({
      title: rec.title,
      description: rec.reason,
      target: rec.target,
      source: "menu-insights",
      type: rec.type,
    });
    router.push(`/recommendations?review=${encodeURIComponent(params.toString())}`);
  };

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
        const data = await api.getMenuAnalytics(restaurantId);
        setAnalytics(data);
      } catch (err: any) {
        setError(err.message ?? "Failed to load menu analytics");
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
          <p className="text-slate-400">Loading menu insights...</p>
        </div>
      </div>
    );
  }

  if (error && !analytics) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-10 max-w-lg text-center">
          <div className="w-16 h-16 bg-indigo-50 rounded-full flex items-center justify-center mx-auto mb-5">
            <Sparkles className="w-8 h-8 text-indigo-400" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">
            No menu data yet
          </h2>
          <p className="text-slate-500 mb-6 leading-relaxed">
            Upload your menu and sales data to unlock powerful insights about what sells, what earns, and what to do next.
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
  const topSellers = analytics?.top_sellers ?? [];
  const bottomSellers = analytics?.bottom_sellers ?? [];
  const marginAnalysis = analytics?.margin_analysis ?? [];
  const menuEngineering = analytics?.menu_engineering ?? [];
  const pairAnalysis = (analytics?.pair_analysis ?? []).slice(0, 10);
  const demandTrends = analytics?.demand_trends ?? [];
  const revenueByItem = (analytics?.revenue_by_item ?? []).slice(0, 12);

  // Key business insights
  const topSeller = topSellers[0];
  const bottomSeller = bottomSellers[0];
  const highestMargin = [...marginAnalysis].sort((a: any, b: any) => (b.margin_pct ?? 0) - (a.margin_pct ?? 0))[0];

  // Peak demand - find busiest hour
  const hourlyData = demandTrends
    .filter((d: any) => d.hour_of_day != null)
    .reduce((acc: Record<number, number>, d: any) => {
      acc[d.hour_of_day] = (acc[d.hour_of_day] ?? 0) + (d.qty ?? 0);
      return acc;
    }, {} as Record<number, number>);
  const hourlyChartData = Object.entries(hourlyData)
    .map(([h, qty]) => ({ hour: Number(h), label: formatHour(Number(h)), qty: qty as number }))
    .sort((a, b) => a.hour - b.hour);
  const peakHour = hourlyChartData.length > 0
    ? hourlyChartData.reduce((max, cur) => (cur.qty as number) > (max.qty as number) ? cur : max)
    : null;

  // Top combos from pair analysis
  const topCombos = pairAnalysis
    .filter((p: any) => p.confidence >= 0.15)
    .sort((a: any, b: any) => (b.lift ?? 0) - (a.lift ?? 0))
    .slice(0, 3);

  // Add-on candidates: items that appear as consequents most often
  const addOnCounts: Record<string, number> = {};
  for (const pair of pairAnalysis) {
    for (const item of pair.consequents ?? []) {
      addOnCounts[item] = (addOnCounts[item] ?? 0) + 1;
    }
  }
  const topAddOns = Object.entries(addOnCounts)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5)
    .map(([item, count]) => ({ item, count }));

  // AI recommendation cards from menu engineering
  const stars = menuEngineering.filter((i: any) => i.classification === "Star");
  const puzzles = menuEngineering.filter((i: any) => i.classification === "Puzzle");
  const dogs = menuEngineering.filter((i: any) => i.classification === "Dog");

  const recommendations = [
    ...(topCombos.length > 0
      ? [{
          type: "combo",
          icon: ShoppingBag,
          color: "bg-violet-50 text-violet-600 border-violet-200",
          badgeColor: "bg-violet-100 text-violet-700",
          title: "Create a Combo Deal",
          target: `${topCombos[0].antecedents?.[0]} + ${topCombos[0].consequents?.[0]}`,
          reason: `These are ordered together ${((topCombos[0].confidence ?? 0) * 100).toFixed(0)}% of the time. Bundle them with a small discount to boost order size.`,
          impact: "Increase average order value",
          urgency: "",
        }]
      : []),
    ...(puzzles.length > 0
      ? [{
          type: "promote",
          icon: Megaphone,
          color: "bg-amber-50 text-amber-600 border-amber-200",
          badgeColor: "bg-amber-100 text-amber-700",
          title: "Promote Hidden Gem",
          target: puzzles[0].item,
          reason: `${puzzles[0].item} has great margins ($${Number(puzzles[0].margin).toFixed(2)}/order) but low sales. A social post or menu highlight could boost orders.`,
          impact: "Unlock untapped profit",
          urgency: "",
        }]
      : []),
    ...(stars.length > 0 && highestMargin
      ? [{
          type: "price",
          icon: DollarSign,
          color: "bg-emerald-50 text-emerald-600 border-emerald-200",
          badgeColor: "bg-emerald-100 text-emerald-700",
          title: "Consider a Small Price Bump",
          target: stars[0].item,
          reason: `${stars[0].item} is your top performer with strong demand. A 5-8% price increase is unlikely to hurt volume and will boost revenue.`,
          impact: "Revenue boost with minimal risk",
          urgency: "",
        }]
      : []),
    ...(dogs.length > 0
      ? [{
          type: "waste",
          icon: AlertTriangle,
          color: "bg-orange-50 text-orange-600 border-orange-200",
          badgeColor: "bg-orange-100 text-orange-700",
          title: "Reduce Waste",
          target: dogs[dogs.length - 1].item,
          reason: `${dogs[dogs.length - 1].item} has low sales and low margins. The ingredients are going to waste. Rework the recipe or run a daily special.`,
          impact: "Cut food waste costs",
          urgency: "",
        }]
      : []),
    ...(dogs.length > 1
      ? [{
          type: "remove",
          icon: Trash2,
          color: "bg-red-50 text-red-600 border-red-200",
          badgeColor: "bg-red-100 text-red-700",
          title: "Consider Removing",
          target: dogs[0].item,
          reason: `${dogs[0].item} sells only ${dogs[0].qty_sold} units with thin margins. Dropping it simplifies your kitchen and reduces waste.`,
          impact: "Simpler menu, less waste",
          urgency: "",
        }]
      : []),
    ...(bottomSeller
      ? [{
          type: "improve",
          icon: Lightbulb,
          color: "bg-sky-50 text-sky-600 border-sky-200",
          badgeColor: "bg-sky-100 text-sky-700",
          title: "Improve Underperformer",
          target: bottomSeller.item,
          reason: `${bottomSeller.item} has only ${bottomSeller.qty_sold} orders and $${Number(bottomSeller.revenue).toFixed(0)} revenue this month. Ask AI for creative ideas to boost its appeal — new description, pairing, or repositioning.`,
          impact: "Turn a weak dish into a winner",
          urgency: "",
        }]
      : []),
  ];

  const maxBarQty = Math.max(...hourlyChartData.map(d => d.qty as number), 1);

  return (
    <div className="max-w-[1400px] mx-auto px-2 sm:px-3 py-10 space-y-10">
      {/* ═══════ HEADER ═══════ */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl font-bold text-slate-900">
            Menu Insights & Growth Opportunities
          </h1>
          <p className="text-slate-500 mt-1.5 max-w-xl">
            See what sells, what earns the most, and exactly what actions to take next to grow your restaurant.
          </p>
        </div>
        <div className="flex items-center gap-3" />
      </motion.div>

      {/* ═══════ KEY BUSINESS INSIGHTS ═══════ */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 sm:grid-cols-3 gap-5"
      >
        {/* Top Selling Dish */}
        <motion.div variants={fadeUp} custom={0}
          className="group bg-white rounded-2xl border border-slate-200 shadow-sm p-6 hover:shadow-md hover:border-slate-300 transition-all"
        >
          <div className="flex items-start justify-between">
            <div className="min-w-0">
              <p className="text-sm font-medium text-slate-500">Top Selling Dish</p>
              <p className="text-2xl font-bold text-slate-900 mt-2 truncate">
                {topSeller?.item ?? "—"}
              </p>
              <p className="text-sm text-slate-400 mt-2">
                {topSeller ? `${topSeller.qty_sold} orders this month` : "Upload sales data"}
              </p>
            </div>
            <div className="w-11 h-11 bg-amber-50 rounded-xl flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
              <Crown className="w-5 h-5 text-amber-500" />
            </div>
          </div>
          {topSeller && (
            <div className="mt-3">
              <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full">
                <Flame className="w-3 h-3" /> Best seller
              </span>
            </div>
          )}
        </motion.div>

        {/* Underperforming Dish */}
        <motion.div variants={fadeUp} custom={1}
          className="group bg-white rounded-2xl border border-slate-200 shadow-sm p-6 hover:shadow-md hover:border-slate-300 transition-all"
        >
          <div className="flex items-start justify-between">
            <div className="min-w-0">
              <p className="text-sm font-medium text-slate-500">Needs Attention</p>
              <p className="text-2xl font-bold text-slate-900 mt-2 truncate">
                {bottomSeller?.item ?? "—"}
              </p>
              <p className="text-sm text-slate-400 mt-2">
                {bottomSeller ? `Only ${bottomSeller.qty_sold} orders this month` : "No data yet"}
              </p>
            </div>
            <div className="w-11 h-11 bg-red-50 rounded-xl flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
              <TrendingDown className="w-5 h-5 text-red-400" />
            </div>
          </div>
          {bottomSeller && (
            <div className="mt-3">
              <span className="inline-flex items-center gap-1 text-xs font-semibold text-orange-600 bg-orange-50 px-2.5 py-1 rounded-full">
                <AlertTriangle className="w-3 h-3" /> Low demand
              </span>
            </div>
          )}
        </motion.div>

        {/* Peak Demand Time */}
        <motion.div variants={fadeUp} custom={2}
          className="group bg-white rounded-2xl border border-slate-200 shadow-sm p-6 hover:shadow-md hover:border-slate-300 transition-all"
        >
          <div className="flex items-start justify-between">
            <div className="min-w-0">
              <p className="text-sm font-medium text-slate-500">Peak Demand Time</p>
              <p className="text-2xl font-bold text-slate-900 mt-2">
                {peakHour ? peakHour.label : "—"}
              </p>
              <p className="text-sm text-slate-400 mt-2">
                {peakHour ? `${peakHour.qty} orders in this window` : "No data yet"}
              </p>
            </div>
            <div className="w-11 h-11 bg-violet-50 rounded-xl flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
              <Clock className="w-5 h-5 text-violet-500" />
            </div>
          </div>
          {peakHour && (
            <div className="mt-3">
              <span className="inline-flex items-center gap-1 text-xs font-semibold text-violet-600 bg-violet-50 px-2.5 py-1 rounded-full">
                <Flame className="w-3 h-3" /> Rush hour
              </span>
            </div>
          )}
        </motion.div>
      </motion.div>

      {/* ═══════ DEMAND BY HOUR CHART ═══════ */}
      {hourlyChartData.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
          className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6"
        >
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-slate-900">When Do Customers Order?</h2>
            <p className="text-sm text-slate-400 mt-0.5">Order volume by time of day — staff up during the rush</p>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={hourlyChartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="label" tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={{ stroke: "#e2e8f0" }} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
              <Tooltip content={<DemandTooltip />} />
              <Bar dataKey="qty" radius={[6, 6, 0, 0]}>
                {hourlyChartData.map((entry, idx) => (
                  <Cell
                    key={idx}
                    fill={peakHour && entry.hour === peakHour.hour ? "#8b5cf6" : "#e2e8f0"}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      )}

      {/* ═══════ CUSTOMER ORDER PATTERNS ═══════ */}
      {(topCombos.length > 0 || topAddOns.length > 0) && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.5 }}
        >
          <div className="mb-5">
            <h2 className="text-lg font-semibold text-slate-900">Customer Order Patterns</h2>
            <p className="text-sm text-slate-400 mt-0.5">How your customers are actually ordering</p>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Combos */}
            {topCombos.length > 0 && (
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
                <div className="flex items-center gap-2 mb-5">
                  <ShoppingBag className="w-5 h-5 text-violet-500" />
                  <h3 className="text-base font-semibold text-slate-900">Top Combos</h3>
                </div>
                <p className="text-sm text-slate-400 mb-4">Customers often order these together — great bundle opportunities</p>
                <div className="space-y-3">
                  {topCombos.map((combo: any, i: number) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.5 + i * 0.1 }}
                      className="rounded-xl border border-slate-100 bg-gradient-to-r from-violet-50/50 to-transparent p-4 hover:shadow-sm transition-shadow"
                    >
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-sm font-semibold text-slate-800">
                          {(combo.antecedents ?? []).join(", ")}
                        </span>
                        <span className="text-slate-300">+</span>
                        <span className="text-sm font-semibold text-slate-800">
                          {(combo.consequents ?? []).join(", ")}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-slate-500">
                          Ordered together {((combo.confidence ?? 0) * 100).toFixed(0)}% of the time
                        </span>
                        <span className="inline-flex items-center text-xs font-medium text-violet-600 bg-violet-100 px-2 py-0.5 rounded-full">
                          High demand
                        </span>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {/* Most Common Add-ons */}
            {topAddOns.length > 0 && (
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
                <div className="flex items-center gap-2 mb-5">
                  <Plus className="w-5 h-5 text-emerald-500" />
                  <h3 className="text-base font-semibold text-slate-900">Most Common Add-ons</h3>
                </div>
                <p className="text-sm text-slate-400 mb-4">Items customers add to their order — easy upsell targets</p>
                <div className="space-y-3">
                  {topAddOns.map((addon, i) => {
                    const maxCount = topAddOns[0].count;
                    const pct = maxCount > 0 ? (addon.count / maxCount) * 100 : 0;
                    return (
                      <motion.div
                        key={addon.item}
                        initial={{ opacity: 0, x: 10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.5 + i * 0.1 }}
                        className="flex items-center gap-4"
                      >
                        <span className="w-6 text-center text-xs font-bold text-slate-400">
                          {i + 1}
                        </span>
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium text-slate-800">{addon.item}</span>
                            <span className="text-xs text-slate-400">{addon.count} pairings</span>
                          </div>
                          <div className="w-full bg-slate-100 rounded-full h-2">
                            <motion.div
                              className="bg-emerald-500 h-2 rounded-full"
                              initial={{ width: 0 }}
                              animate={{ width: `${pct}%` }}
                              transition={{ delay: 0.6 + i * 0.1, duration: 0.5 }}
                            />
                          </div>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
                {topAddOns.length > 0 && (
                  <p className="text-xs text-emerald-600 font-medium mt-4">
                    Suggest these as add-ons to increase ticket size
                  </p>
                )}
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* ═══════ REVENUE BY ITEM ═══════ */}
      {revenueByItem.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.5 }}
          className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6"
        >
          <div className="flex items-center gap-2 mb-5">
            <BarChart3 className="w-5 h-5 text-indigo-500" />
            <h2 className="text-lg font-semibold text-slate-900">Revenue by Dish</h2>
          </div>
          <p className="text-sm text-slate-400 mb-4">Where your money is coming from</p>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={revenueByItem} margin={{ top: 5, right: 10, left: 0, bottom: 5 }} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} tickFormatter={(v) => `$${v}`} />
              <YAxis dataKey="item" type="category" tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} width={130} />
              <Tooltip
                formatter={(val: any) => [`$${Number(val).toLocaleString(undefined, { maximumFractionDigits: 0 })}`, "Revenue"]}
                contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 13 }}
              />
              <Bar dataKey="revenue" radius={[0, 6, 6, 0]} fill="#818cf8" />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      )}

      {/* ═══════ AI RECOMMENDATIONS ═══════ */}
      {recommendations.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.5 }}
        >
          <div className="flex items-center gap-2 mb-5">
            <Sparkles className="w-5 h-5 text-indigo-500" />
            <h2 className="text-lg font-semibold text-slate-900">AI Recommendations</h2>
          </div>
          <p className="text-sm text-slate-400 mb-5">Smart actions your AI assistant identified from the data</p>
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5"
          >
            {recommendations.map((rec, i) => {
              const Icon = rec.icon;
              return (
                <motion.div
                  key={i}
                  variants={fadeUp}
                  custom={i}
                  className={`rounded-2xl border p-5 hover:shadow-md transition-all ${rec.color}`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-white/80 shadow-sm">
                      <Icon className="w-5 h-5" />
                    </div>
                    {rec.urgency && (
                      <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${rec.badgeColor}`}>
                        {rec.urgency}
                      </span>
                    )}
                  </div>
                  <h3 className="text-base font-bold text-slate-900 mb-1">
                    {rec.title}
                  </h3>
                  <p className="text-sm font-semibold text-slate-700 mb-2">
                    {rec.target}
                  </p>
                  <p className="text-sm text-slate-500 leading-relaxed mb-4">
                    {rec.reason}
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-400 font-medium">
                      {rec.impact}
                    </span>
                    <button
                      onClick={() => handleReview(rec)}
                      className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 inline-flex items-center gap-1 transition-colors"
                    >
                      Review <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        </motion.div>
      )}

      {/* ═══════ MENU ENGINEERING SUMMARY ═══════ */}
      {menuEngineering.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7, duration: 0.5 }}
          className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6"
        >
          <div className="flex items-center gap-2 mb-2">
            <Star className="w-5 h-5 text-amber-500" />
            <h2 className="text-lg font-semibold text-slate-900">Menu Performance Overview</h2>
          </div>
          <p className="text-sm text-slate-400 mb-5">Every dish falls into one of four categories based on sales and profitability</p>

          {/* Quadrant summary */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
            {[
              { label: "Stars", desc: "High sales, high profit", cls: "Star", color: "bg-emerald-50 border-emerald-200 text-emerald-700" },
              { label: "Workhorses", desc: "High sales, lower profit", cls: "Plow Horse", color: "bg-blue-50 border-blue-200 text-blue-700" },
              { label: "Hidden Gems", desc: "Low sales, high profit", cls: "Puzzle", color: "bg-amber-50 border-amber-200 text-amber-700" },
              { label: "Underperformers", desc: "Low sales, low profit", cls: "Dog", color: "bg-red-50 border-red-200 text-red-700" },
            ].map((q) => {
              const count = menuEngineering.filter((i: any) => i.classification === q.cls).length;
              return (
                <div key={q.cls} className={`rounded-xl border px-4 py-3 ${q.color}`}>
                  <p className="text-2xl font-bold">{count}</p>
                  <p className="text-sm font-semibold mt-0.5">{q.label}</p>
                  <p className="text-xs opacity-75 mt-0.5">{q.desc}</p>
                </div>
              );
            })}
          </div>

          {/* Category accordions */}
          <div className="space-y-3">
            {[
              { label: "Stars", cls: "Star", color: "border-emerald-200 bg-emerald-50/50", headerColor: "bg-emerald-50 border-emerald-200 text-emerald-700", badgeColor: "bg-emerald-100 text-emerald-700" },
              { label: "Workhorses", cls: "Plow Horse", color: "border-blue-200 bg-blue-50/50", headerColor: "bg-blue-50 border-blue-200 text-blue-700", badgeColor: "bg-blue-100 text-blue-700" },
              { label: "Hidden Gems", cls: "Puzzle", color: "border-amber-200 bg-amber-50/50", headerColor: "bg-amber-50 border-amber-200 text-amber-700", badgeColor: "bg-amber-100 text-amber-700" },
              { label: "Underperformers", cls: "Dog", color: "border-red-200 bg-red-50/50", headerColor: "bg-red-50 border-red-200 text-red-700", badgeColor: "bg-red-100 text-red-700" },
            ].map((cat) => {
              const items = menuEngineering.filter((i: any) => i.classification === cat.cls);
              if (items.length === 0) return null;
              const isOpen = openCategories[cat.cls] ?? false;
              return (
                <div key={cat.cls} className={`rounded-xl border overflow-hidden ${cat.color}`}>
                  <button
                    onClick={() => setOpenCategories(prev => ({ ...prev, [cat.cls]: !prev[cat.cls] }))}
                    className={`w-full flex items-center justify-between px-4 py-3 border-b ${cat.headerColor} hover:opacity-90 transition-opacity`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-bold">{cat.label}</span>
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${cat.badgeColor}`}>
                        {items.length} {items.length === 1 ? "item" : "items"}
                      </span>
                    </div>
                    <svg
                      className={`w-4 h-4 transition-transform ${isOpen ? "rotate-180" : ""}`}
                      fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  {isOpen && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 p-3">
                      {items.map((item: any, i: number) => (
                        <div key={i} className="rounded-lg border border-white/60 bg-white/70 p-3">
                          <span className="text-sm font-semibold text-slate-800 block truncate">{item.item}</span>
                          <div className="flex items-center justify-between text-xs text-slate-500 mt-1.5">
                            <span>{item.qty_sold} sold</span>
                            <span>${Number(item.margin).toFixed(2)} margin</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </motion.div>
      )}

      {/* Review navigates to /recommendations */}
    </div>
  );
}
