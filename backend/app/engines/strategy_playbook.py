"""Strategy Playbook: master list of all reusable strategy templates.

Each strategy defines applicability rules, cooldown, confidence thresholds,
and expected KPI targets so the recommendation engine can match them
against live analytics.

Categories:
  - pricing            Dynamic pricing adjustments
  - bundling           Combos, meal deals, and cross-sell bundles
  - upsell             Premium upgrades and add-on suggestions
  - menu_engineering    Menu design, placement, and psychology
  - menu_simplification Remove or rework underperformers
  - cost_optimization   Ingredient cost reduction and supplier management
  - reorder             Stock replenishment and procurement
  - reduce_overstock    Draw down excess inventory
  - reduce_waste        Minimize spoilage and expiry losses
  - social_promote      Social media content and campaigns
  - social_timing       Post scheduling and engagement optimization
  - loyalty             Customer retention and repeat visit programs
  - day_part            Daypart-specific promotions and optimization
  - seasonal            Seasonal and event-driven strategies
  - operational         Kitchen efficiency and labour optimization
  - customer_experience Service quality and satisfaction boosters
  - delivery            Delivery and takeout channel optimization
  - local_marketing     Neighbourhood and community marketing
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.strategy import StrategyDefinition

# ---------------------------------------------------------------------------
# Playbook data
# ---------------------------------------------------------------------------

STRATEGY_PLAYBOOK: list[dict[str, Any]] = [
    # ══════════════════════════════════════════════════════════════════════
    #  PRICING
    # ══════════════════════════════════════════════════════════════════════
    {
        "code": "PRICE_INCREASE_HIGH_DEMAND",
        "name": "Increase price on high-demand items",
        "category": "pricing",
        "description": "Raise price 5-15% on items with consistently high popularity and strong demand elasticity. Target items where a modest price increase is unlikely to reduce order volume.",
        "applicability_rules": {"min_popularity_score": 0.7, "min_margin_pct": 0.3},
        "blocked_conditions": {"max_recent_price_changes": 2},
        "expected_evidence_fields": [
            "item_name", "current_price", "suggested_price", "popularity_score",
        ],
        "cooldown_days": 14,
        "confidence_threshold": 0.6,
        "expected_kpi_targets": {"revenue_increase_pct": 5},
    },
    {
        "code": "PRICE_DECREASE_LOW_DEMAND",
        "name": "Decrease price on low-demand items",
        "category": "pricing",
        "description": "Lower price 5-10% on underperforming items with healthy margins to stimulate demand and reduce waste from unsold ingredients.",
        "applicability_rules": {"max_popularity_score": 0.3, "min_margin_pct": 0.4},
        "blocked_conditions": {"max_recent_price_changes": 2},
        "expected_evidence_fields": [
            "item_name", "current_price", "suggested_price", "popularity_score",
        ],
        "cooldown_days": 14,
        "confidence_threshold": 0.55,
        "expected_kpi_targets": {"order_volume_increase_pct": 10},
    },
    {
        "code": "DYNAMIC_PEAK_PRICING",
        "name": "Introduce peak-hour pricing premium",
        "category": "pricing",
        "description": "Add a small premium (5-8%) on top-selling items during peak lunch/dinner hours when demand outstrips capacity. Helps manage rush and boost revenue per cover.",
        "applicability_rules": {"min_peak_hour_order_share": 0.4, "min_popularity_score": 0.6},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "item_name", "peak_hours", "current_price", "suggested_peak_price",
        ],
        "cooldown_days": 21,
        "confidence_threshold": 0.55,
        "expected_kpi_targets": {"revenue_increase_pct": 4, "avg_order_value_increase_pct": 3},
    },
    {
        "code": "ANCHOR_PRICE_STRATEGY",
        "name": "Add a premium anchor item to the menu",
        "category": "pricing",
        "description": "Place a high-priced specialty item at the top of a menu section to make other items look more reasonably priced by comparison. Classic menu psychology.",
        "applicability_rules": {"min_categories_available": 2},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "category", "current_highest_price", "suggested_anchor_item", "suggested_anchor_price",
        ],
        "cooldown_days": 60,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"avg_order_value_increase_pct": 6},
    },

    # ══════════════════════════════════════════════════════════════════════
    #  BUNDLING
    # ══════════════════════════════════════════════════════════════════════
    {
        "code": "BUNDLE_COMPLEMENTARY",
        "name": "Bundle complementary items together",
        "category": "bundling",
        "description": "Create a combo from items frequently purchased together at a small 10-15% discount. Increases average order value while giving customers a deal.",
        "applicability_rules": {"min_pair_frequency": 5, "min_pair_confidence": 0.3},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "item_a_name", "item_b_name", "pair_frequency", "suggested_bundle_price",
        ],
        "cooldown_days": 21,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"avg_order_value_increase_pct": 8},
    },
    {
        "code": "BUNDLE_MEAL_DEAL",
        "name": "Create meal deal bundle",
        "category": "bundling",
        "description": "Offer a starter + main + drink combo at a bundled price to increase AOV and simplify customer decision-making.",
        "applicability_rules": {"min_categories_available": 3},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "items", "individual_total", "bundle_price",
        ],
        "cooldown_days": 30,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"avg_order_value_increase_pct": 12},
    },
    {
        "code": "BUNDLE_FAMILY_PACK",
        "name": "Launch a family/sharing bundle",
        "category": "bundling",
        "description": "Create a family-sized sharing pack with 3-4 popular items at a 15-20% discount vs individual pricing. Targets groups and family dining occasions.",
        "applicability_rules": {"min_categories_available": 2, "min_avg_table_size": 2},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "items_included", "individual_total", "bundle_price", "target_group_size",
        ],
        "cooldown_days": 30,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"avg_order_value_increase_pct": 18, "order_volume_increase_pct": 5},
    },

    # ══════════════════════════════════════════════════════════════════════
    #  UPSELL
    # ══════════════════════════════════════════════════════════════════════
    {
        "code": "UPSELL_PREMIUM_VARIANT",
        "name": "Upsell to premium variant",
        "category": "upsell",
        "description": "Suggest a higher-margin premium version of popular items (e.g., larger portion, premium protein, truffle oil upgrade).",
        "applicability_rules": {"min_popularity_score": 0.6, "min_margin_gap": 0.15},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "base_item_name", "premium_item_name", "margin_difference",
        ],
        "cooldown_days": 14,
        "confidence_threshold": 0.55,
        "expected_kpi_targets": {"revenue_increase_pct": 6},
    },
    {
        "code": "UPSELL_ADD_ON_SUGGESTION",
        "name": "Suggest profitable add-ons at checkout",
        "category": "upsell",
        "description": "Train staff or configure POS to suggest high-margin add-ons (extra cheese, side salad, dessert) with popular mains. Small ticket increase per order adds up.",
        "applicability_rules": {"min_popularity_score": 0.5},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "main_item_name", "suggested_add_on", "add_on_price", "add_on_margin_pct",
        ],
        "cooldown_days": 14,
        "confidence_threshold": 0.55,
        "expected_kpi_targets": {"avg_order_value_increase_pct": 5, "revenue_increase_pct": 3},
    },
    {
        "code": "UPSELL_DRINK_PAIRING",
        "name": "Promote drink pairing with popular mains",
        "category": "upsell",
        "description": "Recommend beverage pairings (lassi, chai, soft drinks) with top-selling mains. Drinks carry 70-80% margins and are easy upsells.",
        "applicability_rules": {"min_popularity_score": 0.5, "has_beverage_category": True},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "main_item_name", "suggested_drink", "drink_margin_pct", "estimated_uptake_pct",
        ],
        "cooldown_days": 14,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"avg_order_value_increase_pct": 8, "beverage_sales_increase_pct": 15},
    },

    # ══════════════════════════════════════════════════════════════════════
    #  MENU ENGINEERING
    # ══════════════════════════════════════════════════════════════════════
    {
        "code": "HIGHLIGHT_MARGIN_ITEM",
        "name": "Highlight high-margin item on menu",
        "category": "menu_engineering",
        "description": "Add visual emphasis (badge, box, top placement, chef's pick label) to high-margin items on the menu that aren't getting enough attention.",
        "applicability_rules": {"min_margin_pct": 0.55, "max_popularity_score": 0.5},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "item_name", "margin_pct", "current_popularity_score",
        ],
        "cooldown_days": 21,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"revenue_increase_pct": 7},
    },
    {
        "code": "MENU_DESCRIPTION_REWRITE",
        "name": "Rewrite menu item descriptions for appeal",
        "category": "menu_engineering",
        "description": "Rewrite bland descriptions for high-margin items to make them sound irresistible. Use sensory language (sizzling, hand-crafted, slow-roasted) backed by menu psychology research.",
        "applicability_rules": {"min_margin_pct": 0.4, "max_popularity_score": 0.45},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "item_name", "current_description", "suggested_description", "margin_pct",
        ],
        "cooldown_days": 30,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"order_volume_increase_pct": 8},
    },
    {
        "code": "MENU_CATEGORY_REORDER",
        "name": "Reorder items within menu section",
        "category": "menu_engineering",
        "description": "Place high-margin items at the top and bottom of each menu section (primacy/recency effect). Items in these positions get 25% more attention.",
        "applicability_rules": {"min_category_items": 4},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "category", "current_order", "suggested_order", "high_margin_items",
        ],
        "cooldown_days": 30,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"revenue_increase_pct": 4},
    },
    {
        "code": "INTRODUCE_LIMITED_TIME_OFFER",
        "name": "Create a limited-time-only menu item",
        "category": "menu_engineering",
        "description": "Launch a special limited-time item using ingredients you already have in stock. Creates urgency and excitement, drives foot traffic, and can help draw down overstocked inventory.",
        "applicability_rules": {"min_categories_available": 1},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "suggested_item", "ingredients_available", "limited_period_days", "estimated_margin_pct",
        ],
        "cooldown_days": 21,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"revenue_increase_pct": 5, "foot_traffic_increase_pct": 8},
    },

    # ══════════════════════════════════════════════════════════════════════
    #  MENU SIMPLIFICATION
    # ══════════════════════════════════════════════════════════════════════
    {
        "code": "REMOVE_UNDERPERFORMER",
        "name": "Remove underperforming menu item",
        "category": "menu_simplification",
        "description": "Retire items with low sales AND low margin (dogs). Reduces kitchen complexity, cuts ingredient waste, and focuses staff attention on profitable items.",
        "applicability_rules": {"max_popularity_score": 0.15, "max_margin_pct": 0.25},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "item_name", "weekly_orders", "margin_pct",
        ],
        "cooldown_days": 30,
        "confidence_threshold": 0.65,
        "expected_kpi_targets": {"waste_reduction_pct": 10},
    },
    {
        "code": "SIMPLIFY_MENU_CATEGORY",
        "name": "Simplify an overcrowded menu category",
        "category": "menu_simplification",
        "description": "Reduce the number of items in a category that has too many low-performers. Paradox of choice: fewer options often leads to faster decisions and higher satisfaction.",
        "applicability_rules": {"min_category_items": 8, "max_avg_popularity": 0.35},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "category", "current_item_count", "suggested_removals",
        ],
        "cooldown_days": 30,
        "confidence_threshold": 0.6,
        "expected_kpi_targets": {"waste_reduction_pct": 8, "ops_efficiency_increase_pct": 5},
    },
    {
        "code": "REWORK_LOW_SELLER",
        "name": "Rework a low-selling item instead of removing it",
        "category": "menu_simplification",
        "description": "If a low-selling item has a unique ingredient profile or loyal niche following, consider reworking it (new name, better presentation, adjusted recipe) instead of cutting it entirely.",
        "applicability_rules": {"max_popularity_score": 0.2, "min_margin_pct": 0.35},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "item_name", "current_weekly_orders", "suggested_changes", "margin_pct",
        ],
        "cooldown_days": 30,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"order_volume_increase_pct": 15},
    },

    # ══════════════════════════════════════════════════════════════════════
    #  COST OPTIMIZATION
    # ══════════════════════════════════════════════════════════════════════
    {
        "code": "RENEGOTIATE_SUPPLIER",
        "name": "Renegotiate high-cost ingredient supplier",
        "category": "cost_optimization",
        "description": "Flag ingredients whose unit cost is high relative to revenue contribution. Request quotes from alternate suppliers or negotiate volume discounts with existing ones.",
        "applicability_rules": {"min_ingredient_cost_share": 0.15},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "ingredient_name", "current_unit_cost", "cost_share_pct",
        ],
        "cooldown_days": 60,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"cost_savings_pct": 5},
    },
    {
        "code": "PORTION_SIZE_OPTIMIZATION",
        "name": "Optimize portion sizes to reduce food cost",
        "category": "cost_optimization",
        "description": "Slightly reduce portion size on items where plate waste (uneaten food returned) is high. Saves ingredient cost without noticeably affecting customer satisfaction.",
        "applicability_rules": {"min_food_cost_pct": 0.35},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "item_name", "current_portion_g", "suggested_portion_g", "estimated_savings_per_order",
        ],
        "cooldown_days": 30,
        "confidence_threshold": 0.55,
        "expected_kpi_targets": {"cost_savings_pct": 4, "waste_reduction_pct": 10},
    },
    {
        "code": "SUBSTITUTE_CHEAPER_INGREDIENT",
        "name": "Substitute expensive ingredient with cheaper alternative",
        "category": "cost_optimization",
        "description": "Replace a costly ingredient with a similar but cheaper one in select dishes without compromising taste. Common swaps: regular cream for heavy cream, frozen for fresh herbs in cooked dishes.",
        "applicability_rules": {"min_ingredient_cost_share": 0.10},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "item_name", "current_ingredient", "suggested_substitute", "cost_savings_per_unit",
        ],
        "cooldown_days": 45,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"cost_savings_pct": 6},
    },

    # ══════════════════════════════════════════════════════════════════════
    #  REORDER / PROCUREMENT
    # ══════════════════════════════════════════════════════════════════════
    {
        "code": "REORDER_ALERT",
        "name": "Reorder ingredient approaching stockout",
        "category": "reorder",
        "description": "Trigger a reorder when inventory falls near or below the reorder threshold. Preventing stockouts avoids lost sales and disappointed customers.",
        "applicability_rules": {"max_days_of_stock": 3},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "ingredient_name", "quantity_on_hand", "reorder_threshold",
            "days_of_stock_remaining",
        ],
        "cooldown_days": 7,
        "confidence_threshold": 0.7,
        "expected_kpi_targets": {"stockout_risk_reduction_pct": 80},
    },
    {
        "code": "BULK_REORDER_DISCOUNT",
        "name": "Place bulk reorder to capture supplier discount",
        "category": "reorder",
        "description": "Order in larger quantities for high-turnover ingredients to lower unit cost. Ensure storage capacity and shelf life can support the larger order.",
        "applicability_rules": {"min_weekly_usage_units": 50, "min_margin_pct": 0.3},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "ingredient_name", "current_unit_cost", "estimated_bulk_unit_cost", "weekly_usage",
        ],
        "cooldown_days": 30,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"cost_savings_pct": 8},
    },
    {
        "code": "CONSOLIDATE_DELIVERY_DAYS",
        "name": "Consolidate supplier delivery schedule",
        "category": "reorder",
        "description": "Combine multiple small orders into fewer, larger deliveries to reduce delivery fees and receiving labour. Coordinate with suppliers for fixed delivery windows.",
        "applicability_rules": {"min_weekly_deliveries": 4},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "current_deliveries_per_week", "suggested_deliveries_per_week",
            "estimated_savings_per_week",
        ],
        "cooldown_days": 45,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"cost_savings_pct": 3, "ops_efficiency_increase_pct": 5},
    },

    # ══════════════════════════════════════════════════════════════════════
    #  REDUCE OVERSTOCK
    # ══════════════════════════════════════════════════════════════════════
    {
        "code": "REDUCE_OVERSTOCK",
        "name": "Reduce overstocked ingredient",
        "category": "reduce_overstock",
        "description": "Promote dishes that use an overstocked ingredient to draw down inventory before it expires. Use daily specials, social posts, or server recommendations.",
        "applicability_rules": {"min_overstock_ratio": 2.0},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "ingredient_name", "quantity_on_hand", "normal_weekly_usage",
            "suggested_items_to_promote",
        ],
        "cooldown_days": 14,
        "confidence_threshold": 0.55,
        "expected_kpi_targets": {"waste_reduction_pct": 15},
    },
    {
        "code": "OVERSTOCK_FLASH_SPECIAL",
        "name": "Run a flash special to move overstocked ingredients",
        "category": "reduce_overstock",
        "description": "Create a same-day or next-day special using overstocked items at a slight discount. Frame it as 'Chef's Special' rather than a clearance to maintain perceived value.",
        "applicability_rules": {"min_overstock_ratio": 1.5, "max_days_to_expiry": 10},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "ingredient_name", "quantity_on_hand", "suggested_special_item",
            "suggested_discount_pct",
        ],
        "cooldown_days": 7,
        "confidence_threshold": 0.6,
        "expected_kpi_targets": {"waste_reduction_pct": 25, "revenue_increase_pct": 2},
    },

    # ══════════════════════════════════════════════════════════════════════
    #  REDUCE WASTE
    # ══════════════════════════════════════════════════════════════════════
    {
        "code": "REDUCE_WASTE",
        "name": "Reduce waste from near-expiry ingredients",
        "category": "reduce_waste",
        "description": "Push specials or discounts using ingredients nearing their expiry date. Act immediately — every day of delay reduces the chance of recovery.",
        "applicability_rules": {"max_days_to_expiry": 5},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "ingredient_name", "expiry_date", "quantity_on_hand", "suggested_special",
        ],
        "cooldown_days": 7,
        "confidence_threshold": 0.7,
        "expected_kpi_targets": {"waste_reduction_pct": 20},
    },
    {
        "code": "PREP_BATCH_FREEZE",
        "name": "Batch-prep and freeze surplus ingredients",
        "category": "reduce_waste",
        "description": "When ingredients are nearing expiry but can be frozen (marinades, sauces, pre-portioned proteins), batch-prep them now to extend useful life by weeks.",
        "applicability_rules": {"max_days_to_expiry": 3, "ingredient_freezable": True},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "ingredient_name", "quantity_on_hand", "prep_suggestion", "extended_shelf_days",
        ],
        "cooldown_days": 7,
        "confidence_threshold": 0.65,
        "expected_kpi_targets": {"waste_reduction_pct": 30},
    },
    {
        "code": "FIRST_IN_FIRST_OUT_REMINDER",
        "name": "Enforce FIFO stock rotation",
        "category": "reduce_waste",
        "description": "Remind kitchen staff to use older inventory first. This is especially critical for items with multiple delivery batches that may get mixed up on shelves.",
        "applicability_rules": {"has_multiple_batches": True},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "ingredient_name", "oldest_batch_date", "newest_batch_date",
        ],
        "cooldown_days": 14,
        "confidence_threshold": 0.6,
        "expected_kpi_targets": {"waste_reduction_pct": 12},
    },

    # ══════════════════════════════════════════════════════════════════════
    #  SOCIAL MEDIA PROMOTION
    # ══════════════════════════════════════════════════════════════════════
    {
        "code": "PROMOTE_HIGH_MARGIN_SOCIAL",
        "name": "Promote high-margin item on social media",
        "category": "social_promote",
        "description": "Create a social post featuring a high-margin item that lacks recent promotion. Use appealing food photography and a clear call-to-action.",
        "applicability_rules": {"min_margin_pct": 0.5, "max_recent_posts": 1},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "item_name", "margin_pct", "last_promoted_days_ago",
        ],
        "cooldown_days": 14,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"social_engagement_increase_pct": 15},
    },
    {
        "code": "PROMOTE_TRENDING_SOCIAL",
        "name": "Promote trending item on social media",
        "category": "social_promote",
        "description": "Amplify a menu item whose sales are trending upward with a social push. Ride the momentum to accelerate growth.",
        "applicability_rules": {"min_sales_trend_slope": 0.1, "min_popularity_score": 0.5},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "item_name", "sales_trend_slope", "current_weekly_orders",
        ],
        "cooldown_days": 14,
        "confidence_threshold": 0.55,
        "expected_kpi_targets": {"social_engagement_increase_pct": 20, "revenue_increase_pct": 5},
    },
    {
        "code": "USER_GENERATED_CONTENT_CAMPAIGN",
        "name": "Launch a user-generated content campaign",
        "category": "social_promote",
        "description": "Encourage customers to share photos of their meals with a branded hashtag. Offer a small incentive (10% off next visit). UGC is 3x more trusted than brand-created content.",
        "applicability_rules": {"min_post_count": 5},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "suggested_hashtag", "incentive_offer", "target_platform",
        ],
        "cooldown_days": 30,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"social_engagement_increase_pct": 30, "foot_traffic_increase_pct": 5},
    },
    {
        "code": "BEHIND_THE_SCENES_CONTENT",
        "name": "Post behind-the-scenes kitchen content",
        "category": "social_promote",
        "description": "Share authentic kitchen prep footage, chef stories, or ingredient sourcing journeys. BTS content humanizes the brand and builds trust — consistently outperforms polished ads.",
        "applicability_rules": {"min_post_count": 3},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "suggested_content_type", "featured_dish_or_ingredient", "target_platform",
        ],
        "cooldown_days": 14,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"social_engagement_increase_pct": 25},
    },
    {
        "code": "SOCIAL_CONTEST_GIVEAWAY",
        "name": "Run a social media contest or giveaway",
        "category": "social_promote",
        "description": "Run a 'tag a friend + follow' giveaway for a free meal or dessert. Low cost per acquisition and great for follower growth. Time it around a quiet business period.",
        "applicability_rules": {},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "prize_description", "prize_cost", "contest_duration_days", "target_platform",
        ],
        "cooldown_days": 45,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"social_follower_increase_pct": 10, "foot_traffic_increase_pct": 5},
    },

    # ══════════════════════════════════════════════════════════════════════
    #  SOCIAL TIMING
    # ══════════════════════════════════════════════════════════════════════
    {
        "code": "OPTIMIZE_POST_TIMING",
        "name": "Optimize social media post timing",
        "category": "social_timing",
        "description": "Schedule posts at times that historically receive the highest engagement for your audience. Posting at the right time can double reach without extra spend.",
        "applicability_rules": {"min_post_count": 10},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "best_day", "best_hour", "avg_engagement_at_best_time", "avg_engagement_overall",
        ],
        "cooldown_days": 30,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"social_engagement_increase_pct": 25},
    },
    {
        "code": "POST_FREQUENCY_INCREASE",
        "name": "Increase social media posting frequency",
        "category": "social_timing",
        "description": "If posting less than 4x per week, increase to daily. Restaurants that post daily see 40% more engagement on average. Use a mix of food shots, stories, and BTS content.",
        "applicability_rules": {"max_weekly_posts": 3},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "current_weekly_posts", "suggested_weekly_posts", "content_plan_outline",
        ],
        "cooldown_days": 30,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"social_engagement_increase_pct": 40, "foot_traffic_increase_pct": 5},
    },

    # ══════════════════════════════════════════════════════════════════════
    #  LOYALTY & RETENTION
    # ══════════════════════════════════════════════════════════════════════
    {
        "code": "LAUNCH_LOYALTY_PROGRAM",
        "name": "Launch a simple loyalty/rewards program",
        "category": "loyalty",
        "description": "Implement a stamp card or digital points program (every 10th meal free, or earn points per dollar). Repeat customers spend 67% more than new ones.",
        "applicability_rules": {},
        "blocked_conditions": {"has_active_loyalty_program": True},
        "expected_evidence_fields": [
            "program_type", "reward_structure", "estimated_repeat_rate_increase",
        ],
        "cooldown_days": 90,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"repeat_visit_increase_pct": 20, "revenue_increase_pct": 8},
    },
    {
        "code": "WIN_BACK_LAPSED_CUSTOMERS",
        "name": "Win-back campaign for lapsed customers",
        "category": "loyalty",
        "description": "Send a special offer or personal message to customers who haven't visited in 30+ days. A 'We miss you' with 15% off brings back 10-15% of lapsed diners.",
        "applicability_rules": {"min_customer_count": 50},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "lapsed_customer_count", "suggested_offer", "channel",
        ],
        "cooldown_days": 30,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"repeat_visit_increase_pct": 12, "revenue_increase_pct": 3},
    },
    {
        "code": "VIP_TABLE_RESERVATION",
        "name": "Offer VIP perks for frequent diners",
        "category": "loyalty",
        "description": "Identify top 10% of customers by spend and offer them priority reservations, a free appetizer, or a complimentary drink. Makes them feel valued and cements loyalty.",
        "applicability_rules": {"min_customer_count": 30},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "vip_customer_count", "suggested_perks", "estimated_cost",
        ],
        "cooldown_days": 60,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"repeat_visit_increase_pct": 15, "avg_order_value_increase_pct": 10},
    },

    # ══════════════════════════════════════════════════════════════════════
    #  DAY-PART OPTIMIZATION
    # ══════════════════════════════════════════════════════════════════════
    {
        "code": "SLOW_PERIOD_HAPPY_HOUR",
        "name": "Introduce happy hour or off-peak special",
        "category": "day_part",
        "description": "Offer discounted appetizers or drinks during slow afternoon hours (2-5 PM) to fill empty seats. Even at lower margins, incremental revenue from unused capacity is pure profit.",
        "applicability_rules": {"min_slow_period_hours": 2},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "slow_period_start", "slow_period_end", "suggested_offers", "estimated_foot_traffic_increase",
        ],
        "cooldown_days": 30,
        "confidence_threshold": 0.55,
        "expected_kpi_targets": {"revenue_increase_pct": 6, "foot_traffic_increase_pct": 15},
    },
    {
        "code": "LUNCH_EXPRESS_MENU",
        "name": "Launch a quick-serve lunch express menu",
        "category": "day_part",
        "description": "Offer a streamlined 5-item menu with guaranteed fast service during lunch hours for office workers. Faster turnover = more covers per hour.",
        "applicability_rules": {"min_lunch_orders": 20},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "suggested_items", "target_service_time_minutes", "estimated_covers_increase",
        ],
        "cooldown_days": 45,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"revenue_increase_pct": 8, "table_turnover_increase_pct": 20},
    },
    {
        "code": "EARLY_BIRD_DINNER_DEAL",
        "name": "Early bird dinner discount",
        "category": "day_part",
        "description": "Offer 10-15% off for diners who arrive before 6 PM. Fills the pre-rush gap, spreads demand, and reduces kitchen stress during peak dinner service.",
        "applicability_rules": {},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "discount_pct", "qualifying_hours", "estimated_incremental_covers",
        ],
        "cooldown_days": 30,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"revenue_increase_pct": 4, "foot_traffic_increase_pct": 10},
    },

    # ══════════════════════════════════════════════════════════════════════
    #  SEASONAL & EVENT-DRIVEN
    # ══════════════════════════════════════════════════════════════════════
    {
        "code": "SEASONAL_MENU_ITEM",
        "name": "Launch a seasonal special menu item",
        "category": "seasonal",
        "description": "Introduce a dish tied to the current season or upcoming holiday (pumpkin soup in fall, mango desserts in summer). Creates urgency and repeat visits.",
        "applicability_rules": {},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "season_or_event", "suggested_item", "available_ingredients", "estimated_margin_pct",
        ],
        "cooldown_days": 60,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"revenue_increase_pct": 5, "foot_traffic_increase_pct": 8},
    },
    {
        "code": "EVENT_DAY_PROMOTION",
        "name": "Run a promotion tied to local event or holiday",
        "category": "seasonal",
        "description": "Tie a special offer to an upcoming event (Valentine's prix fixe, game day wings deal, festival thali). Event-anchored promotions create natural urgency.",
        "applicability_rules": {},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "event_name", "event_date", "suggested_offer", "estimated_incremental_revenue",
        ],
        "cooldown_days": 14,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"revenue_increase_pct": 8, "foot_traffic_increase_pct": 15},
    },

    # ══════════════════════════════════════════════════════════════════════
    #  OPERATIONAL EFFICIENCY
    # ══════════════════════════════════════════════════════════════════════
    {
        "code": "STREAMLINE_PREP_WORKFLOW",
        "name": "Streamline kitchen prep for top-selling items",
        "category": "operational",
        "description": "Pre-prep high-volume items (mise en place, batch sauces, pre-portioned proteins) during off-peak hours to speed up service during rush. Reduces ticket times by 20-30%.",
        "applicability_rules": {"min_popularity_score": 0.6},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "item_name", "current_avg_prep_minutes", "suggested_prep_changes",
        ],
        "cooldown_days": 30,
        "confidence_threshold": 0.55,
        "expected_kpi_targets": {"ops_efficiency_increase_pct": 15, "table_turnover_increase_pct": 10},
    },
    {
        "code": "CROSS_UTILIZE_INGREDIENTS",
        "name": "Cross-utilize ingredients across multiple dishes",
        "category": "operational",
        "description": "Identify ingredients used in only one dish and find ways to incorporate them into other items. Reduces unique SKUs, simplifies ordering, and cuts waste from single-use ingredients.",
        "applicability_rules": {"min_single_use_ingredients": 3},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "ingredient_name", "current_dishes", "suggested_additional_dishes", "estimated_waste_reduction",
        ],
        "cooldown_days": 45,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"waste_reduction_pct": 12, "cost_savings_pct": 3},
    },

    # ══════════════════════════════════════════════════════════════════════
    #  CUSTOMER EXPERIENCE
    # ══════════════════════════════════════════════════════════════════════
    {
        "code": "TABLE_TOUCH_PROGRAM",
        "name": "Implement manager table-touch program",
        "category": "customer_experience",
        "description": "Have the owner or manager visit every table during service to check on satisfaction. Personal attention creates memorable experiences and drives word-of-mouth.",
        "applicability_rules": {},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "current_practice", "suggested_frequency", "talking_points",
        ],
        "cooldown_days": 60,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"repeat_visit_increase_pct": 10, "review_score_increase": 0.2},
    },
    {
        "code": "REQUEST_REVIEWS",
        "name": "Actively request online reviews from happy diners",
        "category": "customer_experience",
        "description": "Train staff to ask satisfied customers to leave a Google/Yelp review. Provide a QR code on the receipt or table tent. Restaurants with 50+ reviews get 35% more clicks.",
        "applicability_rules": {},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "current_review_count", "target_review_count", "review_platform", "suggested_method",
        ],
        "cooldown_days": 30,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"review_count_increase_pct": 30, "foot_traffic_increase_pct": 5},
    },
    {
        "code": "COMPLIMENTARY_SURPRISE",
        "name": "Offer a complimentary surprise to delight customers",
        "category": "customer_experience",
        "description": "Surprise select tables with a free small appetizer, dessert bite, or drink. Costs pennies but creates massive goodwill, social shares, and return visits.",
        "applicability_rules": {},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "suggested_item", "cost_per_unit", "frequency_per_shift",
        ],
        "cooldown_days": 30,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"repeat_visit_increase_pct": 8, "social_engagement_increase_pct": 15},
    },

    # ══════════════════════════════════════════════════════════════════════
    #  DELIVERY & TAKEOUT
    # ══════════════════════════════════════════════════════════════════════
    {
        "code": "OPTIMIZE_DELIVERY_MENU",
        "name": "Create a delivery-optimized menu",
        "category": "delivery",
        "description": "Curate a shorter menu of items that travel well (avoid soups that spill, fried items that get soggy). Better delivery food quality = better ratings = more orders.",
        "applicability_rules": {"has_delivery_channel": True},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "items_to_include", "items_to_exclude", "estimated_delivery_rating_increase",
        ],
        "cooldown_days": 45,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"delivery_order_increase_pct": 12, "delivery_rating_increase": 0.3},
    },
    {
        "code": "DELIVERY_EXCLUSIVE_ITEM",
        "name": "Create a delivery-exclusive menu item",
        "category": "delivery",
        "description": "Offer a special item available only for delivery orders. Creates a reason to order online and can utilize ingredients that are overstocked.",
        "applicability_rules": {"has_delivery_channel": True},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "suggested_item", "estimated_margin_pct", "delivery_platform",
        ],
        "cooldown_days": 30,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"delivery_order_increase_pct": 8, "revenue_increase_pct": 3},
    },

    # ══════════════════════════════════════════════════════════════════════
    #  LOCAL MARKETING
    # ══════════════════════════════════════════════════════════════════════
    {
        "code": "LOCAL_BUSINESS_PARTNERSHIP",
        "name": "Partner with nearby businesses for cross-promotion",
        "category": "local_marketing",
        "description": "Partner with local offices, gyms, or shops to offer mutual discounts. 'Show your gym membership for 10% off' drives new foot traffic at zero ad spend.",
        "applicability_rules": {},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "partner_business_type", "suggested_offer", "estimated_new_customers_per_month",
        ],
        "cooldown_days": 60,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"foot_traffic_increase_pct": 10, "revenue_increase_pct": 4},
    },
    {
        "code": "GOOGLE_BUSINESS_OPTIMIZATION",
        "name": "Optimize Google Business Profile",
        "category": "local_marketing",
        "description": "Update Google Business with current hours, photos, menu, and respond to all reviews. An optimized profile gets 70% more visits and 50% more calls than a neglected one.",
        "applicability_rules": {},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "current_profile_completeness", "missing_sections", "action_items",
        ],
        "cooldown_days": 90,
        "confidence_threshold": 0.5,
        "expected_kpi_targets": {"foot_traffic_increase_pct": 12, "online_visibility_increase_pct": 30},
    },

    # ══════════════════════════════════════════════════════════════════════
    #  SCALE CAMPAIGN
    # ══════════════════════════════════════════════════════════════════════
    {
        "code": "SCALE_SUCCESSFUL_CAMPAIGN",
        "name": "Scale a successful past strategy",
        "category": "scale_campaign",
        "description": "Re-apply or expand a strategy that previously delivered strong results. Double down on what works.",
        "applicability_rules": {"min_past_success_count": 1},
        "blocked_conditions": {},
        "expected_evidence_fields": [
            "original_strategy_code", "past_impact", "suggested_expansion",
        ],
        "cooldown_days": 30,
        "confidence_threshold": 0.6,
        "expected_kpi_targets": {"revenue_increase_pct": 10},
    },
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def get_playbook() -> list[dict[str, Any]]:
    """Return the full strategy playbook."""
    return STRATEGY_PLAYBOOK


def get_strategy_by_code(code: str) -> dict[str, Any] | None:
    """Look up a single strategy dict by its unique code."""
    for strategy in STRATEGY_PLAYBOOK:
        if strategy["code"] == code:
            return strategy
    return None


def get_strategies_by_category(category: str) -> list[dict[str, Any]]:
    """Return all strategies in a given category."""
    return [s for s in STRATEGY_PLAYBOOK if s["category"] == category]


def get_all_categories() -> list[str]:
    """Return sorted list of unique strategy categories."""
    return sorted({s["category"] for s in STRATEGY_PLAYBOOK})


def seed_strategies(db: Session) -> list[StrategyDefinition]:
    """Insert all playbook strategies into the StrategyDefinition table.

    Strategies that already exist (matched by ``code``) are skipped so the
    function is safe to call repeatedly (idempotent).

    Returns the list of StrategyDefinition rows that were newly created.
    """
    existing_codes: set[str] = {
        row[0]
        for row in db.query(StrategyDefinition.code).all()
    }

    created: list[StrategyDefinition] = []

    for entry in STRATEGY_PLAYBOOK:
        if entry["code"] in existing_codes:
            continue

        sd = StrategyDefinition(
            code=entry["code"],
            name=entry["name"],
            category=entry.get("category"),
            description=entry.get("description"),
            applicability_rules=entry.get("applicability_rules"),
            blocked_conditions=entry.get("blocked_conditions"),
            expected_evidence_fields=entry.get("expected_evidence_fields"),
            cooldown_days=entry.get("cooldown_days", 14),
            confidence_threshold=entry.get("confidence_threshold", 0.5),
            expected_kpi_targets=entry.get("expected_kpi_targets"),
            is_active=True,
        )
        db.add(sd)
        created.append(sd)

    if created:
        db.commit()
        for sd in created:
            db.refresh(sd)

    return created
