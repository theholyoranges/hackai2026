"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import SimpleBarChart from "@/components/charts/SimpleBarChart";

const QUADRANT_COLORS: Record<string, string> = {
  Star: "bg-green-100 text-green-800",
  Puzzle: "bg-yellow-100 text-yellow-800",
  "Plow Horse": "bg-blue-100 text-blue-800",
  Dog: "bg-red-100 text-red-800",
};

const HEATMAP_COLORS = [
  "bg-gray-100",
  "bg-indigo-100",
  "bg-indigo-200",
  "bg-indigo-300",
  "bg-indigo-400",
  "bg-indigo-500",
  "bg-indigo-600",
];

function getHeatmapColor(value: number, max: number): string {
  if (max === 0) return HEATMAP_COLORS[0];
  const idx = Math.min(Math.floor((value / max) * (HEATMAP_COLORS.length - 1)), HEATMAP_COLORS.length - 1);
  return HEATMAP_COLORS[idx];
}

export default function MenuInsightsPage() {
  
  const restaurantId = 1;

  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const data = await api.getMenuAnalytics(restaurantId);
        setAnalytics(data);
      } catch (err: any) {
        setError(err.message ?? "Failed to load menu analytics");
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
          <p className="text-gray-500">Loading menu insights...</p>
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

  const revenueByItem = (analytics?.revenue_by_item ?? []).slice(0, 15);
  const menuEngineering = analytics?.menu_engineering ?? [];
  const pairAnalysis = analytics?.pair_analysis ?? [];
  const categoryPerformance = analytics?.category_performance ?? [];
  const demandHeatmap = analytics?.demand_heatmap ?? [];

  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const hours = Array.from({ length: 15 }, (_, i) => i + 8); // 8 AM to 10 PM

  let heatmapMax = 0;
  if (demandHeatmap.length > 0) {
    for (const row of demandHeatmap) {
      for (const h of hours) {
        const val = row[`h${h}`] ?? row[h] ?? 0;
        if (val > heatmapMax) heatmapMax = val;
      }
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      <h1 className="text-3xl font-bold text-gray-900">Menu Insights</h1>

      {/* Revenue by Item */}
      {revenueByItem.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Revenue by Item (Top 15)</h2>
          <SimpleBarChart data={revenueByItem} xKey="item_name" yKey="revenue" color="#4f46e5" />
        </div>
      )}

      {/* Menu Engineering Matrix */}
      {menuEngineering.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Menu Engineering Matrix</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Item</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Category</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">Popularity</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">Profitability</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Quadrant</th>
                </tr>
              </thead>
              <tbody>
                {menuEngineering.map((item: any, i: number) => (
                  <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4 font-medium text-gray-900">{item.item_name}</td>
                    <td className="py-3 px-4 text-gray-600">{item.category ?? "--"}</td>
                    <td className="py-3 px-4 text-right text-gray-700">
                      {item.popularity != null ? Number(item.popularity).toFixed(1) : "--"}
                    </td>
                    <td className="py-3 px-4 text-right text-gray-700">
                      {item.profitability != null ? `$${Number(item.profitability).toFixed(2)}` : "--"}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-block px-2.5 py-1 rounded-full text-xs font-medium ${
                          QUADRANT_COLORS[item.quadrant] ?? "bg-gray-100 text-gray-700"
                        }`}
                      >
                        {item.quadrant ?? "Unknown"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Pair Analysis */}
      {pairAnalysis.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Pair Analysis</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Item A</th>
                  <th className="text-center py-3 px-4 font-medium text-gray-600"></th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Item B</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">Confidence</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">Support</th>
                </tr>
              </thead>
              <tbody>
                {pairAnalysis.map((pair: any, i: number) => (
                  <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4 font-medium text-gray-900">{pair.item_a}</td>
                    <td className="py-3 px-4 text-center text-gray-400">&rarr;</td>
                    <td className="py-3 px-4 font-medium text-gray-900">{pair.item_b}</td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <div className="w-16 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-indigo-500 h-2 rounded-full"
                            style={{ width: `${(pair.confidence ?? 0) * 100}%` }}
                          />
                        </div>
                        <span className="text-gray-700">{((pair.confidence ?? 0) * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-right text-gray-700">
                      {((pair.support ?? 0) * 100).toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Category Performance */}
      {categoryPerformance.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Category Performance</h2>
          <SimpleBarChart data={categoryPerformance} xKey="category" yKey="revenue" color="#0ea5e9" />
        </div>
      )}

      {/* Demand Heatmap */}
      {demandHeatmap.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Demand Trends (Day x Hour)</h2>
          <div className="overflow-x-auto">
            <table className="text-xs">
              <thead>
                <tr>
                  <th className="py-2 px-3 text-left font-medium text-gray-600">Day</th>
                  {hours.map((h) => (
                    <th key={h} className="py-2 px-1 text-center font-medium text-gray-600">
                      {h > 12 ? `${h - 12}p` : h === 12 ? "12p" : `${h}a`}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {demandHeatmap.map((row: any, di: number) => (
                  <tr key={di}>
                    <td className="py-1 px-3 font-medium text-gray-700">{row.day ?? days[di]}</td>
                    {hours.map((h) => {
                      const val = row[`h${h}`] ?? row[h] ?? 0;
                      const colorClass = getHeatmapColor(val, heatmapMax);
                      const textColor = val / heatmapMax > 0.6 ? "text-white" : "text-gray-700";
                      return (
                        <td key={h} className="py-1 px-1">
                          <div
                            className={`w-8 h-8 rounded flex items-center justify-center ${colorClass} ${textColor}`}
                            title={`${row.day ?? days[di]} ${h}:00 - ${val} orders`}
                          >
                            {val}
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty State */}
      {revenueByItem.length === 0 && menuEngineering.length === 0 && (
        <div className="bg-white rounded-xl shadow-sm p-12 text-center">
          <p className="text-gray-500 text-lg">No menu data yet. Upload data to get started.</p>
        </div>
      )}
    </div>
  );
}
