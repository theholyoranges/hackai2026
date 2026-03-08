export interface Restaurant {
  id: number;
  name: string;
  cuisine_type: string;
  location: string;
  created_at: string;
}

export interface MenuItem {
  id: number;
  restaurant_id: number;
  name: string;
  category: string;
  price: number;
  cost: number;
  units_sold: number;
  rating: number;
  profit_margin: number;
}

export interface MenuAnalytics {
  total_items: number;
  avg_profit_margin: number;
  top_performers: MenuItem[];
  underperformers: MenuItem[];
  category_breakdown: CategoryBreakdown[];
  pricing_insights: PricingInsight[];
}

export interface CategoryBreakdown {
  category: string;
  item_count: number;
  avg_price: number;
  avg_margin: number;
  total_revenue: number;
}

export interface PricingInsight {
  item_name: string;
  current_price: number;
  suggested_price: number;
  reason: string;
}

export interface InventoryItem {
  id: number;
  restaurant_id: number;
  item_name: string;
  category: string;
  current_stock: number;
  unit: string;
  cost_per_unit: number;
  reorder_point: number;
  shelf_life_days: number;
  last_restocked: string;
}

export interface InventoryAnalytics {
  total_items: number;
  total_value: number;
  low_stock_alerts: InventoryItem[];
  expiring_soon: InventoryItem[];
  waste_risk_items: InventoryItem[];
  category_summary: InventoryCategorySummary[];
}

export interface InventoryCategorySummary {
  category: string;
  item_count: number;
  total_value: number;
  avg_stock_level: number;
}

export interface SocialPost {
  id: number;
  restaurant_id: number;
  platform: string;
  content: string;
  post_date: string;
  likes: number;
  comments: number;
  shares: number;
  sentiment_score: number;
  engagement_rate: number;
}

export interface SocialAnalytics {
  total_posts: number;
  avg_engagement_rate: number;
  avg_sentiment: number;
  platform_breakdown: PlatformBreakdown[];
  top_posts: SocialPost[];
  sentiment_trend: SentimentTrend[];
}

export interface PlatformBreakdown {
  platform: string;
  post_count: number;
  avg_engagement: number;
  avg_sentiment: number;
}

export interface SentimentTrend {
  date: string;
  sentiment: number;
  engagement: number;
}

export interface DashboardSummary {
  restaurant: Restaurant;
  menu_summary: {
    total_items: number;
    avg_profit_margin: number;
    top_item: string;
  };
  inventory_summary: {
    total_items: number;
    low_stock_count: number;
    total_value: number;
  };
  social_summary: {
    total_posts: number;
    avg_engagement: number;
    avg_sentiment: number;
  };
  recent_recommendations: Recommendation[];
}

export interface Recommendation {
  id: number;
  restaurant_id: number;
  category: string;
  title: string;
  description: string;
  confidence: number;
  urgency: "low" | "medium" | "high" | "critical";
  expected_impact: string;
  evidence: string;
  status: "pending" | "accepted" | "rejected" | "implemented";
  created_at: string;
}

export interface StrategyHistory {
  id: number;
  restaurant_id: number;
  recommendation_id: number;
  title: string;
  description: string;
  category: string;
  status: "proposed" | "in_progress" | "completed" | "cancelled";
  outcome: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChatResponse {
  response: string;
  recommendations: Recommendation[];
  data_references: Record<string, unknown>;
}

export interface UploadResponse {
  message: string;
  rows_processed: number;
}
