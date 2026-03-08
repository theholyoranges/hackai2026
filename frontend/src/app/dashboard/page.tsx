"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import StatCard from "@/components/cards/StatCard";
import RecommendationCard from "@/components/cards/RecommendationCard";
import AlertCard from "@/components/cards/AlertCard";
import SimpleLineChart from "@/components/charts/SimpleLineChart";

export default function DashboardPage() {
  const restaurantId = 1;

  const [dashboard, setDashboard] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getDashboard(restaurantId);
      setDashboard(data);
    } catch (err: any) {
      setError(err.message ?? "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, [restaurantId]);

  const handleGenerateGrowthPlan = async () => {
    try {
      setGenerating(true);
      await api.generateRecommendations(restaurantId);
      await fetchDashboard();
    } catch (err: any) {
      setError(err.message ?? "Failed to generate growth plan");
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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
          <p className="text-gray-500">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error && !dashboard) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="bg-white rounded-xl shadow-sm p-6 max-w-md text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <p className="text-gray-500">No data yet. Upload data to get started.</p>
        </div>
      </div>
    );
  }

  const revenueTrend = dashboard?.revenue_trend ?? [];
  const topItem = dashboard?.top_item;
  const bottomItem = dashboard?.bottom_item;
  const highMargin = dashboard?.high_margin_opportunities ?? [];
  const wasteAlerts = dashboard?.waste_alerts ?? [];
  const stockoutAlerts = dashboard?.stockout_alerts ?? [];
  const recommendations = dashboard?.top_recommendations ?? [];

  // Compute summary stats from available data
  const totalRevenue = revenueTrend.reduce((sum: number, d: any) => sum + (d.revenue ?? 0), 0);
  const avgMargin = highMargin.length > 0
    ? highMargin.reduce((sum: number, m: any) => sum + (m.margin_pct ?? 0), 0) / highMargin.length
    : null;
  const itemsAtRisk = stockoutAlerts.length;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <button
          onClick={handleGenerateGrowthPlan}
          disabled={generating}
          className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-medium px-6 py-2.5 rounded-lg transition-colors flex items-center gap-2"
        >
          {generating && (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
          )}
          {generating ? "Generating..." : "Generate Growth Plan"}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Revenue"
          value={`$${totalRevenue.toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
          subtitle={`${revenueTrend.length} days`}
        />
        <StatCard
          title="Top Item"
          value={topItem?.item ?? "--"}
          subtitle={topItem ? `$${Number(topItem.revenue).toLocaleString()} revenue` : ""}
        />
        <StatCard
          title="Avg Margin"
          value={avgMargin != null ? `${avgMargin.toFixed(1)}%` : "--"}
          subtitle="Top margin items"
        />
        <StatCard
          title="Items at Risk"
          value={itemsAtRisk}
          subtitle="Low stock alerts"
          trend={itemsAtRisk > 0 ? "down" : undefined}
          trendValue={itemsAtRisk > 0 ? "Needs attention" : undefined}
        />
      </div>

      {/* Revenue Trend */}
      {revenueTrend.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Revenue Trend</h2>
          <SimpleLineChart data={revenueTrend} xKey="date" yKey="revenue" color="#4f46e5" />
        </div>
      )}

      {/* Recommendations & Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Recommendations */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Top Recommendations</h2>
          {recommendations.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm p-6 text-gray-500 text-center">
              No recommendations yet. Click &quot;Generate Growth Plan&quot; to get started.
            </div>
          ) : (
            recommendations.slice(0, 3).map((rec: any) => (
              <RecommendationCard
                key={rec.id}
                recommendation={rec}
                onAccept={() => handleAccept(rec.id)}
                onReject={() => handleReject(rec.id)}
              />
            ))
          )}
        </div>

        {/* Alerts */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Alerts</h2>

          {wasteAlerts.length === 0 && stockoutAlerts.length === 0 && (
            <div className="bg-white rounded-xl shadow-sm p-6 text-gray-500 text-center">
              No active alerts.
            </div>
          )}

          {wasteAlerts.map((alert: any, i: number) => (
            <AlertCard
              key={`waste-${i}`}
              title="Waste Risk"
              message={`${alert.ingredient}: ${alert.waste_reasons?.join(", ") ?? "potential waste"} (${alert.projected_days_left?.toFixed(0) ?? "?"} days of stock)`}
              severity="warning"
            />
          ))}

          {stockoutAlerts.map((alert: any, i: number) => (
            <AlertCard
              key={`stockout-${i}`}
              title="Stockout Risk"
              message={`${alert.ingredient}: ${alert.projected_days_left?.toFixed(1) ?? "?"} days remaining (${alert.quantity_on_hand} ${alert.unit} left)`}
              severity="danger"
            />
          ))}
        </div>
      </div>
    </div>
  );
}
