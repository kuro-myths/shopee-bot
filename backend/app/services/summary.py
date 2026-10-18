"""Price history summaries per product."""
from ..db import db


def history_summary(product_id: int):
    """Return min/max/avg/count for a product's price history."""
    with db() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS n,
                   MIN(price) AS mn,
                   MAX(price) AS mx,
                   AVG(price) AS avg
            FROM price_history WHERE product_id = ?
            """,
            (product_id,),
        ).fetchone()
    return {
        "count": row["n"],
        "min": row["mn"],
        "max": row["mx"],
        "avg": round(row["avg"], 2) if row["avg"] is not None else None,
    }
