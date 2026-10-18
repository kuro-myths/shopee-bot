"""Product archiving (soft delete).

Instead of hard-deleting a product, it can be archived: the row stays
in the database with its history, but is excluded from listings and
checks by default.
"""
from ..db import db


def archive_product(product_id: int) -> bool:
    """Mark a product as archived. Returns True when it existed."""
    with db() as conn:
        cur = conn.execute(
            "UPDATE products SET archived=1, updated_at=datetime('now') WHERE id=? AND archived=0",
            (product_id,),
        )
        return cur.rowcount > 0


def restore_product(product_id: int) -> bool:
    """Un-archive a product. Returns True when it existed."""
    with db() as conn:
        cur = conn.execute(
            "UPDATE products SET archived=0, updated_at=datetime('now') WHERE id=? AND archived=1",
            (product_id,),
        )
        return cur.rowcount > 0
