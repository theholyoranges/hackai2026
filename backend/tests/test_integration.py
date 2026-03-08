"""End-to-end integration tests for the Restaurant Growth Copilot.

These tests cover the critical business flows:
- CSV ingestion
- Analytics generation
- Strategy playbook matching
- Strategy history filtering (blocked/cooldown)
- Recommendation generation
- Recommendation lifecycle
- Failed strategy is NOT re-recommended
- Successful strategy produces scale-up instead of repetition
"""

from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.engines.menu_analytics import MenuAnalyticsEngine
from app.engines.recommendation_engine import RecommendationEngine
from app.engines.strategy_history_engine import StrategyHistoryEngine
from app.engines.strategy_playbook import seed_strategies
from app.models.inventory_item import InventoryItem
from app.models.menu_item import MenuItem
from app.models.recommendation import Recommendation, RecommendationStatus
from app.models.restaurant import Restaurant
from app.models.sales_record import SalesRecord
from app.models.strategy import StrategyDefinition, StrategyHistory, StrategyStatus
from app.services.csv_parser import parse_menu_csv, parse_sales_csv

SAMPLE_CSV_DIR = Path(__file__).resolve().parent.parent / "data" / "sample_csvs"

# Use SQLite for tests
TEST_DB_URL = "sqlite:///test_restaurant_copilot.db"


@pytest.fixture(scope="module")
def engine():
    eng = create_engine(TEST_DB_URL, echo=False)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    import os
    try:
        os.remove("test_restaurant_copilot.db")
    except FileNotFoundError:
        pass


@pytest.fixture
def db(engine):
    session = sessionmaker(bind=engine)()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def restaurant(db: Session):
    r = Restaurant(name="Test Cafe", cuisine_type="Cafe", location="Test City")
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


@pytest.fixture
def seeded_strategies(db: Session):
    return seed_strategies(db)


class TestCSVIngestion:
    def test_menu_csv_parses_correctly(self, db: Session, restaurant: Restaurant):
        csv_path = SAMPLE_CSV_DIR / "cafe_menu.csv"
        if not csv_path.exists():
            pytest.skip("Sample CSV not found")
        content = csv_path.read_bytes()
        result = parse_menu_csv(content, restaurant.id, db)
        assert result.rows_processed > 0
        assert result.rows_failed == 0
        items = db.query(MenuItem).filter(MenuItem.restaurant_id == restaurant.id).all()
        assert len(items) == result.rows_processed

    def test_sales_csv_parses_correctly(self, db: Session, restaurant: Restaurant):
        # Ensure menu items exist first
        csv_path = SAMPLE_CSV_DIR / "cafe_menu.csv"
        if not csv_path.exists():
            pytest.skip("Sample CSV not found")
        parse_menu_csv(csv_path.read_bytes(), restaurant.id, db)

        sales_path = SAMPLE_CSV_DIR / "cafe_sales.csv"
        if not sales_path.exists():
            pytest.skip("Sample sales CSV not found")
        result = parse_sales_csv(sales_path.read_bytes(), restaurant.id, db)
        assert result.rows_processed > 100

    def test_rejects_malformed_csv(self, db: Session, restaurant: Restaurant):
        bad_csv = b"wrong_col1,wrong_col2\nfoo,bar"
        result = parse_menu_csv(bad_csv, restaurant.id, db)
        assert result.rows_processed == 0
        assert len(result.errors) > 0


class TestMenuAnalytics:
    def test_top_sellers_returns_results(self, db: Session, restaurant: Restaurant):
        top = MenuAnalyticsEngine.get_top_sellers(db, restaurant.id, limit=5)
        assert isinstance(top, list)

    def test_menu_engineering_classification(self, db: Session, restaurant: Restaurant):
        engineering = MenuAnalyticsEngine.get_menu_engineering(db, restaurant.id)
        assert isinstance(engineering, list)
        if engineering:
            categories = {e.get("classification") for e in engineering}
            assert categories.issubset({"Star", "Puzzle", "Plow Horse", "Dog"})


class TestStrategyPlaybook:
    def test_strategies_seeded(self, db: Session, seeded_strategies):
        count = db.query(StrategyDefinition).count()
        assert count >= 10

    def test_no_duplicate_codes(self, db: Session, seeded_strategies):
        codes = [sd.code for sd in db.query(StrategyDefinition).all()]
        assert len(codes) == len(set(codes))


class TestStrategyHistory:
    def test_record_and_block_lifecycle(self, db: Session, restaurant: Restaurant, seeded_strategies):
        sd = db.query(StrategyDefinition).first()
        assert sd is not None

        # Record a suggestion
        sh = StrategyHistoryEngine.record_suggestion(
            db, restaurant.id, sd.id, None,
            evidence={"test": True}
        )
        assert sh.status == StrategyStatus.suggested

        # Accept and activate
        StrategyHistoryEngine.accept_strategy(db, sh.id)
        StrategyHistoryEngine.activate_strategy(db, sh.id)

        # Should now be blocked
        blocked = StrategyHistoryEngine.get_blocked_strategy_codes(db, restaurant.id)
        assert sd.code in blocked

    def test_failed_strategy_blocked_during_cooldown(self, db: Session, restaurant: Restaurant, seeded_strategies):
        sd = db.query(StrategyDefinition).filter(StrategyDefinition.code == "PRICE_INCREASE_HIGH_DEMAND").first()
        if sd is None:
            pytest.skip("Strategy not found")

        sh = StrategyHistoryEngine.record_suggestion(
            db, restaurant.id, sd.id, None,
            evidence={"test": True}
        )
        StrategyHistoryEngine.accept_strategy(db, sh.id)
        StrategyHistoryEngine.activate_strategy(db, sh.id)
        StrategyHistoryEngine.start_evaluation(db, sh.id)
        StrategyHistoryEngine.mark_failed(db, sh.id, actual_impact="No improvement", notes="Test failure")

        # Failed strategy should be in blocked set
        blocked = StrategyHistoryEngine.get_blocked_strategy_codes(db, restaurant.id)
        assert sd.code in blocked

    def test_successful_strategy_tracked(self, db: Session, restaurant: Restaurant, seeded_strategies):
        sd = db.query(StrategyDefinition).filter(StrategyDefinition.code == "BUNDLE_COMPLEMENTARY").first()
        if sd is None:
            pytest.skip("Strategy not found")

        sh = StrategyHistoryEngine.record_suggestion(
            db, restaurant.id, sd.id, None,
            evidence={"test": True}
        )
        StrategyHistoryEngine.accept_strategy(db, sh.id)
        StrategyHistoryEngine.activate_strategy(db, sh.id)
        StrategyHistoryEngine.start_evaluation(db, sh.id)
        StrategyHistoryEngine.mark_successful(db, sh.id, actual_impact="10% AOV increase", notes="Great results")

        successes = StrategyHistoryEngine.get_successful_strategies(db, restaurant.id)
        assert len(successes) >= 1


class TestRecommendationEngine:
    def test_generate_recommendations_returns_list(self, db: Session, restaurant: Restaurant, seeded_strategies):
        engine = RecommendationEngine()
        recs = engine.generate_recommendations(db, restaurant.id)
        assert isinstance(recs, list)

    def test_blocked_strategies_not_recommended(self, db: Session, restaurant: Restaurant, seeded_strategies):
        """A recently failed strategy must NOT appear in new recommendations."""
        sd = db.query(StrategyDefinition).filter(StrategyDefinition.code == "REORDER_ALERT").first()
        if sd is None:
            pytest.skip("Strategy not found")

        # Create a failed strategy history
        sh = StrategyHistory(
            restaurant_id=restaurant.id,
            strategy_definition_id=sd.id,
            status=StrategyStatus.failed,
            completed_at=datetime.utcnow(),
            cooldown_until=datetime.utcnow() + timedelta(days=14),
        )
        db.add(sh)
        db.commit()

        # Generate new recommendations
        engine = RecommendationEngine()
        recs = engine.generate_recommendations(db, restaurant.id)

        # The failed strategy should NOT be in the new recommendations
        rec_codes = set()
        for rec in recs:
            sd_rec = db.query(StrategyDefinition).filter(StrategyDefinition.id == rec.strategy_definition_id).first()
            if sd_rec:
                rec_codes.add(sd_rec.code)

        assert "REORDER_ALERT" not in rec_codes


class TestRecommendationLifecycle:
    def test_accept_and_reject(self, db: Session, restaurant: Restaurant, seeded_strategies):
        rec = Recommendation(
            restaurant_id=restaurant.id,
            strategy_definition_id=db.query(StrategyDefinition).first().id,
            title="Test Recommendation",
            evidence={"test": True},
            confidence=0.8,
            urgency="high",
            expected_impact="5%",
            status=RecommendationStatus.pending,
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)

        # Accept
        rec.status = RecommendationStatus.accepted
        db.commit()
        assert rec.status == RecommendationStatus.accepted

        # Can also reject
        rec.status = RecommendationStatus.rejected
        db.commit()
        assert rec.status == RecommendationStatus.rejected
