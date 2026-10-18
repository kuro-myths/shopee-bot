"""Price drop detection.

A "drop" is recorded when a new price point is below the previous
all-time minimum by more than the configured threshold. Whenever a drop
is detected, a Telegram notification is sent (if the bot is configured).
"""
from ..config import settings


def check_drop(previous_min, new_price):
    """Return (is_drop: bool, drop_pct: float).

    drop_pct is negative when the price is below the previous min.
    """
    if previous_min is None or not new_price or previous_min <= 0:
        return False, 0.0
    diff = new_price - previous_min
    pct = (diff / previous_min) * 100
    return pct < -settings.drop_threshold_pct, pct


def describe_drop(product, new_price, drop_pct):
    """Human-readable message for Telegram notifications."""
    lines = [
        "📉 *HARGA TURUN DETECTED*",
        f"*{product['name']}*",
        f"Marketplace: {product['marketplace']}",
        f"Harga baru: *Rp {new_price:,.0f}*",
        f"Turun: *{abs(drop_pct):.1f}%*",
        product["url"],
    ]
    return "\n".join(lines)
