"""Export helpers: serialize tracked products to CSV or JSON."""
import csv
import io
import json


def _field(row, key, default=None):
    """Read a field from either a dict or a sqlite3.Row safely."""
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return default


def _flatten(product):
    """Map a product row to export-friendly dict."""
    return {
        "id": _field(product, "id"),
        "name": _field(product, "name"),
        "marketplace": _field(product, "marketplace"),
        "url": _field(product, "url"),
        "current_price": _field(product, "current_price"),
        "min_price": _field(product, "min_price"),
        "max_price": _field(product, "max_price"),
        "target_price": _field(product, "target_price"),
        "note": _field(product, "note", ""),
        "created_at": _field(product, "created_at"),
        "updated_at": _field(product, "updated_at"),
    }


def active_products(products):
    """Filter out archived products (soft-deleted) from an export."""
    return [p for p in products if not _field(p, "archived", 0)]


def to_csv(products):
    """Return a CSV string of products."""
    if not products:
        return "id,name,marketplace,url,current_price,min_price,max_price,target_price,note,created_at,updated_at\n"

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(_flatten(products[0]).keys()))
    writer.writeheader()
    for product in products:
        writer.writerow(_flatten(product))
    return buffer.getvalue()


def to_json(products):
    """Return a JSON string of products."""
    return json.dumps([_flatten(p) for p in products], indent=2)
