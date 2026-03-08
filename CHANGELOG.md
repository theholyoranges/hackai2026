# Changelog

All notable changes to the Restaurant Growth Copilot are documented here.

## [1.0.0] - 2026-03-07

### Added

#### Backend - Core Infrastructure
- FastAPI application with versioned API (v1) and health endpoint
- PostgreSQL database configuration with SQLAlchemy 2.0 ORM
- Pydantic v2 schemas for all request/response models
- CORS middleware for frontend communication
- Environment variable configuration via pydantic-settings

#### Backend - Data Models (9 entities)
- Restaurant: profile info, cuisine type, location
- MenuItem: price, ingredient cost, category, active status
- SalesRecord: quantity, total price, order ID for basket analysis, time dimensions
- InventoryItem: quantity on hand, reorder threshold, expiry date, supplier
- RecipeMapping: links menu items to ingredients with quantities
- SocialPost: platform, post type, engagement metrics (likes, comments, shares, reach)
- StrategyDefinition: fixed playbook entries with applicability rules, cooldown, confidence thresholds
- StrategyHistory: full lifecycle tracking (suggested -> accepted -> active -> evaluating -> successful/failed -> archived)
- Recommendation: evidence-based recommendations with confidence, urgency, blocked reasons

#### Backend - CSV Ingestion Pipeline
- Upload endpoints for menu, sales, inventory, recipe mapping, and social post CSVs
- Column validation, name normalization, and error reporting
- Ingestion summary with rows processed/failed/errors
- One-click demo seed endpoint (/api/v1/uploads/seed-demo)

#### Backend - Analytics Engines
- **Menu Analytics**: top/bottom sellers, revenue by item, margin analysis, menu engineering (Star/Puzzle/Plow Horse/Dog), pair analysis via order co-occurrence, demand trends by day/hour, category performance
- **Inventory Analytics**: ingredient usage from recipe mapping + sales, projected days of stock, reorder/stockout/overstock/expiry alerts, waste-prone ingredient detection
- **Social Analytics**: engagement by post type, best posting times, trending items, campaign opportunity detection

#### Backend - Strategy System (Non-Hallucinating)
- Fixed strategy playbook with 17 strategies across 13 categories (pricing, bundling, upsell, menu simplification, cost optimization, reorder, reduce overstock, reduce waste, social promote, social timing, highlight margin, scale campaign, remove underperformer)
- Strategy history engine with full lifecycle management, cooldown logic, duplicate blocking
- Rule-based recommendation selector: matches analytics to playbook strategies, filters blocked, scores by impact * confidence * novelty
- Simulation helpers: price change estimation, bundle scoring, reorder impact, social timing scoring
- LLM explanation layer: generates owner-friendly explanations from structured data (with non-LLM fallback)

#### Backend - Chat Assistant
- Grounded AI chat that uses analytics + strategy history as context
- Refuses to invent unsupported recommendations
- Cites structured evidence from backend

#### Backend - Demo Data
- Realistic sample CSVs for two restaurants:
  - The Cozy Bean (cafe): 30 menu items, 11,000+ sales records over 90 days, 25 ingredients, 60 recipe mappings, 45 social posts
  - Stack House (burger): 25 menu items, 12,000+ sales records, 20 ingredients, 50 recipe mappings, 40 social posts
- Data includes: high/low margin items, popular/unpopular items, co-purchase patterns, inventory waste scenarios, social engagement patterns

#### Frontend - Next.js Dashboard
- Responsive sidebar navigation with restaurant selector
- **Dashboard**: revenue trend chart, top/bottom items, margin opportunities, waste/stockout alerts, top 3 recommendations, "Generate Growth Plan" button
- **Menu Insights**: revenue by item bar chart, menu engineering matrix (Star/Puzzle/Plow Horse/Dog), pair analysis table, category performance, demand heatmap
- **Inventory Insights**: stockout risk alerts, expiry alerts, projected days left table with color coding, daily usage chart, waste-prone items
- **Social Insights**: engagement by post type, best posting times, trending items, campaign opportunities
- **Recommendations**: ranked cards with confidence/urgency/impact, evidence panel, accept/reject buttons, blocked recommendations with reasons
- **Strategy History**: timeline with filter tabs (All/Active/Successful/Failed/Archived), color-coded status badges, outcome metrics
- **Upload**: CSV upload forms for all 5 data types, seed demo button, expected format hints
- **Chat**: conversation interface with suggested questions, grounded AI responses

#### Frontend - Reusable Components
- StatCard, RecommendationCard, AlertCard
- SimpleBarChart, SimpleLineChart, SimplePieChart (Recharts wrappers)
- Sidebar with active page highlighting

#### Testing
- Integration test suite covering: CSV ingestion, analytics generation, strategy playbook matching, strategy history filtering, blocked strategy enforcement, recommendation lifecycle, failed strategy non-repetition

#### Documentation
- Strategy memory contract (docs/strategy_memory_contract.md)
- Architecture notes in HACKAI.md
- This changelog

### Architecture Decisions
- **LLM only for explanation**: All strategy selection is deterministic and evidence-based. The LLM layer formats human-readable text but cannot invent strategies or metrics.
- **Fixed strategy playbook**: No free-form strategy generation. All recommendations come from a predefined library of 17 strategies.
- **Strategy history with cooldown**: Prevents recommending recently failed strategies and avoids repetition of active strategies.
- **Separated analytics and recommendations**: Analytics engines compute facts only. Recommendation engine matches facts to strategies.
