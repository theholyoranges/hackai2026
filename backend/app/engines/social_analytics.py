"""Social-media analytics engine -- computes factual engagement metrics."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from app.models.menu_item import MenuItem
from app.models.sales_record import SalesRecord
from app.models.social_post import SocialPost


class SocialAnalyticsEngine:
    """Pure-analytics helper for social-media post data."""

    # ------------------------------------------------------------------
    # Engagement by post type
    # ------------------------------------------------------------------

    @staticmethod
    def get_engagement_by_type(
        db: Session, restaurant_id: int
    ) -> list[dict[str, Any]]:
        """Average likes, comments, shares, and reach grouped by post_type."""
        rows = (
            db.query(
                SocialPost.post_type,
                func.avg(SocialPost.likes).label("avg_likes"),
                func.avg(SocialPost.comments).label("avg_comments"),
                func.avg(SocialPost.shares).label("avg_shares"),
                func.avg(SocialPost.reach).label("avg_reach"),
                func.count(SocialPost.id).label("post_count"),
            )
            .filter(
                SocialPost.restaurant_id == restaurant_id,
                SocialPost.post_type.isnot(None),
            )
            .group_by(SocialPost.post_type)
            .all()
        )
        return [
            {
                "post_type": r.post_type,
                "avg_likes": round(float(r.avg_likes), 2) if r.avg_likes else 0.0,
                "avg_comments": round(float(r.avg_comments), 2) if r.avg_comments else 0.0,
                "avg_shares": round(float(r.avg_shares), 2) if r.avg_shares else 0.0,
                "avg_reach": round(float(r.avg_reach), 2) if r.avg_reach else 0.0,
                "post_count": int(r.post_count),
            }
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Best times to post
    # ------------------------------------------------------------------

    @staticmethod
    def get_best_times(
        db: Session, restaurant_id: int
    ) -> dict[str, Any]:
        """Average engagement (likes + comments + shares) by day_of_week and hour."""
        posts = (
            db.query(SocialPost)
            .filter(
                SocialPost.restaurant_id == restaurant_id,
                SocialPost.posted_at.isnot(None),
            )
            .all()
        )
        if not posts:
            return {"by_day_of_week": [], "by_hour": []}

        df = pd.DataFrame(
            [
                {
                    "day_of_week": p.posted_at.strftime("%A") if p.posted_at else None,
                    "hour": p.posted_at.hour if p.posted_at else None,
                    "engagement": (p.likes or 0) + (p.comments or 0) + (p.shares or 0),
                    "reach": p.reach or 0,
                }
                for p in posts
            ]
        )

        by_day: list[dict[str, Any]] = []
        if df["day_of_week"].notna().any():
            by_day = (
                df.dropna(subset=["day_of_week"])
                .groupby("day_of_week")[["engagement", "reach"]]
                .mean()
                .round(2)
                .reset_index()
                .to_dict(orient="records")
            )

        by_hour: list[dict[str, Any]] = []
        if df["hour"].notna().any():
            by_hour_df = (
                df.dropna(subset=["hour"])
                .groupby("hour")[["engagement", "reach"]]
                .mean()
                .round(2)
                .reset_index()
            )
            by_hour_df["hour"] = by_hour_df["hour"].astype(int)
            by_hour = by_hour_df.to_dict(orient="records")

        return {"by_day_of_week": by_day, "by_hour": by_hour}

    # ------------------------------------------------------------------
    # Trending items (linked to high-performing posts)
    # ------------------------------------------------------------------

    @staticmethod
    def get_trending_items(
        db: Session, restaurant_id: int
    ) -> list[dict[str, Any]]:
        """Items linked to posts with above-median engagement."""
        rows = (
            db.query(
                MenuItem.name,
                SocialPost.likes,
                SocialPost.comments,
                SocialPost.shares,
                SocialPost.reach,
            )
            .join(SocialPost, SocialPost.menu_item_id == MenuItem.id)
            .filter(SocialPost.restaurant_id == restaurant_id)
            .all()
        )
        if not rows:
            return []

        df = pd.DataFrame(
            [
                {
                    "item": r.name,
                    "likes": r.likes or 0,
                    "comments": r.comments or 0,
                    "shares": r.shares or 0,
                    "reach": r.reach or 0,
                }
                for r in rows
            ]
        )
        df["engagement"] = df["likes"] + df["comments"] + df["shares"]
        median_eng = df["engagement"].median()

        trending = df[df["engagement"] >= median_eng]

        agg = (
            trending.groupby("item")
            .agg(
                avg_engagement=("engagement", "mean"),
                avg_reach=("reach", "mean"),
                post_count=("engagement", "count"),
            )
            .round(2)
            .reset_index()
            .sort_values("avg_engagement", ascending=False)
        )
        return agg.to_dict(orient="records")

    # ------------------------------------------------------------------
    # Campaign opportunities
    # ------------------------------------------------------------------

    @staticmethod
    def get_campaign_opportunities(
        db: Session, restaurant_id: int
    ) -> list[dict[str, Any]]:
        """Combine high-margin items with best social posting windows.

        Returns items that have above-median margin together with the
        best day_of_week and hour windows from social data.
        """
        # --- high-margin items ---
        items = (
            db.query(MenuItem)
            .filter(
                MenuItem.restaurant_id == restaurant_id,
                MenuItem.is_active.is_(True),
                MenuItem.ingredient_cost.isnot(None),
            )
            .all()
        )
        if not items:
            return []

        df_items = pd.DataFrame(
            [
                {
                    "item": i.name,
                    "price": float(i.price),
                    "cost": float(i.ingredient_cost) if i.ingredient_cost is not None else 0.0,
                }
                for i in items
            ]
        )
        df_items["margin"] = df_items["price"] - df_items["cost"]
        median_margin = df_items["margin"].median()
        high_margin = df_items[df_items["margin"] >= median_margin]

        # --- best times ---
        best_times = SocialAnalyticsEngine.get_best_times(db, restaurant_id)
        best_day = None
        best_hour = None

        if best_times["by_day_of_week"]:
            best_day_row = max(
                best_times["by_day_of_week"], key=lambda d: d.get("engagement", 0)
            )
            best_day = best_day_row.get("day_of_week")

        if best_times["by_hour"]:
            best_hour_row = max(
                best_times["by_hour"], key=lambda d: d.get("engagement", 0)
            )
            best_hour = best_hour_row.get("hour")

        results: list[dict[str, Any]] = []
        for _, row in high_margin.iterrows():
            results.append(
                {
                    "item": row["item"],
                    "margin": round(float(row["margin"]), 2),
                    "suggested_post_day": best_day,
                    "suggested_post_hour": int(best_hour) if best_hour is not None else None,
                }
            )
        return results

    # ------------------------------------------------------------------
    # Full analysis
    # ------------------------------------------------------------------

    @classmethod
    def get_full_analysis(
        cls, db: Session, restaurant_id: int
    ) -> dict[str, Any]:
        """Run every social-analytics method and return a combined dict."""
        return {
            "engagement_by_type": cls.get_engagement_by_type(db, restaurant_id),
            "best_times": cls.get_best_times(db, restaurant_id),
            "trending_items": cls.get_trending_items(db, restaurant_id),
            "campaign_opportunities": cls.get_campaign_opportunities(db, restaurant_id),
        }
