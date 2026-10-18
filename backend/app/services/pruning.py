"""History pruning.

Keeps the database small by deleting price points older than a
retention period, while always preserving the single most recent point
per product so charts stay intact.
"""
from datetime import datetime, timedelta

from ..db import db


def prune_history(older_than_days: int = 90) -> int:
    """Delete price points older than the retention window.

    Returns the number of deleted rows. The most recent point per
    product is always kept (based on recorded_at, id as tiebreaker).
    """
    cutoff = datetime.utcnow() - timedelta(days=older_than_days)
    cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")

    with db() as conn:
        cur = conn.execute(
            """
            DELETE FROM price_history
            WHERE recorded_at < ?
              AND id NOT IN (
                SELECT id FROM (
                  SELECT id,
                         ROW_NUMBER() OVER (
                           PARTITION BY product_id
                           ORDER BY recorded_at DESC, id DESC
                         ) AS rn
                  FROM price_history
                ) WHERE rn = 1
              )
            """,
            (cutoff_str,),
        )
        return cur.rowcount
