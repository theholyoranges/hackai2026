"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import SimpleBarChart from "@/components/charts/SimpleBarChart";

const HEATMAP_BG = [
  "bg-gray-100",
  "bg-emerald-100",
  "bg-emerald-200",
  "bg-emerald-300",
  "bg-emerald-400",
  "bg-emerald-500",
];

function getHeatColor(val: number, max: number): string {
  if (max === 0) return HEATMAP_BG[0];
  const idx = Math.min(Math.floor((val / max) * (HEATMAP_BG.length - 1)), HEATMAP_BG.length - 1);
  return HEATMAP_BG[idx];
}

export default function SocialInsightsPage() {
  
  const restaurantId = 1;

  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const data = await api.getSocialAnalytics(restaurantId);
        setAnalytics(data);
      } catch (err: any) {
        setError(err.message ?? "Failed to load social analytics");
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
          <p className="text-gray-500">Loading social insights...</p>
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

  const engagementByType = analytics?.engagement_by_type ?? [];
  const bestTimes = analytics?.best_posting_times ?? [];
  const trendingItems = analytics?.trending_items ?? [];
  const campaigns = analytics?.campaign_opportunities ?? [];

  const hasData = engagementByType.length > 0 || trendingItems.length > 0;

  // Compute max for heatmap
  let timeMax = 0;
  for (const row of bestTimes) {
    for (const key of Object.keys(row)) {
      if (key !== "day" && typeof row[key] === "number" && row[key] > timeMax) {
        timeMax = row[key];
      }
    }
  }

  const timeSlots = bestTimes.length > 0
    ? Object.keys(bestTimes[0]).filter((k) => k !== "day")
    : [];

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      <h1 className="text-3xl font-bold text-gray-900">Social Insights</h1>

      {!hasData && (
        <div className="bg-white rounded-xl shadow-sm p-12 text-center">
          <p className="text-gray-500 text-lg">No social data yet. Upload data to get started.</p>
        </div>
      )}

      {/* Engagement by Post Type */}
      {engagementByType.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Engagement by Post Type</h2>
          <SimpleBarChart data={engagementByType} xKey="post_type" yKey="avg_engagement" color="#10b981" />
        </div>
      )}

      {/* Best Posting Times */}
      {bestTimes.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Best Posting Times</h2>
          <div className="overflow-x-auto">
            <table className="text-xs">
              <thead>
                <tr>
                  <th className="py-2 px-3 text-left font-medium text-gray-600">Day</th>
                  {timeSlots.map((slot) => (
                    <th key={slot} className="py-2 px-1 text-center font-medium text-gray-600">
                      {slot}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {bestTimes.map((row: any, i: number) => (
                  <tr key={i}>
                    <td className="py-1 px-3 font-medium text-gray-700">{row.day}</td>
                    {timeSlots.map((slot) => {
                      const val = row[slot] ?? 0;
                      const bgColor = getHeatColor(val, timeMax);
                      const textColor = val / timeMax > 0.6 ? "text-white" : "text-gray-700";
                      return (
                        <td key={slot} className="py-1 px-1">
                          <div
                            className={`w-10 h-8 rounded flex items-center justify-center ${bgColor} ${textColor}`}
                            title={`${row.day} ${slot}: ${val}`}
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

      {/* Trending Items to Feature */}
      {trendingItems.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Trending Items to Feature</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {trendingItems.map((item: any, i: number) => (
              <div
                key={i}
                className="border border-emerald-200 bg-emerald-50 rounded-lg p-4"
              >
                <p className="font-medium text-emerald-900">{item.item_name ?? item.name}</p>
                {item.trend_score != null && (
                  <div className="flex items-center gap-2 mt-2">
                    <div className="flex-1 bg-emerald-200 rounded-full h-2">
                      <div
                        className="bg-emerald-600 h-2 rounded-full"
                        style={{ width: `${Math.min(Number(item.trend_score) * 100, 100)}%` }}
                      />
                    </div>
                    <span className="text-xs text-emerald-700 font-medium">
                      {(Number(item.trend_score) * 100).toFixed(0)}%
                    </span>
                  </div>
                )}
                {item.reason && (
                  <p className="text-sm text-emerald-700 mt-2">{item.reason}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Campaign Opportunities */}
      {campaigns.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Campaign Opportunities</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {campaigns.map((campaign: any, i: number) => (
              <div
                key={i}
                className="border border-gray-200 rounded-lg p-5 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <h3 className="font-semibold text-gray-900">{campaign.title ?? campaign.name}</h3>
                  {campaign.priority && (
                    <span
                      className={`text-xs font-medium px-2.5 py-1 rounded-full ${
                        campaign.priority === "high"
                          ? "bg-red-100 text-red-800"
                          : campaign.priority === "medium"
                          ? "bg-amber-100 text-amber-800"
                          : "bg-gray-100 text-gray-700"
                      }`}
                    >
                      {campaign.priority}
                    </span>
                  )}
                </div>
                {campaign.description && (
                  <p className="text-sm text-gray-600 mt-2">{campaign.description}</p>
                )}
                {campaign.expected_impact && (
                  <p className="text-sm text-indigo-600 mt-2 font-medium">
                    Expected impact: {campaign.expected_impact}
                  </p>
                )}
                {campaign.suggested_items && (
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {(Array.isArray(campaign.suggested_items)
                      ? campaign.suggested_items
                      : [campaign.suggested_items]
                    ).map((item: string, j: number) => (
                      <span
                        key={j}
                        className="bg-indigo-50 text-indigo-700 text-xs px-2 py-0.5 rounded"
                      >
                        {item}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
