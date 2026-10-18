"""Price target / wishlist logic.

A user can set a target price on a product. When the tracked price
falls to or below the target, the target is considered "reached" and a
notification is sent.
"""


def check_target_reached(target_price, current_price):
    """Return True when current price is at or below the target."""
    if target_price is None or current_price is None:
        return False
    return current_price <= target_price


def describe_target_reached(product, current_price, target_price):
    """Human-readable message for target-reached notifications."""
    lines = [
        "🎯 *TARGET HARGA TERCAPAI*",
        f"*{product['name']}*",
        f"Marketplace: {product['marketplace']}",
        f"Harga sekarang: *Rp {current_price:,.0f}*",
        f"Target kamu: Rp {target_price:,.0f}",
        product["url"],
    ]
    return "\n".join(lines)
