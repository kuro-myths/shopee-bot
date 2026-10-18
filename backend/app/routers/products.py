"""Product endpoints: upsert, list, history, target price, export, affiliate."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Response

from ..db import db
from ..models import AffiliateOut, HistoryPoint, NoteIn, ProductIn, ProductOut, TargetIn, TargetOut
from ..services.affiliate import get_affiliate_url
from ..services.archive import archive_product, restore_product
from ..services.cooldown import should_notify
from ..services.dedupe import should_record
from ..services.detector import check_drop, describe_drop
from ..services.export import active_products, to_csv, to_json
from ..services.filters import list_products as query_products
from ..services.notifier import NotifyError, send_telegram
from ..services.pruning import prune_history
from ..services.summary import history_summary
from ..services.targets import check_target_reached, describe_target_reached

router = APIRouter(prefix="/api/products", tags=["products"])


def _row_to_out(row) -> dict:
    return {
        "id": row["id"],
        "url": row["url"],
        "name": row["name"],
        "marketplace": row["marketplace"],
        "image": row["image"],
        "current_price": row["current_price"],
        "min_price": row["min_price"],
        "max_price": row["max_price"],
        "target_price": row["target_price"],
        "target_reached": (
            row["target_price"] is not None
            and row["current_price"] is not None
            and row["current_price"] <= row["target_price"]
        ),
        "note": row["note"],
        "archived": bool(row["archived"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@router.post("", response_model=ProductOut)
def upsert_product(payload: ProductIn):
    """Create or update a product and record the reported price.

    A price drop is detected when the newly reported price sits below
    the previous all-time minimum by more than the configured threshold.
    A target-reached event fires when the price falls to/below the
    user's target price. Identical consecutive prices within the dedupe
    window are skipped to keep the history meaningful.
    """
    previous_min = None
    previous_target = None
    product_id = None
    notify_drop = None
    notify_target = None

    with db() as conn:
        row = conn.execute(
            "SELECT * FROM products WHERE url = ?", (payload.url,)
        ).fetchone()

        if row:
            product_id = row["id"]
            previous_min = row["min_price"]
            previous_target = row["target_price"]
            conn.execute(
                "UPDATE products SET name=?, marketplace=?, image=?, note=?, updated_at=datetime('now') WHERE id=?",
                (payload.name, payload.marketplace, payload.image, payload.note, product_id),
            )
        else:
            cur = conn.execute(
                "INSERT INTO products (url, name, marketplace, image, note) VALUES (?, ?, ?, ?, ?)",
                (payload.url, payload.name, payload.marketplace, payload.image, payload.note),
            )
            product_id = cur.lastrowid

        # Record the price point if a price was reported (deduped)
        if payload.current_price is not None and should_record(product_id, payload.current_price):
            conn.execute(
                "INSERT INTO price_history (product_id, price) VALUES (?, ?)",
                (product_id, payload.current_price),
            )

            # Refresh min/max stats
            stats = conn.execute(
                "SELECT MIN(price) AS mn, MAX(price) AS mx FROM price_history WHERE product_id=?",
                (product_id,),
            ).fetchone()
            conn.execute(
                "UPDATE products SET current_price=?, min_price=?, max_price=?, updated_at=datetime('now') WHERE id=?",
                (payload.current_price, stats["mn"], stats["mx"], product_id),
            )

            # Detect drop against the PREVIOUS min (before this update)
            is_drop, drop_pct = check_drop(previous_min, payload.current_price)
            if is_drop:
                notify_drop = (product_id, payload.current_price, drop_pct)

            # Detect target reached against the stored target
            if previous_target is not None and check_target_reached(
                previous_target, payload.current_price
            ):
                notify_target = (product_id, payload.current_price, previous_target)
        else:
            conn.execute(
                "UPDATE products SET updated_at=datetime('now') WHERE id=?", (product_id,)
            )

        row = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()

    # Notify after the DB transaction closes (cooldown applies per product).
    # A broken Telegram token must never fail the product upsert.
    if notify_drop:
        pid, new_price, drop_pct = notify_drop
        if should_notify(pid):
            product_dict = _row_to_out(row)
            try:
                send_telegram(describe_drop(product_dict, new_price, drop_pct))
            except NotifyError:
                pass  # notification failure must not break tracking

    if notify_target:
        pid, new_price, target = notify_target
        if should_notify(pid):
            product_dict = _row_to_out(row)
            try:
                send_telegram(describe_target_reached(product_dict, new_price, target))
            except NotifyError:
                pass

    return _row_to_out(row)


@router.get("")
def list_products(
    search: Optional[str] = Query(None, description="Search by name or URL"),
    marketplace: Optional[str] = Query(None, description="Filter by marketplace"),
    has_target: Optional[bool] = Query(None, description="Only products with a target"),
    include_archived: bool = Query(False, description="Include archived products"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """List tracked products with search, filter and pagination."""
    rows, total = query_products(
        search=search,
        marketplace=marketplace,
        has_target=has_target,
        include_archived=include_archived,
        page=page,
        page_size=page_size,
    )
    total_pages = max(1, -(-total // page_size)) if total else 0
    return {
        "products": [_row_to_out(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }


@router.post("/prune")
def prune_endpoint(older_than_days: int = Query(90, ge=1, le=3650)):
    """Prune price history older than the retention window."""
    deleted = prune_history(older_than_days=older_than_days)
    return {"deleted_points": deleted}


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int):
    with db() as conn:
        row = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Product not found")
    return _row_to_out(row)


@router.get("/{product_id}/history", response_model=list[HistoryPoint])
def product_history(
    product_id: int,
    limit: int = Query(500, ge=1, le=5000, description="Max history points"),
):
    with db() as conn:
        rows = conn.execute(
            "SELECT price, recorded_at FROM price_history "
            "WHERE product_id=? ORDER BY id DESC LIMIT ?",
            (product_id, limit),
        ).fetchall()
    return [
        HistoryPoint(price=r["price"], date=r["recorded_at"]) for r in reversed(rows)
    ]


@router.put("/{product_id}/target", response_model=TargetOut)
def set_target(product_id: int, payload: TargetIn):
    """Set or update the target price for a product."""
    if payload.target_price <= 0:
        raise HTTPException(422, "Target price must be positive")

    with db() as conn:
        row = conn.execute(
            "SELECT * FROM products WHERE id=?", (product_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Product not found")
        conn.execute(
            "UPDATE products SET target_price=?, updated_at=datetime('now') WHERE id=?",
            (payload.target_price, product_id),
        )
        row = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()

    reached = check_target_reached(row["target_price"], row["current_price"])
    if reached:
        try:
            send_telegram(
                describe_target_reached(_row_to_out(row), row["current_price"], row["target_price"])
            )
        except NotifyError:
            pass  # notification failure must not fail the request
    return {"id": product_id, "target_price": row["target_price"], "target_reached": reached}


@router.get("/{product_id}/summary")
def product_summary(product_id: int):
    """Return min/max/avg/count for a product's price history."""
    with db() as conn:
        exists = conn.execute(
            "SELECT id FROM products WHERE id=?", (product_id,)
        ).fetchone()
    if not exists:
        raise HTTPException(404, "Product not found")
    return history_summary(product_id)


@router.put("/{product_id}/note", response_model=ProductOut)
def set_note(product_id: int, payload: NoteIn):
    """Attach a free-text note to a product."""
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM products WHERE id=?", (product_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Product not found")
        conn.execute(
            "UPDATE products SET note=?, updated_at=datetime('now') WHERE id=?",
            (payload.note, product_id),
        )
        row = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    return _row_to_out(row)


@router.delete("/{product_id}/target", response_model=TargetOut)
def clear_target(product_id: int):
    """Remove the target price from a product."""
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM products WHERE id=?", (product_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Product not found")
        conn.execute(
            "UPDATE products SET target_price=NULL, updated_at=datetime('now') WHERE id=?",
            (product_id,),
        )
    return {"id": product_id, "target_price": None, "target_reached": False}


@router.post("/{product_id}/affiliate", response_model=AffiliateOut)
def product_affiliate(product_id: int):
    with db() as conn:
        row = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Product not found")
    return get_affiliate_url(row)


@router.post("/{product_id}/archive")
def archive_endpoint(product_id: int):
    """Archive a product (soft delete)."""
    if not archive_product(product_id):
        raise HTTPException(404, "Product not found")
    return {"archived": product_id}


@router.post("/{product_id}/restore")
def restore_endpoint(product_id: int):
    """Restore an archived product."""
    if not restore_product(product_id):
        raise HTTPException(404, "Product not found")
    return {"restored": product_id}


@router.delete("/{product_id}")
def delete_product(product_id: int):
    """Permanently remove a product and its price history."""
    with db() as conn:
        cur = conn.execute("DELETE FROM products WHERE id=?", (product_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "Product not found")
    return {"deleted": product_id}


@router.get("/export/{fmt}")
def export_products(fmt: str):
    """Export all active (non-archived) products as CSV or JSON."""
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM products WHERE archived = 0 ORDER BY updated_at DESC"
        ).fetchall()
    rows = active_products(rows)

    if fmt == "csv":
        return Response(
            content=to_csv(rows),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="products.csv"'},
        )
    if fmt == "json":
        return Response(
            content=to_json(rows),
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="products.json"'},
        )
    raise HTTPException(400, "format must be 'csv' or 'json'")
