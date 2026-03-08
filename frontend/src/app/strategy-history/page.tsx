"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { useRestaurant } from "@/context/RestaurantContext";

const STATUS_TABS = ["All", "active", "successful", "failed", "archived"];

const STATUS_COLORS: Record<string, string> = {
  active: "bg-blue-100 text-blue-800",
  successful: "bg-green-100 text-green-800",
  completed: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
  archived: "bg-gray-100 text-gray-600",
  pending: "bg-amber-100 text-amber-800",
};

export default function StrategyHistoryPage() {
  
  const { restaurantId } = useRestaurant();

  const [strategies, setStrategies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("All");

  useEffect(() => {
    (async () => {
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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
          <p className="text-gray-500">Loading strategy history...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      <h1 className="text-3xl font-bold text-gray-900">Strategy History</h1>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex flex-wrap gap-2">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab
                ? "bg-indigo-600 text-white"
                : "bg-white text-gray-700 border border-gray-200 hover:bg-gray-50"
            }`}
          >
            {tab === "All" ? "All" : tab.charAt(0).toUpperCase() + tab.slice(1)}
            {tab !== "All" && (
              <span className="ml-1.5 text-xs opacity-70">
                ({strategies.filter((s) => s.status === tab).length})
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Empty State */}
      {filtered.length === 0 && (
        <div className="bg-white rounded-xl shadow-sm p-12 text-center">
          <p className="text-gray-500 text-lg">
            {strategies.length === 0
              ? "No strategies yet. Accept recommendations to create strategies."
              : "No strategies match this filter."}
          </p>
        </div>
      )}

      {/* Strategy Timeline / Table */}
      {filtered.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Strategy</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Status</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Created</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Updated</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Evidence</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Outcome</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((strategy: any, i: number) => (
                  <tr key={strategy.id ?? i} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-4 px-4">
                      <p className="font-medium text-gray-900">{strategy.name ?? strategy.title}</p>
                      {strategy.description && (
                        <p className="text-xs text-gray-500 mt-1 max-w-sm truncate">{strategy.description}</p>
                      )}
                    </td>
                    <td className="py-4 px-4">
                      <span
                        className={`inline-block px-2.5 py-1 rounded-full text-xs font-medium ${
                          STATUS_COLORS[strategy.status] ?? "bg-gray-100 text-gray-700"
                        }`}
                      >
                        {strategy.status ?? "unknown"}
                      </span>
                    </td>
                    <td className="py-4 px-4 text-gray-600">
                      {strategy.created_at
                        ? new Date(strategy.created_at).toLocaleDateString()
                        : "--"}
                    </td>
                    <td className="py-4 px-4 text-gray-600">
                      {strategy.updated_at
                        ? new Date(strategy.updated_at).toLocaleDateString()
                        : "--"}
                    </td>
                    <td className="py-4 px-4 text-gray-600 max-w-xs">
                      {strategy.evidence_summary ? (
                        <p className="text-xs truncate" title={strategy.evidence_summary}>
                          {strategy.evidence_summary}
                        </p>
                      ) : strategy.evidence ? (
                        <p className="text-xs truncate" title={String(strategy.evidence)}>
                          {typeof strategy.evidence === "string"
                            ? strategy.evidence
                            : JSON.stringify(strategy.evidence).slice(0, 80)}
                        </p>
                      ) : (
                        "--"
                      )}
                    </td>
                    <td className="py-4 px-4">
                      {strategy.outcome_metrics ? (
                        <div className="space-y-1">
                          {typeof strategy.outcome_metrics === "object" ? (
                            Object.entries(strategy.outcome_metrics).map(([key, val]) => (
                              <p key={key} className="text-xs text-gray-700">
                                <span className="font-medium">{key}:</span> {String(val)}
                              </p>
                            ))
                          ) : (
                            <p className="text-xs text-gray-700">{String(strategy.outcome_metrics)}</p>
                          )}
                        </div>
                      ) : strategy.outcome ? (
                        <p className="text-xs text-gray-700">{String(strategy.outcome)}</p>
                      ) : (
                        <span className="text-gray-400 text-xs">Pending</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Timeline View */}
      {filtered.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Timeline</h2>
          <div className="relative">
            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />
            {filtered.map((strategy: any, i: number) => (
              <div key={strategy.id ?? i} className="relative pl-10 pb-8">
                <div
                  className={`absolute left-2.5 w-3 h-3 rounded-full top-1.5 ${
                    strategy.status === "successful" || strategy.status === "completed"
                      ? "bg-green-500"
                      : strategy.status === "active"
                      ? "bg-blue-500"
                      : strategy.status === "failed"
                      ? "bg-red-500"
                      : "bg-gray-400"
                  }`}
                />
                <div className="bg-white rounded-lg border border-gray-200 p-4">
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="font-medium text-gray-900">{strategy.name ?? strategy.title}</h3>
                    <span
                      className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                        STATUS_COLORS[strategy.status] ?? "bg-gray-100 text-gray-700"
                      }`}
                    >
                      {strategy.status}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500">
                    {strategy.created_at
                      ? new Date(strategy.created_at).toLocaleDateString("en-US", {
                          year: "numeric",
                          month: "short",
                          day: "numeric",
                        })
                      : ""}
                    {strategy.updated_at && strategy.updated_at !== strategy.created_at
                      ? ` - ${new Date(strategy.updated_at).toLocaleDateString("en-US", {
                          year: "numeric",
                          month: "short",
                          day: "numeric",
                        })}`
                      : ""}
                  </p>
                  {strategy.description && (
                    <p className="text-sm text-gray-600 mt-2">{strategy.description}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
