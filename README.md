# Restaurant Growth Copilot

An AI-powered platform for local restaurants that helps scale revenue and reduce costs through evidence-based menu optimization, inventory management, and social media recommendations.

## Key Principle

The system does NOT hallucinate strategies. It uses:
- Analytics + rule-based strategy selection from a fixed playbook
- Strategy history and feedback memory to prevent repetition
- LLM only for explanation and report formatting

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create database
createdb restaurant_copilot

# Copy and edit environment variables
cp .env.example .env

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Seed Demo Data

```bash
# POST to the seed endpoint
curl -X POST http://localhost:8000/api/v1/uploads/seed-demo
```

This creates two demo restaurants with realistic data:
- **The Cozy Bean** (cafe) - 30 menu items, 11K+ sales, 25 ingredients
- **Stack House** (burger) - 25 menu items, 12K+ sales, 20 ingredients

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

### Run Tests

```bash
cd backend
pytest tests/ -v
```

## Architecture

```
User -> Next.js Dashboard -> FastAPI Backend -> PostgreSQL
                                    |
                          +---------+---------+
                          |         |         |
                     Analytics  Strategy   LLM
                      Engines    Engine   Explanation
                          |         |      (format only)
                     Menu/Inv/  Playbook +
                      Social    History
```

## Project Structure

```
backend/
  app/
    api/v1/         # FastAPI route handlers (thin)
    core/           # Config, database setup
    engines/        # Analytics, strategy, recommendation logic
    models/         # SQLAlchemy ORM models
    schemas/        # Pydantic request/response schemas
    services/       # CSV parser, seed service, chat service
  data/sample_csvs/ # Demo data for 2 restaurants
  tests/            # Integration tests

frontend/
  src/
    app/            # Next.js pages (dashboard, insights, etc.)
    components/     # Reusable UI components
    lib/            # API client
    types/          # TypeScript type definitions

docs/               # Strategy memory contract, architecture notes
```

## Strategy Categories (17 strategies)

| Category | Strategies |
|----------|-----------|
| Pricing | Price increase (high demand), Price decrease (low demand) |
| Bundling | Complementary items, Meal deals |
| Upsell | Premium variant suggestions |
| Menu | Remove underperformer, Simplify category |
| Inventory | Reorder alert, Bulk reorder discount |
| Waste | Reduce overstock, Reduce near-expiry waste |
| Social | Promote high-margin items, Promote trending, Optimize timing |
| Growth | Highlight margin items, Scale successful campaigns |
| Cost | Renegotiate supplier pricing |
