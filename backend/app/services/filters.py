"""Filtering, search and pagination for product listings."""
from ..db import db

PAGE_SIZE_DEFAULT = 50
PAGE_SIZE_MAX = 200


def list_products(search=None, marketplace=None, has_target=None, page=1, page_size=50, include_archived=False):
    """Return (products, total) filtered and paginated."""
    clauses = []
    params = []

    if not include_archived:
        clauses.append("archived = 0")

    if search:
        clauses.append("(name LIKE ? OR url LIKE ?)")
        like = f"%{search}%"
        params.extend([like, like])

    if marketplace:
        clauses.append("marketplace = ?")
        params.append(marketplace)

    if has_target is not None:
        if has_target:
            clauses.append("target_price IS NOT NULL")
        else:
            clauses.append("target_price IS NULL")

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    page = max(1, page)
    page_size = min(max(1, page_size), PAGE_SIZE_MAX)
    offset = (page - 1) * page_size

    with db() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) AS c FROM products {where}", params
        ).fetchone()["c"]
        rows = conn.execute(
            f"SELECT * FROM products {where} ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            [*params, page_size, offset],
        ).fetchall()

    return list(rows), total
