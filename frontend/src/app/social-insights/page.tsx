"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  Instagram,
  Video,
  TrendingUp,
  Clock,
  Sparkles,
  Zap,
  Heart,
  MessageCircle,
  Share2,
  Eye,
  Music,
  Hash,
  Star,
  Megaphone,
  DollarSign,
  Lightbulb,
  Flame,
  Calendar,
  ChevronRight,
  X,
  Link2,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { motion } from "framer-motion";

import { api } from "@/lib/api";
import { useRestaurant } from "@/context/RestaurantContext";

/* ------------------------------------------------------------------ */
/*  Animation variants                                                  */
/* ------------------------------------------------------------------ */
const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.45, ease: "easeOut" as const },
  }),
};

const staggerContainer = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
};

/* ------------------------------------------------------------------ */
/*  Inline markdown renderer                                            */
/* ------------------------------------------------------------------ */
function renderInlineMarkdown(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i} className="font-semibold text-slate-900">{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      return <em key={i}>{part.slice(1, -1)}</em>;
    }
    return <span key={i}>{part}</span>;
  });
}

/* ------------------------------------------------------------------ */
/*  Hardcoded trend signals                                             */
/* ------------------------------------------------------------------ */
const TRENDING_SONGS = [
  { name: "City Lights Beat", vibe: "Upbeat / Aesthetic" },
  { name: "Midnight Masala Mix", vibe: "Vibey / Cultural" },
  { name: "Spicy Drop Remix", vibe: "High energy / Fun" },
];

const TRENDING_HASHTAGS = [
  "#FoodieFinds",
  "#InstaEats",
  "#TikTokTastes",
  "#CravingNow",
  "#StreetToTable",
];

const PLATFORM_NOTES = [
  { platform: "Instagram", note: "Favors polished reels and aesthetic plating shots", icon: Instagram },
  { platform: "TikTok", note: "Works well for fast edits, food reveals, and satisfying prep clips", icon: Video },
];

/* ------------------------------------------------------------------ */
/*  Helpers                                                             */
/* ------------------------------------------------------------------ */
function formatHour(h: number): string {
  if (h === 0) return "12 AM";
  if (h === 12) return "12 PM";
  return h > 12 ? `${h - 12} PM` : `${h} AM`;
}

function engagementLabel(rate: number): { label: string; color: string } {
  if (rate >= 0.08) return { label: "Best", color: "bg-emerald-100 text-emerald-700" };
  if (rate >= 0.04) return { label: "Good", color: "bg-blue-100 text-blue-700" };
  return { label: "Needs Improvement", color: "bg-amber-100 text-amber-700" };
}

function postTakeaway(engagement: number, avgEngagement: number, postType: string): string {
  if (engagement > avgEngagement * 1.3) {
    if (postType?.toLowerCase().includes("reel") || postType?.toLowerCase().includes("video"))
      return "Strong format for featured dishes";
    return "Post more like this";
  }
  if (engagement > avgEngagement) return "Good format for weekend promotions";
  return "Works well for quick offers";
}

/* ------------------------------------------------------------------ */
/*  Chart tooltips                                                      */
/* ------------------------------------------------------------------ */
function EngagementTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-lg px-4 py-3 text-sm">
      <p className="font-semibold text-slate-700">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} className="text-slate-600">
          <span className="font-medium" style={{ color: p.color }}>{p.name}:</span> {Math.round(p.value)}
        </p>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main page                                                           */
/* ------------------------------------------------------------------ */
export default function SocialInsightsPage() {
  const { restaurantId } = useRestaurant();

  const [analytics, setAnalytics] = useState<any>(null);
  const [menuData, setMenuData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [draftModal, setDraftModal] = useState<{
    title: string;
    description: string;
    target_item?: string;
    context?: Record<string, any>;
  } | null>(null);
  const [elaboration, setElaboration] = useState<string | null>(null);
  const [elaborating, setElaborating] = useState(false);

  const handleDraftPost = useCallback(async (idea: any) => {
    const description = [
      `Platform: ${idea.platform}`,
      `Format: ${idea.format}`,
      `Hook: "${idea.hook}"`,
      `Visual Direction: ${idea.visual}`,
      `Suggested Song: ${idea.song}`,
      `Hashtags: ${idea.hashtags.join(" ")}`,
      `Best Time: ${idea.bestTime}`,
      `Why: ${idea.reason}`,
    ].join("\n");
    setDraftModal({
      title: idea.title,
      description,
      target_item: idea.menuItem,
      context: { recommendation_type: "social_post_idea", platform: idea.platform },
    });
    setElaboration(null);
    setElaborating(true);
    try {
      const result = await api.elaborateRecommendation({
        title: `Social Post Idea: ${idea.title}`,
        description: `Write a detailed social media post draft and creative brief for this content idea:\n\n${description}\n\nInclude: a ready-to-post caption with emojis, 3 visual shot suggestions, posting tips, and engagement hooks. Make it feel like a real content creator brief.`,
        target_item: idea.menuItem,
        context: { recommendation_type: "social_post_idea", platform: idea.platform },
      });
      setElaboration(result.elaboration);
    } catch {
      setElaboration("Sorry, couldn't generate a draft right now. Please try again in a moment.");
    } finally {
      setElaborating(false);
    }
  }, []);

  useEffect(() => {
    (async () => {
      if (!restaurantId) {
        setLoading(false);
        setError("no_restaurant");
        return;
      }
      try {
        setLoading(true);
        setError(null);
        const [social, menu] = await Promise.all([
          api.getSocialAnalytics(restaurantId),
          api.getMenuAnalytics(restaurantId).catch(() => null),
        ]);
        setAnalytics(social);
        setMenuData(menu);
      } catch (err: any) {
        setError(err.message ?? "Failed to load social analytics");
      } finally {
        setLoading(false);
      }
    })();
  }, [restaurantId]);

  /* ---------- loading / empty ---------- */
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
          <p className="text-slate-400">Loading social insights...</p>
        </div>
      </div>
    );
  }

  if (error && !analytics) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-10 max-w-lg text-center">
          <div className="w-16 h-16 bg-pink-50 rounded-full flex items-center justify-center mx-auto mb-5">
            <Instagram className="w-8 h-8 text-pink-400" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">No social data yet</h2>
          <p className="text-slate-500 mb-6 leading-relaxed">
            Upload your social media post data to unlock engagement insights, trend-aware content ideas, and smart recommendations.
          </p>
          <Link
            href="/upload"
            className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6 py-3 rounded-xl transition-colors text-sm shadow-sm"
          >
            <Zap className="w-4 h-4" /> Upload Data
          </Link>
        </div>
      </div>
    );
  }

  /* ---------- extract data ---------- */
  const engagementByType = (analytics?.engagement_by_type ?? []).map((e: any) => ({
    ...e,
    avg_engagement: Math.round((e.avg_likes ?? 0) + (e.avg_comments ?? 0) + (e.avg_shares ?? 0)),
    engagement_rate: ((e.avg_likes ?? 0) + (e.avg_comments ?? 0) + (e.avg_shares ?? 0)) / Math.max(e.avg_reach ?? 1, 1),
  }));
  const engagementByPlatform = (analytics?.engagement_by_platform ?? []).map((e: any) => ({
    ...e,
    avg_engagement: e.avg_engagement ?? Math.round((e.avg_likes ?? 0) + (e.avg_comments ?? 0) + (e.avg_shares ?? 0)),
    engagement_rate: ((e.avg_likes ?? 0) + (e.avg_comments ?? 0) + (e.avg_shares ?? 0)) / Math.max(e.avg_reach ?? 1, 1),
  }));
  const bestTimes = analytics?.best_times ?? [];
  const trendingItems = analytics?.trending_items ?? [];
  const topPosts = analytics?.top_posts ?? [];
  // Separate day-of-week and hour entries from best_times
  const dayEntries = bestTimes.filter((t: any) => t.day_of_week);
  const hourEntries = bestTimes.filter((t: any) => t.hour != null).sort((a: any, b: any) => a.hour - b.hour);

  // Compute KPIs
  const bestPlatform = engagementByPlatform.length > 0
    ? [...engagementByPlatform].sort((a: any, b: any) => b.engagement_rate - a.engagement_rate)[0]
    : null;

  const bestFormat = engagementByType.length > 0
    ? [...engagementByType].sort((a: any, b: any) => b.engagement_rate - a.engagement_rate)[0]
    : null;

  const bestMenuItem = trendingItems.length > 0 ? trendingItems[0] : null;

  const bestDay = dayEntries.length > 0
    ? [...dayEntries].sort((a: any, b: any) => (b.engagement ?? 0) - (a.engagement ?? 0))[0]
    : null;
  const bestHour = hourEntries.length > 0
    ? [...hourEntries].sort((a: any, b: any) => (b.engagement ?? 0) - (a.engagement ?? 0))[0]
    : null;

  const avgEngAll = topPosts.length > 0
    ? topPosts.reduce((s: number, p: any) => s + (p.engagement ?? 0), 0) / topPosts.length
    : 0;

  // Menu + social opportunities
  const marginAnalysis = menuData?.margin_analysis ?? [];

  // Build menu+social cross-reference
  const menuSocialOps = (() => {
    if (!trendingItems.length || !marginAnalysis.length) return [];
    const marginMap: Record<string, any> = {};
    for (const m of marginAnalysis) {
      marginMap[m.item] = m;
    }
    return trendingItems
      .filter((t: any) => marginMap[t.item])
      .map((t: any) => ({
        item: t.item,
        avg_engagement: t.avg_engagement,
        post_count: t.post_count,
        margin: marginMap[t.item]?.margin ?? 0,
        margin_pct: marginMap[t.item]?.margin_pct ?? 0,
      }))
      .sort((a: any, b: any) => (b.margin * b.avg_engagement) - (a.margin * a.avg_engagement))
      .slice(0, 6);
  })();

  // Generate post ideas
  const postIdeas = (() => {
    const items = trendingItems.slice(0, 3);
    if (!items.length) return [];
    const igIdeas = items.map((item: any, i: number) => {
      const concepts = [
        { title: `${item.item} Glow-Up Reel`, hook: `This is the dish everyone secretly comes back for`, visual: "Close-up plating, butter brush shot, slow reveal", format: "Reel" },
        { title: `Behind the ${item.item}`, hook: `Watch our chef work magic in 15 seconds`, visual: "Kitchen action, steam rising, final plate reveal", format: "Reel" },
        { title: `${item.item} — Worth the Hype?`, hook: `Our most popular dish, and here's why`, visual: "Aesthetic flat lay, drizzle moment, first bite reaction", format: "Carousel" },
      ];
      const concept = concepts[i % concepts.length];
      return {
        platform: "Instagram",
        ...concept,
        menuItem: item.item,
        song: TRENDING_SONGS[i % TRENDING_SONGS.length].name,
        hashtags: [TRENDING_HASHTAGS[0], TRENDING_HASHTAGS[1], TRENDING_HASHTAGS[3]],
        bestTime: bestDay ? `${bestDay.day_of_week} ${bestHour ? formatHour(bestHour.hour) : "Evening"}` : "Friday Evening",
        reason: `${item.item} gets above-average engagement and ${concept.format.toLowerCase()}s are your strongest format`,
      };
    });
    const tkIdeas = items.map((item: any, i: number) => {
      const concepts = [
        { title: `${item.item} in 7 Seconds`, hook: `Watch this go from pan to plate`, visual: "Fast cuts, sauce toss, cheese finish, plated reveal", format: "Short Video" },
        { title: `POV: You Ordered ${item.item}`, hook: `When the food is this good, you don't share`, visual: "First person perspective, steam close-up, satisfying bite", format: "Short Video" },
        { title: `Making ${item.item} ASMR Style`, hook: `Turn the volume up for this one`, visual: "Sizzle sounds, chopping, plating with natural audio", format: "Short Video" },
      ];
      const concept = concepts[i % concepts.length];
      return {
        platform: "TikTok",
        ...concept,
        menuItem: item.item,
        song: TRENDING_SONGS[(i + 1) % TRENDING_SONGS.length].name,
        hashtags: [TRENDING_HASHTAGS[2], TRENDING_HASHTAGS[4]],
        bestTime: bestDay ? `${bestDay.day_of_week} ${bestHour ? formatHour(Math.max(bestHour.hour - 1, 10)) : "Afternoon"}` : "Saturday Afternoon",
        reason: `Fast edits and food reveals match TikTok's strongest engagement patterns`,
      };
    });
    return [...igIdeas, ...tkIdeas];
  })();

  // Best posting windows
  const postingWindows = (() => {
    if (!dayEntries.length) return [];
    const sorted = [...dayEntries].sort((a: any, b: any) => (b.engagement ?? 0) - (a.engagement ?? 0));
    return sorted.slice(0, 4).map((d: any, i: number) => {
      const badge = i === 0
        ? { label: "Best Window", color: "bg-emerald-100 text-emerald-700" }
        : i === 1
          ? { label: "Good Window", color: "bg-blue-100 text-blue-700" }
          : { label: "Test More", color: "bg-slate-100 text-slate-600" };
      const tips = [
        "Best for food reveal posts",
        "Strong for featured dishes",
        "Good for quick offers",
        "Worth experimenting with",
      ];
      return {
        day: d.day_of_week,
        engagement: Math.round(d.engagement ?? 0),
        reach: Math.round(d.reach ?? 0),
        tip: tips[i] ?? tips[3],
        ...badge,
      };
    });
  })();

  const hasData = engagementByType.length > 0 || trendingItems.length > 0;

  return (
    <div className="max-w-7xl mx-auto px-4 py-10 space-y-10">
      {/* ═══════ HEADER ═══════ */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <h1 className="text-3xl font-bold text-slate-900">
          Social Media Insights & Growth Opportunities
        </h1>
        <p className="text-slate-500 mt-1.5 max-w-xl">
          See what content works, when to post, and exactly what to create next to grow your restaurant's social presence.
        </p>
      </motion.div>

      {!hasData && (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-12 text-center">
          <p className="text-slate-500 text-lg">No social data yet. Upload data to get started.</p>
        </div>
      )}

      {/* ═══════ KEY BUSINESS INSIGHTS ═══════ */}
      {hasData && (
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5"
        >
          {/* Best Platform */}
          <motion.div variants={fadeUp} custom={0}
            className="group bg-gradient-to-br from-pink-50 to-white rounded-2xl border border-pink-200 shadow-sm p-6 hover:shadow-md hover:border-pink-300 transition-all"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Best Platform</p>
                <p className="text-2xl font-bold text-slate-900 mt-2">
                  {bestPlatform?.platform ?? "—"}
                </p>
                <p className="text-sm text-slate-400 mt-2">
                  {bestPlatform ? "Highest average engagement across recent posts" : "Upload social data"}
                </p>
              </div>
              <div className="w-11 h-11 bg-pink-100 rounded-xl flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
                <Instagram className="w-5 h-5 text-pink-500" />
              </div>
            </div>
            {bestPlatform && (
              <div className="mt-3">
                <span className="inline-flex items-center gap-1 text-xs font-semibold text-pink-600 bg-pink-100 px-2.5 py-1 rounded-full">
                  <Flame className="w-3 h-3" /> Top performer
                </span>
              </div>
            )}
          </motion.div>

          {/* Best Format */}
          <motion.div variants={fadeUp} custom={1}
            className="group bg-gradient-to-br from-violet-50 to-white rounded-2xl border border-violet-200 shadow-sm p-6 hover:shadow-md hover:border-violet-300 transition-all"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Best Content Format</p>
                <p className="text-2xl font-bold text-slate-900 mt-2">
                  {bestFormat?.post_type ?? "—"}
                </p>
                <p className="text-sm text-slate-400 mt-2">
                  {bestFormat ? "Short videos get the most attention" : "No data yet"}
                </p>
              </div>
              <div className="w-11 h-11 bg-violet-100 rounded-xl flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
                <Video className="w-5 h-5 text-violet-500" />
              </div>
            </div>
            {bestFormat && (
              <div className="mt-3">
                <span className="inline-flex items-center gap-1 text-xs font-semibold text-violet-600 bg-violet-100 px-2.5 py-1 rounded-full">
                  <TrendingUp className="w-3 h-3" /> High engagement
                </span>
              </div>
            )}
          </motion.div>

          {/* Most Engaging Menu Item */}
          <motion.div variants={fadeUp} custom={2}
            className="group bg-gradient-to-br from-amber-50 to-white rounded-2xl border border-amber-200 shadow-sm p-6 hover:shadow-md hover:border-amber-300 transition-all"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Most Engaging Dish</p>
                <p className="text-2xl font-bold text-slate-900 mt-2 truncate">
                  {bestMenuItem?.item ?? "—"}
                </p>
                <p className="text-sm text-slate-400 mt-2">
                  {bestMenuItem ? "Posts about this dish perform best" : "No data yet"}
                </p>
              </div>
              <div className="w-11 h-11 bg-amber-100 rounded-xl flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
                <Star className="w-5 h-5 text-amber-500" />
              </div>
            </div>
            {bestMenuItem && (
              <div className="mt-3">
                <span className="inline-flex items-center gap-1 text-xs font-semibold text-amber-600 bg-amber-100 px-2.5 py-1 rounded-full">
                  <Heart className="w-3 h-3" /> Fan favorite
                </span>
              </div>
            )}
          </motion.div>

          {/* Best Time to Post */}
          <motion.div variants={fadeUp} custom={3}
            className="group bg-gradient-to-br from-blue-50 to-white rounded-2xl border border-blue-200 shadow-sm p-6 hover:shadow-md hover:border-blue-300 transition-all"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Best Time to Post</p>
                <p className="text-2xl font-bold text-slate-900 mt-2">
                  {bestDay ? `${bestDay.day_of_week}${bestHour ? `, ${formatHour(bestHour.hour)}` : ""}` : "—"}
                </p>
                <p className="text-sm text-slate-400 mt-2">
                  {bestDay ? "This posting window gets the strongest response" : "No data yet"}
                </p>
              </div>
              <div className="w-11 h-11 bg-blue-100 rounded-xl flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
                <Clock className="w-5 h-5 text-blue-500" />
              </div>
            </div>
            {bestDay && (
              <div className="mt-3">
                <span className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 bg-blue-100 px-2.5 py-1 rounded-full">
                  <Calendar className="w-3 h-3" /> Peak window
                </span>
              </div>
            )}
          </motion.div>
        </motion.div>
      )}

      {/* ═══════ SOCIAL PERFORMANCE SNAPSHOT ═══════ */}
      {(topPosts.length > 0 || engagementByType.length > 0) && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
        >
          <div className="mb-5">
            <h2 className="text-lg font-semibold text-slate-900">Social Performance Snapshot</h2>
            <p className="text-sm text-slate-400 mt-0.5">Your best content and what format works</p>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Performing Posts */}
            {topPosts.length > 0 && (
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
                <h3 className="text-base font-semibold text-slate-900 mb-4 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-indigo-500" /> Top Performing Posts
                </h3>
                <div className="space-y-3">
                  {topPosts.slice(0, 5).map((post: any, i: number) => {
                    const takeaway = postTakeaway(post.engagement, avgEngAll, post.post_type ?? "");
                    return (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.4 + i * 0.08 }}
                        className="rounded-xl border border-slate-100 bg-gradient-to-r from-slate-50/50 to-transparent p-4 hover:shadow-sm transition-shadow"
                      >
                        <div className="flex items-start justify-between gap-3 mb-2">
                          <div className="flex items-center gap-2 min-w-0">
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full shrink-0 ${
                              post.platform === "Instagram" ? "bg-pink-100 text-pink-700" : "bg-slate-800 text-white"
                            }`}>
                              {post.platform}
                            </span>
                            <span className="text-xs font-medium text-slate-500">{post.post_type}</span>
                          </div>
                          <span className="text-xs text-slate-400 shrink-0">
                            {post.posted_at ? new Date(post.posted_at).toLocaleDateString() : ""}
                          </span>
                        </div>
                        {post.menu_item_name && (
                          <p className="text-sm font-semibold text-slate-800 mb-1">{post.menu_item_name}</p>
                        )}
                        {post.content_summary && (
                          <p className="text-xs text-slate-500 mb-2 line-clamp-1">{post.content_summary}</p>
                        )}
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3 text-xs text-slate-500">
                            <span className="flex items-center gap-1"><Heart className="w-3 h-3" /> {post.likes}</span>
                            <span className="flex items-center gap-1"><MessageCircle className="w-3 h-3" /> {post.comments}</span>
                            <span className="flex items-center gap-1"><Share2 className="w-3 h-3" /> {post.shares}</span>
                            <span className="flex items-center gap-1"><Eye className="w-3 h-3" /> {post.reach?.toLocaleString()}</span>
                          </div>
                          <span className="text-[10px] font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full">
                            {takeaway}
                          </span>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Engagement by Platform & Format */}
            <div className="space-y-6">
              {engagementByPlatform.length > 0 && (
                <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
                  <h3 className="text-base font-semibold text-slate-900 mb-4">Engagement by Platform</h3>
                  <div className="space-y-3">
                    {engagementByPlatform.map((p: any, i: number) => {
                      const badge = engagementLabel(p.engagement_rate);
                      return (
                        <motion.div
                          key={p.platform}
                          initial={{ opacity: 0, x: 10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.4 + i * 0.08 }}
                          className="flex items-center justify-between rounded-xl border border-slate-100 p-3.5"
                        >
                          <div className="flex items-center gap-3">
                            <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${
                              p.platform === "Instagram" ? "bg-pink-100" : "bg-slate-100"
                            }`}>
                              {p.platform === "Instagram" ? <Instagram className="w-4 h-4 text-pink-600" /> : <Video className="w-4 h-4 text-slate-700" />}
                            </div>
                            <div>
                              <p className="text-sm font-semibold text-slate-800">{p.platform}</p>
                              <p className="text-xs text-slate-400">{p.post_count} posts · {Math.round(p.avg_reach)} avg reach</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-sm font-bold text-slate-900">{Math.round(p.avg_engagement)}</p>
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${badge.color}`}>{badge.label}</span>
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                </div>
              )}

              {engagementByType.length > 0 && (
                <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
                  <h3 className="text-base font-semibold text-slate-900 mb-4">Engagement by Format</h3>
                  <ResponsiveContainer width="100%" height={180}>
                    <BarChart data={engagementByType} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="post_type" tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
                      <Tooltip content={<EngagementTooltip />} />
                      <Bar dataKey="avg_likes" name="Likes" stackId="a" fill="#f472b6" radius={[0, 0, 0, 0]} />
                      <Bar dataKey="avg_comments" name="Comments" stackId="a" fill="#818cf8" radius={[0, 0, 0, 0]} />
                      <Bar dataKey="avg_shares" name="Shares" stackId="a" fill="#34d399" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      )}

      {/* ═══════ CURRENT TREND SIGNALS ═══════ */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4, duration: 0.5 }}
        className="bg-gradient-to-br from-fuchsia-50 via-violet-50 to-indigo-50 rounded-2xl border border-violet-200 shadow-sm p-6"
      >
        <div className="flex items-center justify-between mb-1">
          <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-fuchsia-500" /> Current Trend Signals
          </h2>
          <span className="text-[10px] font-medium text-slate-400 bg-white/60 px-2.5 py-1 rounded-full border border-slate-200">
            Hardcoded — API-ready for future integration
          </span>
        </div>
        <p className="text-sm text-slate-500 mb-5">Trending audio, hashtags, and platform tips to keep your content fresh</p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Trending Songs */}
          <div>
            <h3 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-1.5">
              <Music className="w-4 h-4 text-fuchsia-500" /> Trending Songs
            </h3>
            <div className="space-y-2">
              {TRENDING_SONGS.map((song, i) => (
                <motion.div
                  key={song.name}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.5 + i * 0.08 }}
                  className="flex items-center gap-3 bg-white/70 border border-white rounded-xl p-3 hover:shadow-sm transition-shadow"
                >
                  <div className="w-8 h-8 bg-gradient-to-br from-fuchsia-400 to-violet-500 rounded-lg flex items-center justify-center shrink-0">
                    <Music className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-800">{song.name}</p>
                    <p className="text-[10px] text-slate-400">{song.vibe}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Trending Hashtags */}
          <div>
            <h3 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-1.5">
              <Hash className="w-4 h-4 text-indigo-500" /> Trending Hashtags
            </h3>
            <div className="flex flex-wrap gap-2">
              {TRENDING_HASHTAGS.map((tag, i) => (
                <motion.span
                  key={tag}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.5 + i * 0.06 }}
                  className="inline-flex items-center gap-1 text-sm font-semibold px-3.5 py-2 rounded-full bg-white/80 border border-indigo-200 text-indigo-700 hover:bg-indigo-50 hover:border-indigo-300 transition-colors cursor-default"
                >
                  {tag}
                </motion.span>
              ))}
            </div>
          </div>

          {/* Platform Notes */}
          <div>
            <h3 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-1.5">
              <Lightbulb className="w-4 h-4 text-amber-500" /> Platform Tips
            </h3>
            <div className="space-y-2">
              {PLATFORM_NOTES.map((p, i) => {
                const Icon = p.icon;
                return (
                  <motion.div
                    key={p.platform}
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5 + i * 0.1 }}
                    className="bg-white/70 border border-white rounded-xl p-3 hover:shadow-sm transition-shadow"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Icon className="w-4 h-4 text-slate-600" />
                      <span className="text-sm font-semibold text-slate-800">{p.platform}</span>
                    </div>
                    <p className="text-xs text-slate-500 leading-relaxed">{p.note}</p>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </div>
      </motion.div>

      {/* ═══════ CONTENT OPPORTUNITIES ═══════ */}
      {trendingItems.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.5 }}
          className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6"
        >
          <div className="mb-5">
            <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <Megaphone className="w-5 h-5 text-indigo-500" /> Content Opportunities
            </h2>
            <p className="text-sm text-slate-400 mt-0.5">Which menu items and themes are working best on social</p>
          </div>
          <div className="space-y-3">
            {trendingItems.slice(0, 6).map((item: any, i: number) => {
              const maxEng = Math.max(...trendingItems.map((t: any) => t.avg_engagement ?? 0), 1);
              const pct = ((item.avg_engagement ?? 0) / maxEng) * 100;
              const label = pct >= 80 ? "Audience loves this" : pct >= 50 ? "Good item to feature" : "Worth posting more";
              return (
                <motion.div
                  key={item.item}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.55 + i * 0.06 }}
                  className="flex items-center gap-4"
                >
                  <span className="w-6 text-center text-xs font-bold text-slate-400">{i + 1}</span>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-semibold text-slate-800">{item.item}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-slate-400">{item.post_count} posts</span>
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-600">{label}</span>
                      </div>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <motion.div
                        className="bg-indigo-500 h-2 rounded-full"
                        initial={{ width: 0 }}
                        animate={{ width: `${pct}%` }}
                        transition={{ delay: 0.6 + i * 0.06, duration: 0.5 }}
                      />
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </motion.div>
      )}

      {/* ═══════ BEST TIME TO POST ═══════ */}
      {postingWindows.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.55, duration: 0.5 }}
        >
          <div className="mb-5">
            <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <Clock className="w-5 h-5 text-blue-500" /> Best Time to Post
            </h2>
            <p className="text-sm text-slate-400 mt-0.5">When your posts tend to get the strongest response</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {postingWindows.map((w: any, i: number) => (
              <motion.div
                key={w.day}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 + i * 0.08 }}
                className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 hover:shadow-md hover:border-slate-300 transition-all"
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-lg font-bold text-slate-900">{w.day}</span>
                  <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full ${w.color}`}>{w.label}</span>
                </div>
                <p className="text-sm text-slate-500 mb-2">{w.tip}</p>
                <div className="flex items-center gap-3 text-xs text-slate-400">
                  <span className="flex items-center gap-1"><Heart className="w-3 h-3" /> {w.engagement} avg engagement</span>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* ═══════ TREND-AWARE POST IDEAS ═══════ */}
      {postIdeas.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.5 }}
        >
          <div className="mb-5">
            <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-fuchsia-500" /> Trend-Aware Post Ideas
            </h2>
            <p className="text-sm text-slate-400 mt-0.5">AI-generated content ideas based on your data and current trends</p>
          </div>
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5"
          >
            {postIdeas.slice(0, 6).map((idea: any, i: number) => (
              <motion.div
                key={i}
                variants={fadeUp}
                custom={i}
                className={`rounded-2xl border p-5 hover:shadow-md transition-all ${
                  idea.platform === "Instagram"
                    ? "bg-gradient-to-br from-pink-50 to-white border-pink-200"
                    : "bg-gradient-to-br from-slate-50 to-white border-slate-200"
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full ${
                    idea.platform === "Instagram" ? "bg-pink-100 text-pink-700" : "bg-slate-800 text-white"
                  }`}>
                    {idea.platform}
                  </span>
                  <span className="text-[10px] font-medium text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">{idea.format}</span>
                </div>
                <h3 className="text-base font-bold text-slate-900 mb-1">{idea.title}</h3>
                <p className="text-sm font-medium text-indigo-600 mb-2">{idea.menuItem}</p>

                <div className="space-y-2 mb-4">
                  <div>
                    <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Hook</p>
                    <p className="text-sm text-slate-600 italic">"{idea.hook}"</p>
                  </div>
                  <div>
                    <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Visual Direction</p>
                    <p className="text-xs text-slate-500">{idea.visual}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2 mb-2 flex-wrap">
                  <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-fuchsia-600 bg-fuchsia-50 px-2 py-0.5 rounded-full border border-fuchsia-200">
                    <Music className="w-2.5 h-2.5" /> {idea.song}
                  </span>
                  {idea.hashtags.map((tag: string) => (
                    <span key={tag} className="text-[10px] font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full">
                      {tag}
                    </span>
                  ))}
                </div>

                <div className="flex items-center gap-2 mb-3 text-xs text-slate-400">
                  <Clock className="w-3 h-3" />
                  <span>Best: {idea.bestTime}</span>
                </div>

                <p className="text-xs text-slate-500 leading-relaxed mb-3">
                  {idea.reason}
                </p>

                <button
                  onClick={() => handleDraftPost(idea)}
                  className="w-full text-center text-xs font-semibold text-indigo-600 hover:text-indigo-700 bg-indigo-50 hover:bg-indigo-100 py-2 rounded-lg transition-colors inline-flex items-center justify-center gap-1"
                >
                  Draft Post <ChevronRight className="w-3 h-3" />
                </button>
              </motion.div>
            ))}
          </motion.div>
        </motion.div>
      )}

      {/* ═══════ MENU + SOCIAL OPPORTUNITIES ═══════ */}
      {menuSocialOps.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.65, duration: 0.5 }}
          className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6"
        >
          <div className="mb-5">
            <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-emerald-500" /> Menu + Social Opportunities
            </h2>
            <p className="text-sm text-slate-400 mt-0.5">Items with strong margin and social engagement — worth featuring more</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {menuSocialOps.map((op: any, i: number) => {
              const isHighMargin = op.margin_pct > 50;
              const isHighEng = op.avg_engagement > (trendingItems[0]?.avg_engagement ?? 0) * 0.6;
              let suggestion = "Worth featuring more often";
              if (isHighMargin && isHighEng) suggestion = "Strong margin & engagement — promote heavily";
              else if (isHighMargin) suggestion = "High-margin item with social potential";
              else if (isHighEng) suggestion = "Strong visibility opportunity";

              return (
                <motion.div
                  key={op.item}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.7 + i * 0.06 }}
                  className="rounded-xl border border-emerald-100 bg-emerald-50/30 p-4 hover:shadow-sm transition-shadow"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-bold text-slate-800">{op.item}</span>
                    <span className="text-[10px] font-semibold text-emerald-600 bg-emerald-100 px-2 py-0.5 rounded-full">
                      {op.margin_pct?.toFixed(0)}% margin
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mb-2">{suggestion}</p>
                  <div className="flex items-center gap-3 text-xs text-slate-400">
                    <span>{Math.round(op.avg_engagement)} avg engagement</span>
                    <span>{op.post_count} posts</span>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </motion.div>
      )}

      {/* ═══════ CONNECT ACCOUNTS PLACEHOLDER ═══════ */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.75, duration: 0.5 }}
        className="bg-gradient-to-r from-slate-50 to-slate-100 rounded-2xl border border-dashed border-slate-300 p-8"
      >
        <div className="flex flex-col sm:flex-row items-center gap-6">
          <div className="w-14 h-14 bg-white rounded-2xl border border-slate-200 shadow-sm flex items-center justify-center shrink-0">
            <Link2 className="w-6 h-6 text-slate-400" />
          </div>
          <div className="text-center sm:text-left flex-1">
            <h3 className="text-base font-bold text-slate-800">Connect Your Social Accounts</h3>
            <p className="text-sm text-slate-500 mt-1 max-w-lg">
              Link your Instagram or TikTok to automatically pull real engagement data, detect menu items in posts, and get live trend signals — no more CSV uploads.
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              disabled
              className="inline-flex items-center gap-2 bg-gradient-to-r from-pink-500 to-purple-500 text-white font-semibold px-5 py-2.5 rounded-xl text-sm shadow-sm opacity-60 cursor-not-allowed"
            >
              <Instagram className="w-4 h-4" /> Instagram
            </button>
            <button
              disabled
              className="inline-flex items-center gap-2 bg-slate-900 text-white font-semibold px-5 py-2.5 rounded-xl text-sm shadow-sm opacity-60 cursor-not-allowed"
            >
              <Video className="w-4 h-4" /> TikTok
            </button>
          </div>
        </div>
        <p className="text-[10px] text-slate-400 text-center mt-4">Coming soon — OAuth integration with Meta Graph API and TikTok Business API</p>
      </motion.div>

      {/* ═══════ DRAFT POST MODAL ═══════ */}
      {draftModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm px-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.25 }}
            className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-lg max-h-[80vh] overflow-hidden flex flex-col"
          >
            {/* Header */}
            <div className="flex items-start justify-between p-6 pb-4 border-b border-slate-100">
              <div className="flex items-start gap-3">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 mt-0.5 ${
                  draftModal.context?.platform === "TikTok" ? "bg-slate-900" : "bg-gradient-to-br from-pink-500 to-purple-500"
                }`}>
                  {draftModal.context?.platform === "TikTok"
                    ? <Video className="w-5 h-5 text-white" />
                    : <Instagram className="w-5 h-5 text-white" />
                  }
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-900">{draftModal.title}</h3>
                  {draftModal.target_item && (
                    <p className="text-sm text-indigo-600 font-medium mt-0.5">{draftModal.target_item}</p>
                  )}
                </div>
              </div>
              <button
                onClick={() => { setDraftModal(null); setElaboration(null); }}
                className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Body */}
            <div className="p-6 overflow-y-auto flex-1">
              {elaborating ? (
                <div className="flex flex-col items-center justify-center py-10 gap-3">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
                  <p className="text-sm text-slate-400">AI is drafting your post...</p>
                </div>
              ) : elaboration ? (
                <div className="space-y-1">
                  {elaboration.split("\n").map((line, i) => {
                    const trimmed = line.trim();
                    if (!trimmed) return <div key={i} className="h-2" />;
                    const numberedMatch = trimmed.match(/^(\d+)[.)]\s+(.+)/);
                    if (numberedMatch) {
                      return (
                        <div key={i} className="flex items-start gap-2.5 my-1">
                          <span className="text-xs font-bold text-indigo-500 bg-indigo-50 w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                            {numberedMatch[1]}
                          </span>
                          <span className="text-sm text-slate-700 leading-relaxed">{renderInlineMarkdown(numberedMatch[2])}</span>
                        </div>
                      );
                    }
                    if (trimmed.startsWith("- ") || trimmed.startsWith("• ") || trimmed.startsWith("* ")) {
                      const content = trimmed.replace(/^[-•*]\s+/, "");
                      return (
                        <div key={i} className="flex items-start gap-2.5 my-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-[7px] shrink-0" />
                          <span className="text-sm text-slate-700 leading-relaxed">{renderInlineMarkdown(content)}</span>
                        </div>
                      );
                    }
                    return <p key={i} className="text-sm text-slate-700 leading-relaxed my-1.5">{renderInlineMarkdown(trimmed)}</p>;
                  })}
                </div>
              ) : null}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between p-4 border-t border-slate-100 bg-slate-50/50">
              <button
                onClick={() => { setDraftModal(null); setElaboration(null); }}
                className="text-sm font-medium text-slate-500 hover:text-slate-700 px-4 py-2 transition-colors"
              >
                Close
              </button>
              <button
                onClick={() => draftModal && handleDraftPost({
                  title: draftModal.title,
                  menuItem: draftModal.target_item ?? "",
                  platform: draftModal.context?.platform ?? "Instagram",
                  format: "Reel",
                  hook: "",
                  visual: "",
                  song: TRENDING_SONGS[0].name,
                  hashtags: TRENDING_HASHTAGS.slice(0, 3),
                  bestTime: "Friday Evening",
                  reason: "",
                })}
                disabled={elaborating}
                className="text-sm font-medium text-indigo-600 hover:text-indigo-700 disabled:text-indigo-300 px-3 py-2 transition-colors inline-flex items-center gap-1.5"
              >
                <Zap className="w-3.5 h-3.5" /> Regenerate
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
