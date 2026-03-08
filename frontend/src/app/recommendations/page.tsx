"use client";

import { useEffect, useState, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  Zap,
  UtensilsCrossed,
  Megaphone,
  Settings,
  Sparkles,
  CloudRain,
  MapPin,
  Star,
  Eye,
  Check,
  X,
  Loader2,
  AlertTriangle,
  Package,
  TrendingDown,
  ShoppingBag,
  DollarSign,
  Trash2,
  Lightbulb,
  Flame,
  RotateCcw,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

import { api } from "@/lib/api";
import { useRestaurant } from "@/context/RestaurantContext";

/* ------------------------------------------------------------------ */
/*  Types                                                               */
/* ------------------------------------------------------------------ */
type WidgetType = "local-demand" | "menu-opportunities" | "inventory" | "local-marketing" | "operations";
type Priority = "all" | "critical" | "high" | "medium" | "low";

interface UnifiedRec {
  id: string;
  title: string;
  description: string;
  target?: string;
  widget: WidgetType;
  priority: Priority;
  source: "menu-insights" | "inventory" | "local" | "ai";
  sourceLabel: string;
  category?: string;
  evidence?: Record<string, any>;
  type?: string;
}

/* ------------------------------------------------------------------ */
/*  Widget config                                                       */
/* ------------------------------------------------------------------ */
const WIDGETS: {
  type: WidgetType;
  title: string;
  description: string;
  icon: typeof Zap;
  gradient: string;
  borderColor: string;
  iconBg: string;
}[] = [
  {
    type: "local-demand",
    title: "Right Now Nearby",
    description: "Weather, local events, competitor gaps",
    icon: CloudRain,
    gradient: "from-amber-500/10 to-orange-500/10",
    borderColor: "border-amber-200",
    iconBg: "bg-amber-100 text-amber-600",
  },
  {
    type: "menu-opportunities",
    title: "Menu Opportunities",
    description: "Combos, pricing, underperformers",
    icon: UtensilsCrossed,
    gradient: "from-blue-500/10 to-indigo-500/10",
    borderColor: "border-blue-200",
    iconBg: "bg-blue-100 text-blue-600",
  },
  {
    type: "inventory",
    title: "Inventory Actions",
    description: "Waste reduction, reorder, overstock",
    icon: Package,
    gradient: "from-emerald-500/10 to-teal-500/10",
    borderColor: "border-emerald-200",
    iconBg: "bg-emerald-100 text-emerald-600",
  },
  {
    type: "local-marketing",
    title: "Marketing & Social",
    description: "Posts, promos, campaigns",
    icon: Megaphone,
    gradient: "from-purple-500/10 to-pink-500/10",
    borderColor: "border-purple-200",
    iconBg: "bg-purple-100 text-purple-600",
  },
];

const PRIORITY_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  critical: { label: "Critical", color: "text-red-700", bg: "bg-red-100 border-red-200" },
  high: { label: "High", color: "text-orange-700", bg: "bg-orange-100 border-orange-200" },
  medium: { label: "Medium", color: "text-amber-700", bg: "bg-amber-100 border-amber-200" },
  low: { label: "Low", color: "text-green-700", bg: "bg-green-100 border-green-200" },
};

const SOURCE_CONFIG: Record<string, { label: string; color: string }> = {
  "menu-insights": { label: "Menu Insights", color: "bg-blue-50 text-blue-600 border-blue-200" },
  inventory: { label: "Inventory", color: "bg-emerald-50 text-emerald-600 border-emerald-200" },
  local: { label: "Local Intel", color: "bg-amber-50 text-amber-600 border-amber-200" },
  ai: { label: "AI Generated", color: "bg-purple-50 text-purple-600 border-purple-200" },
};

/* ------------------------------------------------------------------ */
/*  Animations                                                          */
/* ------------------------------------------------------------------ */
const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({
    opacity: 1, y: 0,
    transition: { delay: i * 0.06, duration: 0.4, ease: "easeOut" as const },
  }),
};

/* ------------------------------------------------------------------ */
/*  Hardcoded local recommendations                                     */
/* ------------------------------------------------------------------ */
function getLocalRecs(): UnifiedRec[] {
  return [
    // Weather
    {
      id: "local-weather-1",
      title: "Promote Hot Drinks & Comfort Food",
      description: "It's been rainy all week in Richardson. Customers crave warm comfort food — feature chai, coffee, soups, and hot appetizers prominently on your menu board and delivery apps.",
      widget: "local-demand",
      priority: "high",
      source: "local",
      sourceLabel: "Rainy Weather",
      category: "weather",
    },
    {
      id: "local-weather-2",
      title: "Push Delivery-Friendly Meals",
      description: "Rainy weather drives delivery orders up 20-30%. Make sure your top combos are visible on delivery platforms and consider a limited-time free delivery promo.",
      widget: "local-demand",
      priority: "high",
      source: "local",
      sourceLabel: "Rainy Weather",
      category: "weather",
    },
    {
      id: "local-weather-3",
      title: "Add a Rainy Day Special",
      description: "Create a \"Rainy Day Combo\" — a warm drink + comfort dish at a small discount. Customers love themed specials and it gives you something to post about on social media.",
      widget: "local-marketing",
      priority: "medium",
      source: "local",
      sourceLabel: "Rainy Weather",
      category: "weather",
    },
    // Competitor gaps from Google reviews
    {
      id: "local-reviews-1",
      title: "Highlight Your Cleanliness Standards",
      description: "Nearby restaurants are getting negative Google reviews about cleanliness. This is your chance — post photos of your clean kitchen, highlight hygiene ratings on social media, and add a \"Kitchen Tour\" story to Instagram.",
      widget: "local-marketing",
      priority: "high",
      source: "local",
      sourceLabel: "Google Reviews Intel",
      category: "competitor",
    },
    {
      id: "local-reviews-2",
      title: "Run a \"Fresh & Clean\" Campaign",
      description: "Local competitors are losing customers over cleanliness complaints. Create signage and social content emphasizing your fresh ingredients and kitchen standards. This builds trust with nearby customers looking for alternatives.",
      widget: "local-marketing",
      priority: "medium",
      source: "local",
      sourceLabel: "Google Reviews Intel",
      category: "competitor",
    },
    {
      id: "local-reviews-3",
      title: "Capture Competitor's Unhappy Customers",
      description: "People leaving negative reviews at nearby restaurants are actively looking for alternatives. Run a geo-targeted ad or offer a first-time visitor discount to attract them to your restaurant.",
      widget: "local-marketing",
      priority: "medium",
      source: "local",
      sourceLabel: "Google Reviews Intel",
      category: "competitor",
    },
    // No events this week
    {
      id: "local-events-1",
      title: "No Major Events This Week — Focus on Regulars",
      description: "No large events nearby this week. A great time to focus on loyalty — send a thank-you offer to repeat customers or test a new menu item with your regulars before the next busy weekend.",
      widget: "local-demand",
      priority: "low",
      source: "local",
      sourceLabel: "Events Update",
      category: "events",
    },
  ];
}

/* ------------------------------------------------------------------ */
/*  Build recs from menu analytics                                      */
/* ------------------------------------------------------------------ */
function buildMenuRecs(menuData: any): UnifiedRec[] {
  if (!menuData) return [];
  const recs: UnifiedRec[] = [];

  const engineering = menuData.menu_engineering ?? [];
  const combos = menuData.pair_associations ?? [];
  const stars = engineering.filter((i: any) => i.classification === "Star");
  const puzzles = engineering.filter((i: any) => i.classification === "Puzzle");
  const dogs = engineering.filter((i: any) => i.classification === "Dog");

  // Combo deal
  if (combos.length > 0) {
    const top = combos[0];
    recs.push({
      id: "menu-combo-1",
      title: "Create a Combo Deal",
      target: `${top.antecedents?.[0]} + ${top.consequents?.[0]}`,
      description: `These items are frequently ordered together (${((top.confidence ?? 0) * 100).toFixed(0)}% of the time). Bundle them with a small discount to boost average order value.`,
      widget: "menu-opportunities",
      priority: "high",
      source: "menu-insights",
      sourceLabel: "Pair Analysis",
      type: "combo",
      evidence: { items: `${top.antecedents?.[0]} + ${top.consequents?.[0]}`, frequency: top.support_count },
    });
  }

  // Promote hidden gem
  if (puzzles.length > 0) {
    recs.push({
      id: "menu-promote-1",
      title: "Promote Hidden Gem",
      target: puzzles[0].item,
      description: `${puzzles[0].item} has great margins ($${Number(puzzles[0].margin).toFixed(2)}/order) but low sales. A social media post or menu highlight could boost orders.`,
      widget: "menu-opportunities",
      priority: "medium",
      source: "menu-insights",
      sourceLabel: "Menu Engineering",
      type: "promote",
    });
  }

  // Price bump
  if (stars.length > 0) {
    recs.push({
      id: "menu-price-1",
      title: "Consider a Small Price Bump",
      target: stars[0].item,
      description: `${stars[0].item} is your top performer with strong demand. A 5-8% price increase is unlikely to hurt volume and will boost revenue.`,
      widget: "menu-opportunities",
      priority: "medium",
      source: "menu-insights",
      sourceLabel: "Menu Engineering",
      type: "price",
    });
  }

  // Waste / remove underperformers
  if (dogs.length > 0) {
    recs.push({
      id: "menu-waste-1",
      title: "Reduce Waste on Low Performer",
      target: dogs[dogs.length - 1].item,
      description: `${dogs[dogs.length - 1].item} has low sales and low margins. The ingredients are going to waste. Rework the recipe or run a daily special.`,
      widget: "menu-opportunities",
      priority: "medium",
      source: "menu-insights",
      sourceLabel: "Menu Engineering",
      type: "waste",
    });
  }

  if (dogs.length > 1) {
    recs.push({
      id: "menu-remove-1",
      title: "Consider Removing from Menu",
      target: dogs[0].item,
      description: `${dogs[0].item} sells only ${dogs[0].qty_sold} units with thin margins. Dropping it simplifies your kitchen and reduces waste.`,
      widget: "menu-opportunities",
      priority: "low",
      source: "menu-insights",
      sourceLabel: "Menu Engineering",
      type: "remove",
    });
  }

  // Improve underperformer
  const sorted = [...(menuData.sales_by_item ?? [])].sort((a: any, b: any) => (a.qty_sold ?? 0) - (b.qty_sold ?? 0));
  if (sorted.length > 0) {
    const bottom = sorted[0];
    recs.push({
      id: "menu-improve-1",
      title: "Improve Underperformer",
      target: bottom.item,
      description: `${bottom.item} has only ${bottom.qty_sold} orders and $${Number(bottom.revenue).toFixed(0)} revenue this month. Try a new description, pairing, or repositioning.`,
      widget: "menu-opportunities",
      priority: "low",
      source: "menu-insights",
      sourceLabel: "Sales Analysis",
      type: "improve",
    });
  }

  return recs;
}

/* ------------------------------------------------------------------ */
/*  Build recs from inventory analytics                                 */
/* ------------------------------------------------------------------ */
function buildInventoryRecs(invData: any): UnifiedRec[] {
  if (!invData) return [];
  const recs: UnifiedRec[] = [];

  const wasteProne = invData.waste_prone ?? [];
  const overstockRisks = invData.overstock_risks ?? [];
  const reorderAlerts = invData.reorder_alerts ?? [];
  const stockoutRisks = invData.stockout_risks ?? [];

  // Waste specials
  for (const item of wasteProne.slice(0, 2)) {
    recs.push({
      id: `inv-waste-${item.ingredient}`,
      title: "Run a Special to Reduce Waste",
      target: item.ingredient,
      description: `${item.ingredient} has ${item.quantity_on_hand?.toFixed(1)} ${item.unit} on hand with high waste risk. Create a daily special or combo to use it up.`,
      widget: "inventory",
      priority: "high",
      source: "inventory",
      sourceLabel: "Waste Risk",
      type: "waste_special",
    });
  }

  // Overstock → order less
  for (const item of overstockRisks.slice(0, 2)) {
    recs.push({
      id: `inv-overstock-${item.ingredient}`,
      title: "Reduce Next Order Quantity",
      target: item.ingredient,
      description: `${item.ingredient} has ${item.projected_days_left?.toFixed(0)} days of supply. Cut your next order by 30-50% to free up cash.`,
      widget: "inventory",
      priority: "medium",
      source: "inventory",
      sourceLabel: "Overstock",
      type: "reduce_order",
    });
  }

  // Reorder alerts
  for (const item of [...stockoutRisks, ...reorderAlerts].slice(0, 3)) {
    const days = item.projected_days_left ?? item.days_of_stock_remaining ?? 0;
    recs.push({
      id: `inv-reorder-${item.ingredient}`,
      title: "Reorder Soon",
      target: item.ingredient,
      description: `${item.ingredient} has only ~${days.toFixed(0)} days of stock left. Place an order now to prevent a stockout.`,
      widget: "inventory",
      priority: days <= 2 ? "critical" : "high",
      source: "inventory",
      sourceLabel: "Low Stock",
      type: "reorder",
    });
  }

  return recs;
}

/* ------------------------------------------------------------------ */
/*  Detail Drawer                                                       */
/* ------------------------------------------------------------------ */
function DetailDrawer({
  rec,
  onClose,
}: {
  rec: UnifiedRec;
  onClose: () => void;
}) {
  const [elaboration, setElaboration] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const elaborate = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.elaborateRecommendation({
        title: rec.title,
        description: rec.description,
        target_item: rec.target,
        context: { source: rec.source, category: rec.category, type: rec.type },
      });
      setElaboration(res.elaboration);
    } catch {
      setElaboration("Unable to generate details right now. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [rec]);

  useEffect(() => {
    elaborate();
  }, [elaborate]);

  function renderMarkdown(text: string) {
    return text.split("\n").map((line, i) => {
      const trimmed = line.trim();
      if (!trimmed) return <br key={i} />;
      const numMatch = trimmed.match(/^(\d+)[.)]\s+(.+)/);
      if (numMatch) {
        return (
          <div key={i} className="flex items-start gap-2.5 my-1">
            <span className="text-xs font-bold text-indigo-500 bg-indigo-50 w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5">{numMatch[1]}</span>
            <span className="text-sm text-gray-700 leading-relaxed">{renderInline(numMatch[2])}</span>
          </div>
        );
      }
      if (trimmed.startsWith("- ") || trimmed.startsWith("• ") || trimmed.startsWith("* ")) {
        return (
          <div key={i} className="flex items-start gap-2.5 my-1">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-[7px] shrink-0" />
            <span className="text-sm text-gray-700 leading-relaxed">{renderInline(trimmed.slice(2))}</span>
          </div>
        );
      }
      return <p key={i} className="text-sm text-gray-700 leading-relaxed my-1.5">{renderInline(trimmed)}</p>;
    });
  }

  function renderInline(text: string) {
    return text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/).map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) return <strong key={i}>{part.slice(2, -2)}</strong>;
      if (part.startsWith("*") && part.endsWith("*")) return <em key={i}>{part.slice(1, -1)}</em>;
      return part;
    });
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 40 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 40 }}
      className="fixed inset-y-0 right-0 w-full max-w-md bg-white shadow-2xl border-l border-gray-200 z-50 overflow-y-auto"
    >
      <div className="p-6 space-y-5">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-gray-900">Recommendation Details</h3>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 transition">
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        <div>
          <h4 className="font-semibold text-gray-900 text-base">{rec.title}</h4>
          {rec.target && <p className="text-sm text-indigo-600 font-medium mt-1">{rec.target}</p>}
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            <span className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full border ${PRIORITY_CONFIG[rec.priority]?.bg} ${PRIORITY_CONFIG[rec.priority]?.color}`}>
              {PRIORITY_CONFIG[rec.priority]?.label}
            </span>
            <span className={`text-[11px] font-medium px-2.5 py-0.5 rounded-full border ${SOURCE_CONFIG[rec.source]?.color}`}>
              {rec.sourceLabel}
            </span>
          </div>
        </div>

        <div>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Summary</p>
          <p className="text-sm text-gray-700 leading-relaxed">{rec.description}</p>
        </div>

        <div className="border-t pt-4">
          <p className="text-xs font-semibold text-indigo-600 uppercase tracking-wider mb-2">AI Action Plan</p>
          {loading ? (
            <div className="flex items-center justify-center gap-2 py-8 text-indigo-600">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span className="text-sm font-medium">Generating action plan...</span>
            </div>
          ) : elaboration ? (
            <div className="space-y-2">
              <div className="bg-indigo-50/50 rounded-lg p-4 border border-indigo-100 space-y-1.5">
                {renderMarkdown(elaboration)}
              </div>
              <button onClick={elaborate} className="text-sm text-indigo-600 hover:text-indigo-700 font-medium">
                Regenerate
              </button>
            </div>
          ) : null}
        </div>
      </div>
    </motion.div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main page (inner, uses useSearchParams)                             */
/* ------------------------------------------------------------------ */
function RecommendationsInner() {
  const { restaurantId } = useRestaurant();
  const searchParams = useSearchParams();

  const [menuData, setMenuData] = useState<any>(null);
  const [invData, setInvData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedWidget, setSelectedWidget] = useState<WidgetType | null>(null);
  const [priorityFilter, setPriorityFilter] = useState<Priority>("all");
  const [detailRec, setDetailRec] = useState<UnifiedRec | null>(null);

  // Fetch data from menu + inventory analytics
  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [menu, inv] = await Promise.all([
          api.getMenuAnalytics(restaurantId).catch(() => null),
          api.getInventoryAnalytics(restaurantId).catch(() => null),
        ]);
        setMenuData(menu);
        setInvData(inv);
      } finally {
        setLoading(false);
      }
    })();
  }, [restaurantId]);

  // Build all recommendations
  const allRecs: UnifiedRec[] = [
    ...getLocalRecs(),
    ...buildMenuRecs(menuData),
    ...buildInventoryRecs(invData),
  ];

  // Sort: critical first, then high, medium, low
  const priorityOrder: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
  allRecs.sort((a, b) => (priorityOrder[a.priority] ?? 9) - (priorityOrder[b.priority] ?? 9));

  // Handle deep link from menu insights / inventory
  useEffect(() => {
    const reviewParam = searchParams.get("review");
    if (reviewParam && allRecs.length > 0) {
      try {
        const params = new URLSearchParams(decodeURIComponent(reviewParam));
        const title = params.get("title") ?? "";
        const description = params.get("description") ?? "";
        const target = params.get("target") ?? "";
        const source = params.get("source") ?? "menu-insights";
        const type = params.get("type") ?? "";

        // Find matching rec or create a transient one
        const match = allRecs.find(
          (r) => r.title === title && r.target === target
        );
        if (match) {
          setDetailRec(match);
          setSelectedWidget(match.widget);
        } else {
          setDetailRec({
            id: "review-deeplink",
            title,
            description,
            target: target || undefined,
            widget: source === "inventory" ? "inventory" : "menu-opportunities",
            priority: "medium",
            source: source as any,
            sourceLabel: source === "inventory" ? "Inventory" : "Menu Insights",
            type,
          });
          setSelectedWidget(source === "inventory" ? "inventory" : "menu-opportunities");
        }
      } catch {
        // ignore bad params
      }
    }
  }, [searchParams, loading]);

  // Widget counts
  const widgetCounts: Record<WidgetType, number> = {
    "local-demand": 0, "menu-opportunities": 0, inventory: 0, "local-marketing": 0, operations: 0,
  };
  for (const r of allRecs) widgetCounts[r.widget]++;

  // Filtered
  const filteredRecs = allRecs.filter((r) => {
    if (selectedWidget && r.widget !== selectedWidget) return false;
    if (priorityFilter !== "all" && r.priority !== priorityFilter) return false;
    return true;
  });

  const priorityCounts: Record<string, number> = { all: 0, critical: 0, high: 0, medium: 0, low: 0 };
  for (const r of allRecs) {
    if (selectedWidget && r.widget !== selectedWidget) continue;
    priorityCounts.all++;
    priorityCounts[r.priority] = (priorityCounts[r.priority] || 0) + 1;
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
          <p className="text-gray-500">Building recommendations...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-[1400px] mx-auto px-2 sm:px-3 py-8 space-y-8">
      {/* Drawer overlay */}
      <AnimatePresence>
        {detailRec && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.3 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black z-40"
              onClick={() => setDetailRec(null)}
            />
            <DetailDrawer rec={detailRec} onClose={() => setDetailRec(null)} />
          </>
        )}
      </AnimatePresence>

      {/* Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <Sparkles className="w-8 h-8 text-indigo-500" />
          Smart Recommendations
        </h1>
        <p className="text-gray-500 mt-1">
          Actions pulled from your menu data, inventory, local weather, and nearby competitor reviews
        </p>
      </motion.div>

      {/* Context chips */}
      <div className="flex flex-wrap gap-3">
        <span className="text-sm font-semibold px-4 py-2 rounded-full bg-sky-50 text-sky-700 border border-sky-200 flex items-center gap-2">
          <CloudRain className="w-4 h-4" /> Rainy this week
        </span>
        <span className="text-sm font-semibold px-4 py-2 rounded-full bg-gray-50 text-gray-600 border border-gray-200 flex items-center gap-2">
          <MapPin className="w-4 h-4" /> Richardson, TX
        </span>
        <span className="text-sm font-semibold px-4 py-2 rounded-full bg-amber-50 text-amber-700 border border-amber-200 flex items-center gap-2">
          <Star className="w-4 h-4" /> Competitors: cleanliness complaints
        </span>
        <span className="text-sm font-semibold px-4 py-2 rounded-full bg-slate-50 text-slate-500 border border-slate-200">
          No major events this week
        </span>
      </div>

      {/* Opportunity Widgets */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {WIDGETS.map((w, i) => {
          const isSelected = selectedWidget === w.type;
          const count = widgetCounts[w.type];
          const Icon = w.icon;
          return (
            <motion.button
              key={w.type}
              custom={i}
              variants={fadeUp}
              initial="hidden"
              animate="visible"
              onClick={() => {
                setSelectedWidget(isSelected ? null : w.type);
                setPriorityFilter("all");
              }}
              className={`relative text-left p-5 rounded-2xl border-2 transition-all duration-200 ${
                isSelected
                  ? `${w.borderColor} bg-gradient-to-br ${w.gradient} shadow-lg ring-2 ring-offset-2 ${w.borderColor.replace("border-", "ring-")}`
                  : "border-gray-100 bg-white hover:border-gray-200 hover:shadow-md"
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className={`p-2 rounded-xl ${w.iconBg}`}>
                  <Icon className="w-5 h-5" />
                </div>
                {count > 0 && (
                  <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                    isSelected ? "bg-white/80 text-gray-900" : "bg-gray-100 text-gray-600"
                  }`}>
                    {count}
                  </span>
                )}
              </div>
              <h3 className="font-bold text-gray-900 text-sm">{w.title}</h3>
              <p className="text-xs text-gray-500 mt-1 leading-relaxed">{w.description}</p>
            </motion.button>
          );
        })}
      </div>

      {/* Priority Filter */}
      {selectedWidget && (
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="flex flex-wrap gap-2">
          {(["all", "critical", "high", "medium", "low"] as Priority[]).map((p) => {
            const isActive = priorityFilter === p;
            const count = priorityCounts[p] || 0;
            return (
              <button
                key={p}
                onClick={() => setPriorityFilter(p)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all flex items-center gap-2 ${
                  isActive ? "bg-gray-900 text-white shadow-md" : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"
                }`}
              >
                {p === "all" ? "All Priorities" : p.charAt(0).toUpperCase() + p.slice(1)}
                <span className={`text-xs font-bold px-1.5 py-0.5 rounded-full ${isActive ? "bg-white/20 text-white" : "bg-gray-100 text-gray-500"}`}>
                  {count}
                </span>
              </button>
            );
          })}
        </motion.div>
      )}

      {/* Prompt to select widget */}
      {!selectedWidget && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          className="bg-gradient-to-br from-gray-50 to-white border border-gray-100 rounded-2xl p-12 text-center"
        >
          <Sparkles className="w-10 h-10 text-indigo-300 mx-auto mb-3" />
          <p className="text-gray-500 text-lg font-medium">Choose an opportunity area to see recommendations</p>
          <p className="text-gray-400 text-sm mt-1">
            {allRecs.length} recommendation{allRecs.length !== 1 ? "s" : ""} across all categories
          </p>
        </motion.div>
      )}

      {/* Recommendation Cards */}
      <AnimatePresence mode="wait">
        {selectedWidget && (
          <motion.div
            key={selectedWidget}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
            className="space-y-4"
          >
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-bold text-gray-900">
                {WIDGETS.find((w) => w.type === selectedWidget)?.title}
              </h2>
              <span className="text-sm text-gray-400">
                {filteredRecs.length} recommendation{filteredRecs.length !== 1 ? "s" : ""}
              </span>
            </div>

            {filteredRecs.length === 0 && (
              <div className="bg-gray-50 rounded-2xl p-8 text-center border border-gray-100">
                <p className="text-gray-400 font-medium">No recommendations match this filter</p>
              </div>
            )}

            {filteredRecs.map((rec, i) => (
              <motion.div
                key={rec.id}
                custom={i}
                variants={fadeUp}
                initial="hidden"
                animate="visible"
                className="bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow p-5"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-2">
                      <h3 className="font-semibold text-gray-900">{rec.title}</h3>
                      <span className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full border ${PRIORITY_CONFIG[rec.priority]?.bg} ${PRIORITY_CONFIG[rec.priority]?.color}`}>
                        {PRIORITY_CONFIG[rec.priority]?.label}
                      </span>
                    </div>

                    {rec.target && (
                      <p className="text-sm font-medium text-indigo-600 mb-1">{rec.target}</p>
                    )}

                    <p className="text-gray-600 text-sm mb-3 leading-relaxed">{rec.description}</p>

                    <div className="flex items-center gap-3 flex-wrap">
                      <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full border ${SOURCE_CONFIG[rec.source]?.color}`}>
                        {rec.sourceLabel}
                      </span>
                      <button
                        onClick={() => setDetailRec(rec)}
                        className="text-sm font-medium text-indigo-600 hover:text-indigo-700 flex items-center gap-1 transition"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        View Details
                      </button>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Page export with Suspense boundary for useSearchParams              */
/* ------------------------------------------------------------------ */
export default function RecommendationsPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    }>
      <RecommendationsInner />
    </Suspense>
  );
}
