"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { AlertCard } from "@/components/cards/AlertCard";
import { SimpleBarChart } from "@/components/charts/SimpleBarChart";

function daysLeftColor(days: number): string {
  if (days <= 2) return "bg-red-100 text-red-800";
  if (days <= 5) return "bg-amber-100 text-amber-800";
  if (days <= 10) return "bg-yellow-100 text-yellow-800";
  return "bg-green-100 text-green-800";
}

export default function InventoryInsightsPage() {
  const searchParams = useSearchParams();
  const restaurantId = Number(searchParams.get("restaurant_id") ?? 1);

  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const data = await api.getInventoryAnalytics(restaurantId);
        setAnalytics(data);
      } catch (err: any) {
        setError(err.message ?? "Failed to load inventory analytics");
      } finally {
        setLoading(false);
      }
    })();
  }, [restaurantId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
          <p className="text-gray-500">Loading inventory insights...</p>
        </div>
      </div>
    );
  }

  if (error && !analytics) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="bg-white rounded-xl shadow-sm p-6 max-w-md text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <p className="text-gray-500">No data yet. Upload data to get started.</p>
        </div>
      </div>
    );
  }

  const stockoutRisks = analytics?.stockout_risks ?? [];
  const expiryRisks = analytics?.expiry_risks ?? [];
  const ingredients = analytics?.ingredients ?? [];
  const usageRates = (analytics?.usage_rates ?? []).slice(0, 12);
  const wasteProne = analytics?.waste_prone ?? [];
  const reorderAlerts = analytics?.reorder_alerts ?? [];

  const hasData = stockoutRisks.length > 0 || ingredients.length > 0;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      <h1 className="text-3xl font-bold text-gray-900">Inventory Insights</h1>

      {!hasData && (
        <div className="bg-white rounded-xl shadow-sm p-12 text-center">
          <p className="text-gray-500 text-lg">No inventory data yet. Upload data to get started.</p>
        </div>
      )}

      {/* Risk Alerts */}
      {(stockoutRisks.length > 0 || expiryRisks.length > 0) && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Risk Alerts</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {stockoutRisks.map((alert: any, i: number) => (
              <AlertCard
                key={`stockout-${i}`}
                title="Stockout Risk"
                message={alert.message ?? `${alert.ingredient}: ~${alert.days_left} days remaining at current usage`}
                severity="error"
              />
            ))}
            {expiryRisks.map((alert: any, i: number) => (
              <AlertCard
                key={`expiry-${i}`}
                title="Expiry Risk"
                message={alert.message ?? `${alert.ingredient}: expires in ${alert.days_until_expiry} days`}
                severity="warning"
              />
            ))}
          </div>
        </div>
      )}

      {/* Ingredients Table */}
      {ingredients.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Ingredient Status</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Ingredient</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">Current Stock</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">Daily Usage</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">Projected Days Left</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Status</th>
                </tr>
              </thead>
              <tbody>
                {ingredients.map((ing: any, i: number) => {
                  const daysLeft = ing.projected_days_left ?? ing.days_left ?? 0;
                  return (
                    <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 font-medium text-gray-900">{ing.name ?? ing.ingredient}</td>
                      <td className="py-3 px-4 text-right text-gray-700">
                        {ing.current_stock != null ? `${Number(ing.current_stock).toFixed(1)} ${ing.unit ?? ""}` : "--"}
                      </td>
                      <td className="py-3 px-4 text-right text-gray-700">
                        {ing.daily_usage != null ? `${Number(ing.daily_usage).toFixed(1)} ${ing.unit ?? ""}/day` : "--"}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <span
                          className={`inline-block px-2.5 py-1 rounded-full text-xs font-medium ${daysLeftColor(daysLeft)}`}
                        >
                          {daysLeft.toFixed(0)} days
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        {daysLeft <= 2 && (
                          <span className="text-red-600 font-medium text-xs">CRITICAL</span>
                        )}
                        {daysLeft > 2 && daysLeft <= 5 && (
                          <span className="text-amber-600 font-medium text-xs">LOW</span>
                        )}
                        {daysLeft > 5 && (
                          <span className="text-green-600 font-medium text-xs">OK</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Usage Rate Chart */}
      {usageRates.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Daily Usage Rate (Top Ingredients)</h2>
          <SimpleBarChart data={usageRates} xKey="ingredient" yKey="daily_usage" color="#f59e0b" />
        </div>
      )}

      {/* Waste-Prone Items */}
      {wasteProne.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Waste-Prone Items</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {wasteProne.map((item: any, i: number) => (
              <div
                key={i}
                className="border border-red-200 bg-red-50 rounded-lg p-4"
              >
                <p className="font-medium text-red-900">{item.ingredient ?? item.name}</p>
                <p className="text-sm text-red-700 mt-1">
                  {item.waste_rate != null
                    ? `${(Number(item.waste_rate) * 100).toFixed(1)}% waste rate`
                    : item.reason ?? "High waste detected"}
                </p>
                {item.estimated_loss != null && (
                  <p className="text-sm text-red-600 mt-1 font-medium">
                    ~${Number(item.estimated_loss).toFixed(2)} lost/week
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Reorder Alerts */}
      {reorderAlerts.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Reorder Alerts</h2>
          <div className="space-y-3">
            {reorderAlerts.map((alert: any, i: number) => (
              <div
                key={i}
                className="flex items-center justify-between border border-amber-200 bg-amber-50 rounded-lg p-4"
              >
                <div>
                  <p className="font-medium text-amber-900">{alert.ingredient ?? alert.name}</p>
                  <p className="text-sm text-amber-700 mt-0.5">
                    {alert.message ?? `Reorder ${alert.suggested_quantity ?? ""} ${alert.unit ?? ""} by ${alert.reorder_by ?? "soon"}`}
                  </p>
                </div>
                <span className="shrink-0 bg-amber-200 text-amber-900 text-xs font-medium px-3 py-1 rounded-full">
                  Reorder
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
