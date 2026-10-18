"""Aggregate statistics over tracked products."""
from ..db import db


def compute_stats():
    """Return summary statistics across all products."""
    with db() as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"]
        if total == 0:
            return {
                "total": 0,
                "with_target": 0,
                "below_min": 0,
                "price_points": 0,
                "avg_drop_pct": 0.0,
                "marketplaces": {},
            }

        with_target = conn.execute(
            "SELECT COUNT(*) AS c FROM products WHERE target_price IS NOT NULL"
        ).fetchone()["c"]

        below_min = conn.execute(
            "SELECT COUNT(*) AS c FROM products "
            "WHERE min_price IS NOT NULL AND current_price IS NOT NULL "
            "AND current_price < min_price"
        ).fetchone()["c"]

        price_points = conn.execute(
            "SELECT COUNT(*) AS c FROM price_history"
        ).fetchone()["c"]

        avg_drop = conn.execute(
            "SELECT AVG((min_price - current_price) * 100.0 / min_price) AS v "
            "FROM products WHERE min_price > 0 AND current_price IS NOT NULL"
        ).fetchone()["v"]

        market_rows = conn.execute(
            "SELECT marketplace, COUNT(*) AS c FROM products GROUP BY marketplace"
        ).fetchall()

    return {
        "total": total,
        "with_target": with_target,
        "below_min": below_min,
        "price_points": price_points,
        "avg_drop_pct": round(avg_drop or 0.0, 2),
        "marketplaces": {r["marketplace"]: r["c"] for r in market_rows},
    }
