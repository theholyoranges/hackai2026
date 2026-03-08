"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { StatCard } from "@/components/cards/StatCard";
import { RecommendationCard } from "@/components/cards/RecommendationCard";
import { AlertCard } from "@/components/cards/AlertCard";
import { SimpleLineChart } from "@/components/charts/SimpleLineChart";

export default function DashboardPage() {
  const searchParams = useSearchParams();
  const restaurantId = Number(searchParams.get("restaurant_id") ?? 1);

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

  const summary = dashboard?.summary ?? {};
  const revenueTrend = dashboard?.revenue_trend ?? [];
  const recommendations = dashboard?.top_recommendations ?? [];
  const wasteAlerts = dashboard?.waste_alerts ?? [];
  const stockoutAlerts = dashboard?.stockout_alerts ?? [];

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
          value={summary.total_revenue != null ? `$${Number(summary.total_revenue).toLocaleString()}` : "--"}
          subtitle={summary.revenue_period ?? ""}
          trend={summary.revenue_trend}
        />
        <StatCard
          title="Top Item"
          value={summary.top_item ?? "--"}
          subtitle={summary.top_item_revenue ? `$${Number(summary.top_item_revenue).toLocaleString()} revenue` : ""}
        />
        <StatCard
          title="Avg Margin"
          value={summary.avg_margin != null ? `${(Number(summary.avg_margin) * 100).toFixed(1)}%` : "--"}
          subtitle="Across all items"
          trend={summary.margin_trend}
        />
        <StatCard
          title="Items at Risk"
          value={summary.items_at_risk ?? 0}
          subtitle="Low stock or expiring"
          trend={summary.items_at_risk > 0 ? { direction: "down" as const, value: "Needs attention" } : undefined}
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
              No recommendations yet. Click "Generate Growth Plan" to get started.
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
              message={alert.message ?? `${alert.ingredient}: ${alert.reason}`}
              severity="warning"
            />
          ))}

          {stockoutAlerts.map((alert: any, i: number) => (
            <AlertCard
              key={`stockout-${i}`}
              title="Stockout Risk"
              message={alert.message ?? `${alert.ingredient}: ${alert.days_left} days remaining`}
              severity="error"
            />
          ))}
        </div>
      </div>
    </div>
  );
}
