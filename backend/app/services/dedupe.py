"""Price history de-duplication.

The extension reports a price every time the user opens a product page,
which can produce many identical consecutive points. Dedupe keeps the
history meaningful by skipping a new point when it equals the previous
one recorded within a short window.
"""
import os

from ..db import db

DEDUPE_WINDOW_SECONDS = int(os.getenv("DEDUPE_WINDOW_SECONDS", str(60 * 60)))  # 1 hour


def should_record(product_id: int, price: float) -> bool:
    """Return False when an identical price was recorded recently."""
    with db() as conn:
        row = conn.execute(
            "SELECT price, recorded_at FROM price_history "
            "WHERE product_id=? ORDER BY recorded_at DESC LIMIT 1",
            (product_id,),
        ).fetchone()
    if row is None:
        return True
    if abs(row["price"] - price) > 0.001:
        return True
    # Same price: only skip if recorded within the dedupe window
    try:
        from datetime import datetime
        last = datetime.fromisoformat(row["recorded_at"].replace(" ", "T"))
        now = datetime.utcnow()
        return (now - last).total_seconds() > DEDUPE_WINDOW_SECONDS
    except Exception:
        return True
