"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import RecommendationCard from "@/components/cards/RecommendationCard";

const CATEGORIES = ["All", "menu", "inventory", "marketing", "pricing", "operations"];

const URGENCY_COLORS: Record<string, string> = {
  high: "bg-red-100 text-red-800",
  medium: "bg-amber-100 text-amber-800",
  low: "bg-green-100 text-green-800",
};

export default function RecommendationsPage() {
  
  const restaurantId = 1;

  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("All");
  const [expandedEvidence, setExpandedEvidence] = useState<Set<number>>(new Set());

  const fetchRecommendations = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getRecommendations(restaurantId);
      setRecommendations(Array.isArray(data) ? data : data?.recommendations ?? []);
    } catch (err: any) {
      setError(err.message ?? "Failed to load recommendations");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, [restaurantId]);

  const handleGenerate = async () => {
    try {
      setGenerating(true);
      setError(null);
      await api.generateRecommendations(restaurantId);
      await fetchRecommendations();
    } catch (err: any) {
      setError(err.message ?? "Failed to generate recommendations");
    } finally {
      setGenerating(false);
    }
  };

  const handleAccept = async (id: number) => {
    await api.updateRecommendationStatus(id, "accepted");
    fetchRecommendations();
  };

  const handleReject = async (id: number) => {
    await api.updateRecommendationStatus(id, "rejected");
    fetchRecommendations();
  };

  const toggleEvidence = (id: number) => {
    setExpandedEvidence((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const activeRecs = recommendations.filter(
    (r) => r.status !== "blocked" && (filter === "All" || r.category === filter)
  );
  const blockedRecs = recommendations.filter(
    (r) => r.status === "blocked" && (filter === "All" || r.category === filter)
  );

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
          <p className="text-gray-500">Loading recommendations...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <h1 className="text-3xl font-bold text-gray-900">Recommendations</h1>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-medium px-6 py-2.5 rounded-lg transition-colors flex items-center gap-2"
        >
          {generating && (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
          )}
          {generating ? "Generating..." : "Generate Recommendations"}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Category Filter */}
      <div className="flex flex-wrap gap-2">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => setFilter(cat)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filter === cat
                ? "bg-indigo-600 text-white"
                : "bg-white text-gray-700 border border-gray-200 hover:bg-gray-50"
            }`}
          >
            {cat === "All" ? "All" : cat.charAt(0).toUpperCase() + cat.slice(1)}
          </button>
        ))}
      </div>

      {/* Active Recommendations */}
      {activeRecs.length === 0 && !error && (
        <div className="bg-white rounded-xl shadow-sm p-12 text-center">
          <p className="text-gray-500 text-lg">
            No recommendations yet. Click "Generate Recommendations" to get AI-powered insights.
          </p>
        </div>
      )}

      <div className="space-y-4">
        {activeRecs.map((rec: any) => (
          <div key={rec.id} className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="font-semibold text-gray-900 text-lg">{rec.title}</h3>
                  {rec.urgency && (
                    <span
                      className={`text-xs font-medium px-2.5 py-1 rounded-full ${
                        URGENCY_COLORS[rec.urgency] ?? "bg-gray-100 text-gray-700"
                      }`}
                    >
                      {rec.urgency}
                    </span>
                  )}
                  {rec.category && (
                    <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700">
                      {rec.category}
                    </span>
                  )}
                </div>

                {rec.description && (
                  <p className="text-gray-600 text-sm mb-3">{rec.description}</p>
                )}

                {/* Confidence Bar */}
                {rec.confidence != null && (
                  <div className="flex items-center gap-3 mb-3">
                    <span className="text-xs text-gray-500 w-20">Confidence</span>
                    <div className="flex-1 max-w-xs bg-gray-200 rounded-full h-2.5">
                      <div
                        className={`h-2.5 rounded-full ${
                          rec.confidence >= 0.7
                            ? "bg-green-500"
                            : rec.confidence >= 0.4
                            ? "bg-amber-500"
                            : "bg-red-500"
                        }`}
                        style={{ width: `${(rec.confidence ?? 0) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-gray-700">
                      {((rec.confidence ?? 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                )}

                {/* Expected Impact */}
                {rec.expected_impact && (
                  <p className="text-sm text-indigo-600 font-medium mb-3">
                    Expected impact: {rec.expected_impact}
                  </p>
                )}

                {/* Evidence Collapsible */}
                {rec.evidence && (
                  <div className="mt-2">
                    <button
                      onClick={() => toggleEvidence(rec.id)}
                      className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
                    >
                      <svg
                        className={`w-4 h-4 transition-transform ${expandedEvidence.has(rec.id) ? "rotate-90" : ""}`}
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                      Evidence
                    </button>
                    {expandedEvidence.has(rec.id) && (
                      <div className="mt-2 pl-5 border-l-2 border-gray-200 text-sm text-gray-600 space-y-1">
                        {Array.isArray(rec.evidence) ? (
                          rec.evidence.map((e: string, i: number) => <p key={i}>{e}</p>)
                        ) : (
                          <p>{typeof rec.evidence === "string" ? rec.evidence : JSON.stringify(rec.evidence)}</p>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Accept / Reject */}
              {rec.status !== "accepted" && rec.status !== "rejected" && (
                <div className="flex flex-col gap-2 shrink-0">
                  <button
                    onClick={() => handleAccept(rec.id)}
                    className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
                  >
                    Accept
                  </button>
                  <button
                    onClick={() => handleReject(rec.id)}
                    className="bg-white hover:bg-gray-50 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg border border-gray-300 transition-colors"
                  >
                    Reject
                  </button>
                </div>
              )}
              {rec.status === "accepted" && (
                <span className="text-xs font-medium px-3 py-1.5 rounded-full bg-green-100 text-green-800">
                  Accepted
                </span>
              )}
              {rec.status === "rejected" && (
                <span className="text-xs font-medium px-3 py-1.5 rounded-full bg-gray-100 text-gray-600">
                  Rejected
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Blocked Recommendations */}
      {blockedRecs.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-500 mt-8">Blocked Recommendations</h2>
          {blockedRecs.map((rec: any) => (
            <div key={rec.id} className="bg-gray-50 rounded-xl border border-gray-200 p-6 opacity-70">
              <div className="flex items-center gap-3 mb-2">
                <h3 className="font-semibold text-gray-700">{rec.title}</h3>
                <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-gray-200 text-gray-600">
                  Blocked
                </span>
              </div>
              {rec.description && (
                <p className="text-gray-500 text-sm mb-2">{rec.description}</p>
              )}
              {rec.blocked_reason && (
                <p className="text-sm text-red-600">
                  Reason: {rec.blocked_reason}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
