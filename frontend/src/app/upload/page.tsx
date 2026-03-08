"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useRestaurant } from "@/context/RestaurantContext";

type StepStatus = "pending" | "uploading" | "done" | "error";

interface StepState {
  status: StepStatus;
  message?: string;
  detail?: string;
}

export default function UploadPage() {
  const { restaurantId, setRestaurantId, triggerRefresh } = useRestaurant();

  // Create restaurant state
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newCuisine, setNewCuisine] = useState("");
  const [creating, setCreating] = useState(false);
  const [createMsg, setCreateMsg] = useState<string | null>(null);

  // Required files
  const [menuFile, setMenuFile] = useState<File | null>(null);
  const [salesFile, setSalesFile] = useState<File | null>(null);
  const [inventoryFile, setInventoryFile] = useState<File | null>(null);

  const [steps, setSteps] = useState<Record<string, StepState>>({
    menu: { status: "pending" },
    inventory: { status: "pending" },
    sales: { status: "pending" },
    recipes: { status: "pending" },
  });
  const [running, setRunning] = useState(false);
  const [allDone, setAllDone] = useState(false);

  // Optional social upload
  const [socialFile, setSocialFile] = useState<File | null>(null);
  const [socialResult, setSocialResult] = useState<StepState | null>(null);
  const [socialUploading, setSocialUploading] = useState(false);

  const updateStep = (key: string, state: StepState) => {
    setSteps((prev) => ({ ...prev, [key]: state }));
  };

  const runSmartUpload = async () => {
    if (!menuFile || !salesFile || !inventoryFile) return;
    setRunning(true);
    setAllDone(false);
    setSteps({
      menu: { status: "pending" },
      inventory: { status: "pending" },
      sales: { status: "pending" },
      recipes: { status: "pending" },
    });

    // Step 1: Upload menu
    updateStep("menu", { status: "uploading", message: "Uploading menu..." });
    try {
      const menuRes = await api.uploadCSV("menu-items", restaurantId, menuFile);
      updateStep("menu", {
        status: "done",
        message: `Menu uploaded: ${menuRes.rows_processed} items`,
        detail: menuRes.rows_failed > 0 ? `${menuRes.rows_failed} rows failed` : undefined,
      });
    } catch (err: any) {
      updateStep("menu", { status: "error", message: err.message ?? "Menu upload failed" });
      setRunning(false);
      return;
    }

    // Step 2: Upload inventory
    updateStep("inventory", { status: "uploading", message: "Uploading inventory..." });
    try {
      const invRes = await api.uploadCSV("inventory-items", restaurantId, inventoryFile);
      updateStep("inventory", {
        status: "done",
        message: `Inventory uploaded: ${invRes.rows_processed} ingredients`,
        detail: invRes.rows_failed > 0 ? `${invRes.rows_failed} rows failed` : undefined,
      });
    } catch (err: any) {
      updateStep("inventory", { status: "error", message: err.message ?? "Inventory upload failed" });
      setRunning(false);
      return;
    }

    // Step 3: Upload POS sales (auto-converted)
    updateStep("sales", { status: "uploading", message: "Converting & uploading POS sales..." });
    try {
      const salesRes = await api.uploadPOSSales(restaurantId, salesFile);
      updateStep("sales", {
        status: "done",
        message: `Sales imported: ${salesRes.rows_processed} records`,
        detail: salesRes.rows_failed > 0 ? `${salesRes.rows_failed} rows failed` : undefined,
      });
    } catch (err: any) {
      updateStep("sales", { status: "error", message: err.message ?? "Sales upload failed" });
      setRunning(false);
      return;
    }

    // Step 4: Generate recipes from standard recipe book
    updateStep("recipes", { status: "uploading", message: "Generating recipe mappings..." });
    try {
      const recipeRes = await api.generateRecipes(restaurantId);
      updateStep("recipes", {
        status: "done",
        message: `Generated ${recipeRes.recipes_created} recipe mappings for ${recipeRes.menu_items_processed} items`,
        detail: recipeRes.menu_items_skipped > 0
          ? `${recipeRes.menu_items_skipped} items had no standard recipe`
          : undefined,
      });
    } catch (err: any) {
      updateStep("recipes", { status: "error", message: err.message ?? "Recipe generation failed" });
      setRunning(false);
      return;
    }

    setAllDone(true);
    setRunning(false);
  };

  const handleSocialUpload = async () => {
    if (!socialFile) return;
    setSocialUploading(true);
    try {
      const res = await api.uploadCSV("social-posts", restaurantId, socialFile);
      setSocialResult({
        status: "done",
        message: `Uploaded ${res.rows_processed} posts`,
        detail: res.rows_failed > 0 ? `${res.rows_failed} rows failed` : undefined,
      });
    } catch (err: any) {
      setSocialResult({ status: "error", message: err.message ?? "Upload failed" });
    } finally {
      setSocialUploading(false);
    }
  };

  const handleCreateRestaurant = async () => {
    if (!newName.trim()) return;
    setCreating(true);
    setCreateMsg(null);
    try {
      const res = await api.createRestaurant({
        name: newName.trim(),
        cuisine_type: newCuisine.trim() || undefined,
      });
      setRestaurantId(res.id);
      triggerRefresh();
      setCreateMsg(`Created "${res.name}" (ID: ${res.id}) — now selected!`);
      setShowCreate(false);
      setNewName("");
      setNewCuisine("");
    } catch (err: any) {
      setCreateMsg(err.message ?? "Failed to create restaurant");
    } finally {
      setCreating(false);
    }
  };

  const stepIcon = (s: StepStatus) => {
    switch (s) {
      case "pending": return <div className="w-6 h-6 rounded-full border-2 border-gray-300" />;
      case "uploading": return <div className="w-6 h-6 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />;
      case "done": return (
        <div className="w-6 h-6 rounded-full bg-emerald-500 flex items-center justify-center">
          <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
        </div>
      );
      case "error": return (
        <div className="w-6 h-6 rounded-full bg-red-500 flex items-center justify-center">
          <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
        </div>
      );
    }
  };

  const canRun = menuFile && salesFile && inventoryFile && !running;

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Smart Upload</h1>
        <p className="text-gray-500 mt-1">
          Upload your menu, inventory, and POS sales. Recipe mappings are generated automatically.
        </p>
      </div>

      {/* Create Restaurant */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500">
              Uploading to: <span className="font-semibold text-gray-900">Restaurant #{restaurantId}</span>
            </p>
            <p className="text-xs text-gray-400 mt-0.5">Select a restaurant from the sidebar, or create a new one.</p>
          </div>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
          >
            {showCreate ? "Cancel" : "+ New Restaurant"}
          </button>
        </div>
        {showCreate && (
          <div className="mt-4 flex flex-wrap items-end gap-3">
            <div className="flex-1 min-w-[180px]">
              <label className="block text-xs text-gray-500 mb-1">Name *</label>
              <input
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Spice Garden"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>
            <div className="flex-1 min-w-[140px]">
              <label className="block text-xs text-gray-500 mb-1">Cuisine</label>
              <input
                value={newCuisine}
                onChange={(e) => setNewCuisine(e.target.value)}
                placeholder="Indian"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>
            <button
              onClick={handleCreateRestaurant}
              disabled={!newName.trim() || creating}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-300 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              {creating ? "Creating..." : "Create"}
            </button>
          </div>
        )}
        {createMsg && (
          <p className={`mt-3 text-sm ${createMsg.startsWith("Created") ? "text-emerald-600" : "text-red-500"}`}>
            {createMsg}
          </p>
        )}
      </div>

      {/* Main Upload Flow (3 required files) */}
      <div className="bg-white rounded-xl shadow-sm p-6 space-y-6">
        <h2 className="text-lg font-semibold text-gray-900">Required Files (3)</h2>

        {/* 1. Menu */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            1. Menu CSV
          </label>
          <p className="text-xs text-gray-400">
            Columns: name, category, price, ingredient_cost, description
          </p>
          <input
            type="file"
            accept=".csv"
            onChange={(e) => setMenuFile(e.target.files?.[0] ?? null)}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 cursor-pointer"
          />
        </div>

        {/* 2. Inventory */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            2. Inventory CSV
          </label>
          <p className="text-xs text-gray-400">
            Columns: ingredient_name, unit, quantity_on_hand, reorder_threshold, unit_cost, expiry_date, supplier
          </p>
          <input
            type="file"
            accept=".csv"
            onChange={(e) => setInventoryFile(e.target.files?.[0] ?? null)}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 cursor-pointer"
          />
        </div>

        {/* 3. POS Sales */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            3. POS Sales CSV
          </label>
          <p className="text-xs text-gray-400">
            Any standard POS export — we auto-detect columns like Transaction ID, Date, Time, Item Name, Qty, Price, etc.
          </p>
          <input
            type="file"
            accept=".csv"
            onChange={(e) => setSalesFile(e.target.files?.[0] ?? null)}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 cursor-pointer"
          />
        </div>

        {/* Run Button */}
        <button
          onClick={runSmartUpload}
          disabled={!canRun}
          className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-semibold px-6 py-3 rounded-lg transition-colors text-lg"
        >
          {running ? "Processing..." : "Upload & Generate"}
        </button>

        {/* Progress Steps */}
        {Object.values(steps).some((s) => s.status !== "pending") && (
          <div className="space-y-4 pt-2">
            {[
              { key: "menu", label: "Upload Menu" },
              { key: "inventory", label: "Upload Inventory" },
              { key: "sales", label: "Convert & Import POS Sales" },
              { key: "recipes", label: "Generate Recipe Mappings" },
            ].map(({ key, label }) => {
              const step = steps[key];
              return (
                <div key={key} className="flex items-start gap-3">
                  {stepIcon(step.status)}
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-medium ${
                      step.status === "done" ? "text-emerald-700" :
                      step.status === "error" ? "text-red-700" :
                      step.status === "uploading" ? "text-indigo-700" :
                      "text-gray-400"
                    }`}>
                      {label}
                    </p>
                    {step.message && (
                      <p className={`text-xs mt-0.5 ${
                        step.status === "error" ? "text-red-500" : "text-gray-500"
                      }`}>
                        {step.message}
                      </p>
                    )}
                    {step.detail && (
                      <p className="text-xs text-gray-400 mt-0.5">{step.detail}</p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Success Banner */}
        {allDone && (
          <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 text-sm text-emerald-700">
            <p className="font-semibold">All done! Your restaurant is set up.</p>
            <p className="mt-1">Head to the <a href="/dashboard" className="underline font-medium">Dashboard</a> to see your insights, or upload social data below.</p>
          </div>
        )}
      </div>

      {/* Optional: Social Media */}
      <div className="bg-white rounded-xl shadow-sm p-6 space-y-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Optional: Social Media</h2>
          <p className="text-sm text-gray-500 mt-1">Add social media post data to unlock social insights.</p>
        </div>

        <div className="space-y-2">
          <p className="text-xs text-gray-400">
            Columns: platform, post_type, content_summary, menu_item_name, posted_at, likes, comments, shares, reach
          </p>
          <div className="flex items-center gap-3">
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setSocialFile(e.target.files?.[0] ?? null)}
              className="flex-1 text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-gray-50 file:text-gray-700 hover:file:bg-gray-100 cursor-pointer"
            />
            <button
              onClick={handleSocialUpload}
              disabled={!socialFile || socialUploading}
              className="bg-gray-600 hover:bg-gray-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              {socialUploading ? "..." : "Upload"}
            </button>
          </div>
          {socialResult && (
            <p className={`text-xs ${socialResult.status === "done" ? "text-emerald-600" : "text-red-500"}`}>
              {socialResult.message}
            </p>
          )}
        </div>
      </div>

      {/* Seed Demo */}
      <div className="bg-gray-50 rounded-xl p-6 text-center space-y-3">
        <p className="text-sm text-gray-500">Or skip uploading and try with demo data</p>
        <button
          onClick={async () => {
            try {
              await api.seedDemo();
              alert("Demo data seeded! Go to Dashboard.");
            } catch (err: any) {
              alert(err.message ?? "Failed to seed");
            }
          }}
          className="bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium px-6 py-2 rounded-lg transition-colors"
        >
          Seed Demo Data
        </button>
      </div>
    </div>
  );
}
