"""Command handlers for the PriceDrop Tracker Telegram bot.

Kept as pure functions that receive (backend_client, args) so the
message routing stays thin and the handlers are unit-testable.
"""
import re


def fmt_rp(n):
    return f"Rp {n:,.0f}" if n else "Rp —"


def parse_target_arg(arg):
    """Parse '/target <id> <price>' into (product_id, price) or None."""
    m = re.match(r"(\d+)\s+([\d.]+)", arg)
    if not m:
        return None
    return int(m.group(1)), float(m.group(2).replace(".", ""))


def cmd_start():
    return (
        "PriceDrop Tracker bot\n\n"
        "/track <url> - mulai pantau harga produk Shopee/TikTok\n"
        "/list - daftar produk yang dipantau\n"
        "/search <kata> - cari produk yang dipantau\n"
        "/target <id> <harga> - set target harga\n"
        "/archive <id> - arsipkan produk\n"
        "/note <id> <teks> - simpan catatan produk\n"
        "/top - produk dengan diskon terbesar\n"
        "/recent - produk yang baru diperbarui\n"
        "/stats - statistik pemantauan\n"
        "/export - unduh daftar produk (JSON)\n"
        "/ping - cek koneksi backend\n"
        "/version - lihat versi API\n"
        "/price <id> - lihat harga terkini produk\n"
        "/history <id> - riwayat harga terakhir produk\n"
        "/restore <id> - kembalikan produk yang diarsipkan\n"
        "/settings - lihat pengaturan chat\n"
        "/menu - tampilkan menu tombol\n"
        "/drop on|off - aktifkan/nonaktifkan notifikasi chat\n"
        "/prune <hari> - bersihkan riwayat harga lama\n"
        "/untrack <id> - hapus produk dari pantauan\n\n"
        "Alias: /daftar = /list, /bantuan = /help, /panduan = /menu\n\n"
        "Kirim link produk, dan saya akan kabari kalau harganya turun."
    )


def cmd_settings(alerts: bool, backend_url: str) -> str:
    """Show per-chat configuration summary."""
    return (
        "Pengaturan chat:\n"
        f"- Notifikasi harga turun: {'AKTIF' if alerts else 'NONAKTIF'}\n"
        f"- Backend: {backend_url}\n\n"
        "Ubah notifikasi dengan /drop on|off."
    )


def cmd_list(products):
    if not products:
        return "Belum ada produk yang dipantau."
    lines = ["Produk yang dipantau:\n"]
    for p in products:
        lines.append(
            f"#{p['id']} {p['marketplace']} - {fmt_rp(p['current_price'])} "
            f"(min {fmt_rp(p['min_price'])})\n  {p['name'][:60]}"
        )
    return "\n".join(lines)


def cmd_stats(products):
    if not products:
        return "Belum ada data untuk statistik."
    total = len(products)
    with_target = sum(1 for p in products if p.get("target_price"))
    drops = sum(
        1 for p in products
        if p.get("min_price") and p.get("current_price")
        and p["current_price"] < p["min_price"]
    )
    marketplaces = {}
    for p in products:
        marketplaces[p.get("marketplace", "?")] = (
            marketplaces.get(p.get("marketplace", "?"), 0) + 1
        )
    lines = [
        "Statistik pemantauan:",
        f"Total produk: {total}",
        f"Produk dengan target: {with_target}",
        f"Harga di bawah minimum: {drops}",
        "Per marketplace: " + ", ".join(f"{k}={v}" for k, v in marketplaces.items()),
    ]
    return "\n".join(lines)


def cmd_top(products, n=5):
    """Products with the biggest discount vs their minimum price."""
    ranked = []
    for p in products:
        if not p.get("min_price") or not p.get("current_price") or p["min_price"] <= 0:
            continue
        pct = (p["min_price"] - p["current_price"]) / p["min_price"] * 100
        if pct > 0:
            ranked.append((pct, p))
    ranked.sort(reverse=True)
    if not ranked:
        return "Belum ada produk dengan harga di bawah minimum."
    lines = ["Produk dengan diskon terbesar:"]
    for pct, p in ranked[:n]:
        lines.append(f"#{p['id']} {p['name'][:40]} - {pct:.1f}% ({fmt_rp(p['current_price'])})")
    return "\n".join(lines)


def cmd_recent(products, n=5):
    """Most recently updated products."""
    ordered = sorted(
        products, key=lambda p: p.get("updated_at") or "", reverse=True
    )
    if not ordered:
        return "Belum ada produk."
    lines = ["Produk terbaru:"]
    for p in ordered[:n]:
        lines.append(f"#{p['id']} {p['name'][:40]} - {fmt_rp(p['current_price'])}")
    return "\n".join(lines)
