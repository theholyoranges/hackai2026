"use client";

import { useState } from "react";
import { api } from "@/lib/api";

interface UploadSection {
  key: string;
  label: string;
  type: string;
  description: string;
  hint: string;
}

const UPLOAD_SECTIONS: UploadSection[] = [
  {
    key: "menu",
    label: "Menu Items",
    type: "menu",
    description: "Upload your menu with item names, prices, categories, and costs.",
    hint: "Expected columns: item_name, category, price, cost, description",
  },
  {
    key: "sales",
    label: "Sales Transactions",
    type: "sales",
    description: "Upload historical sales data for demand and revenue analysis.",
    hint: "Expected columns: date, item_name, quantity, revenue, order_id",
  },
  {
    key: "inventory",
    label: "Inventory",
    type: "inventory",
    description: "Upload current inventory levels and expiry dates.",
    hint: "Expected columns: ingredient, quantity, unit, expiry_date, cost_per_unit",
  },
  {
    key: "recipe_mapping",
    label: "Recipe Mapping",
    type: "recipe_mapping",
    description: "Upload ingredient requirements per menu item.",
    hint: "Expected columns: item_name, ingredient, quantity_needed, unit",
  },
  {
    key: "social",
    label: "Social Posts",
    type: "social",
    description: "Upload social media post performance data.",
    hint: "Expected columns: date, platform, post_type, content, likes, comments, shares",
  },
];

interface UploadResult {
  success: boolean;
  message: string;
  summary?: {
    rows_ingested?: number;
    rows_skipped?: number;
    warnings?: string[];
    [key: string]: any;
  };
}

export default function UploadPage() {
  const [restaurantId, setRestaurantId] = useState(1);
  const [files, setFiles] = useState<Record<string, File | null>>({});
  const [uploading, setUploading] = useState<Record<string, boolean>>({});
  const [results, setResults] = useState<Record<string, UploadResult>>({});
  const [seeding, setSeeding] = useState(false);
  const [seedResult, setSeedResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);

  const handleFileChange = (key: string, file: File | null) => {
    setFiles((prev) => ({ ...prev, [key]: file }));
    setResults((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
  };

  const handleUpload = async (section: UploadSection) => {
    const file = files[section.key];
    if (!file) return;

    try {
      setUploading((prev) => ({ ...prev, [section.key]: true }));
      const response = await api.uploadCSV(section.type, restaurantId, file);
      setResults((prev) => ({
        ...prev,
        [section.key]: {
          success: true,
          message: `${section.label} data uploaded successfully.`,
          summary: response,
        },
      }));
    } catch (err: any) {
      setResults((prev) => ({
        ...prev,
        [section.key]: {
          success: false,
          message: err.message ?? `Failed to upload ${section.label} data.`,
        },
      }));
    } finally {
      setUploading((prev) => ({ ...prev, [section.key]: false }));
    }
  };

  const handleSeedDemo = async () => {
    try {
      setSeeding(true);
      setSeedResult(null);
      await api.seedDemo(restaurantId);
      setSeedResult({
        success: true,
        message: "Demo data seeded successfully! Navigate to Dashboard to view insights.",
      });
    } catch (err: any) {
      setSeedResult({
        success: false,
        message: err.message ?? "Failed to seed demo data.",
      });
    } finally {
      setSeeding(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
      <h1 className="text-3xl font-bold text-gray-900">Upload Data</h1>

      {/* Restaurant Selector & Seed Demo */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <label
              htmlFor="restaurant-select"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Restaurant
            </label>
            <select
              id="restaurant-select"
              value={restaurantId}
              onChange={(e) => setRestaurantId(Number(e.target.value))}
              className="border border-gray-300 rounded-lg px-4 py-2 text-gray-700 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
            >
              {[1, 2, 3, 4, 5].map((id) => (
                <option key={id} value={id}>
                  Restaurant {id}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col items-end gap-2">
            <button
              onClick={handleSeedDemo}
              disabled={seeding}
              className="bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-400 text-white font-medium px-6 py-2.5 rounded-lg transition-colors flex items-center gap-2"
            >
              {seeding && (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
              )}
              {seeding ? "Seeding..." : "Seed Demo Data"}
            </button>
            <p className="text-xs text-gray-500">
              Quickly populate sample data for testing
            </p>
          </div>
        </div>

        {seedResult && (
          <div
            className={`mt-4 rounded-lg p-4 text-sm ${
              seedResult.success
                ? "bg-green-50 border border-green-200 text-green-700"
                : "bg-red-50 border border-red-200 text-red-700"
            }`}
          >
            {seedResult.message}
          </div>
        )}
      </div>

      {/* Upload Sections */}
      {UPLOAD_SECTIONS.map((section) => (
        <div key={section.key} className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">
            {section.label}
          </h2>
          <p className="text-sm text-gray-600 mb-3">{section.description}</p>
          <p className="text-xs text-gray-400 bg-gray-50 rounded-lg px-3 py-2 mb-4 font-mono">
            {section.hint}
          </p>

          <div className="flex items-center gap-4 flex-wrap">
            <label className="flex-1 min-w-[200px]">
              <input
                type="file"
                accept=".csv"
                onChange={(e) =>
                  handleFileChange(section.key, e.target.files?.[0] ?? null)
                }
                className="block w-full text-sm text-gray-500
                  file:mr-4 file:py-2 file:px-4
                  file:rounded-lg file:border-0
                  file:text-sm file:font-medium
                  file:bg-indigo-50 file:text-indigo-700
                  hover:file:bg-indigo-100
                  cursor-pointer"
              />
            </label>
            <button
              onClick={() => handleUpload(section)}
              disabled={!files[section.key] || uploading[section.key]}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white text-sm font-medium px-5 py-2 rounded-lg transition-colors flex items-center gap-2"
            >
              {uploading[section.key] && (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
              )}
              {uploading[section.key] ? "Uploading..." : "Upload"}
            </button>
          </div>

          {/* Result */}
          {results[section.key] && (
            <div
              className={`mt-4 rounded-lg p-4 text-sm ${
                results[section.key].success
                  ? "bg-green-50 border border-green-200 text-green-700"
                  : "bg-red-50 border border-red-200 text-red-700"
              }`}
            >
              <p className="font-medium">{results[section.key].message}</p>

              {/* Ingestion Summary */}
              {results[section.key].success && results[section.key].summary && (
                <div className="mt-2 text-xs space-y-0.5">
                  {results[section.key].summary?.rows_ingested != null && (
                    <p>Rows ingested: {results[section.key].summary!.rows_ingested}</p>
                  )}
                  {results[section.key].summary?.rows_skipped != null &&
                    results[section.key].summary!.rows_skipped! > 0 && (
                      <p>Rows skipped: {results[section.key].summary!.rows_skipped}</p>
                    )}
                  {results[section.key].summary?.message && (
                    <p>{results[section.key].summary!.message}</p>
                  )}
                  {results[section.key].summary?.warnings &&
                    results[section.key].summary!.warnings!.length > 0 && (
                      <div className="mt-1">
                        <p className="font-medium text-amber-700">Warnings:</p>
                        {results[section.key].summary!.warnings!.map(
                          (w: string, i: number) => (
                            <p key={i} className="text-amber-600">
                              {w}
                            </p>
                          )
                        )}
                      </div>
                    )}
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
