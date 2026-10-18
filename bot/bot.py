"""
PriceDrop Tracker — Telegram bot.

Commands:
  /start        - welcome message
  /track <url>  - start tracking a Shopee / TikTok Shop product
  /list         - show tracked products and current prices
  /search <q>   - search tracked products
  /target <id> <price> - set a target price
  /stats        - tracking statistics
  /export       - download the tracked product list (JSON)
  /ping         - check backend connectivity
  /untrack <id> - stop tracking a product
  /drop         - enable/disable drop alerts for this chat
"""
import os
import re
import sys

import requests

from commands import cmd_list, cmd_recent, cmd_settings, cmd_start, cmd_stats, cmd_top, fmt_rp, parse_target_arg
from state import alerts_enabled, set_alerts

API_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

if not TOKEN:
    print("TELEGRAM_BOT_TOKEN is not set. See .env.example")
    sys.exit(1)

BOT_API = f"https://api.telegram.org/bot{TOKEN}"


def tg(method, **params):
    url = f"{BOT_API}/{method}"
    try:
        r = requests.post(url, json=params, timeout=15)
        return r.json()
    except Exception as e:
        print("Telegram error:", e)
        return {"ok": False}


def backend(path, method="GET", payload=None):
    url = f"{API_URL}{path}"
    try:
        if method == "POST":
            r = requests.post(url, json=payload, timeout=15)
        elif method == "PUT":
            r = requests.put(url, json=payload, timeout=15)
        elif method == "DELETE":
            r = requests.delete(url, timeout=15)
        else:
            r = requests.get(url, timeout=15)
        if r.status_code == 200:
            return r.json()
        print("Backend error:", r.status_code, r.text[:200])
    except Exception as e:
        print("Backend unreachable:", e)
    return None


def parse_track_url(text):
    """Extract a product URL from a /track command."""
    m = re.search(r"https?://[^\s]+", text)
    if not m:
        return None
    url = m.group(0).rstrip(".,;)")
    if "shopee.co.id" in url or "tiktok.com" in url:
        return url
    return None


def handle_message(chat_id, text):
    parts = text.split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd in ("/start", "/help", "/bantuan"):
        return cmd_start()

    if cmd == "/track":
        url = parse_track_url(text)
        if not url:
            return "Kasih link produk Shopee atau TikTok Shop yang valid."
        data = backend("/api/products", "POST", {
            "url": url,
            "name": "Produk (link)",
            "marketplace": "shopee" if "shopee" in url else "tiktok",
            "current_price": None,
        })
        if data:
            reply_markup = None
            if url.startswith("http"):
                reply_markup = {
                    "inline_keyboard": [[
                        {"text": "Buka produk", "url": url},
                    ]]
                }
            reply = (
                f"Produk terdaftar! #{data['id']}\n"
                f"{data['name']}\n"
                f"{data['url']}\n\n"
                "Harga akan tercatat otomatis saat kamu buka halamannya "
                "pakai ekstensi Chrome."
            )
            if reply_markup:
                tg("sendMessage", chat_id=chat_id, text=reply, reply_markup=reply_markup)
                return None
            return reply
        return "Gagal mendaftarkan produk. Backend aktif?"

    if cmd in ("/list", "/daftar"):
        data = backend("/api/products")
        if data is None:
            return "Backend tidak merespons."
        return cmd_list(data.get("products", []))

    if cmd == "/search":
        q = arg.strip()
        if not q:
            return "Contoh: /search keyboard"
        data = backend(f"/api/products?search={q}")
        if data is None:
            return "Backend tidak merespons."
        products = data.get("products", [])
        if not products:
            return f"Tidak ada produk cocok dengan '{q}'."
        return cmd_list(products)

    if cmd == "/target":
        parsed = parse_target_arg(arg)
        if not parsed:
            return "Contoh: /target 3 45000"
        product_id, target_price = parsed
        data = backend(f"/api/products/{product_id}/target", "PUT", {
            "target_price": target_price,
        })
        if data:
            reached = "SUDAH TERCAPAI" if data["target_reached"] else "disimpan"
            return f"Target untuk #{product_id}: {fmt_rp(target_price)} ({reached})."
        return "Gagal set target - pastikan ID produk benar."

    if cmd == "/stats":
        data = backend("/api/products")
        if data is None:
            return "Backend tidak merespons."
        return cmd_stats(data.get("products", []))

    if cmd == "/settings":
        return cmd_settings(alerts_enabled(chat_id), API_URL)

    if cmd == "/price":
        m = re.match(r"(\d+)", arg)
        if not m:
            return "Contoh: /price 3"
        product_id = int(m.group(1))
        data = backend(f"/api/products/{product_id}")
        if not data:
            return "Produk tidak ditemukan."
        return (
            f"#{data['id']} {data['name'][:50]}\n"
            f"Harga sekarang: {fmt_rp(data['current_price'])}\n"
            f"Min: {fmt_rp(data['min_price'])} | Max: {fmt_rp(data['max_price'])}\n"
            f"Target: {fmt_rp(data['target_price']) if data.get('target_price') else '—'}"
        )

    if cmd == "/history":
        m = re.match(r"(\d+)", arg)
        if not m:
            return "Contoh: /history 3"
        product_id = int(m.group(1))
        data = backend(f"/api/products/{product_id}/history")
        if data is None:
            return "Produk tidak ditemukan atau backend tidak merespons."
        if not data:
            return "Belum ada riwayat harga."
        points = data[-5:]
        lines = [f"Riwayat harga #{product_id} (5 terakhir):"]
        for point in points:
            lines.append(f"{point['date']} - {fmt_rp(point['price'])}")
        return "\n".join(lines)

    if cmd == "/restore":
        m = re.match(r"(\d+)", arg)
        if not m:
            return "Contoh: /restore 3"
        product_id = int(m.group(1))
        try:
            r = requests.post(f"{API_URL}/api/products/{product_id}/restore", timeout=15)
            if r.status_code == 200:
                return f"Produk #{product_id} dikembalikan ke daftar."
            return f"Produk #{product_id} tidak ditemukan."
        except Exception:
            return "Gagal restore - backend aktif?"

    if cmd == "/export":
        try:
            r = requests.get(f"{API_URL}/api/products/export/json", timeout=15)
            if r.status_code == 200:
                with open("products_export.json", "w", encoding="utf-8") as f:
                    f.write(r.text)
                return "Daftar produk diexport ke products_export.json di server bot."
            return "Gagal export dari backend."
        except Exception as e:
            print("Export error:", e)
            return "Gagal export - backend tidak merespons."

    if cmd == "/ping":
        try:
            r = requests.get(f"{API_URL}/health", timeout=10)
            if r.status_code == 200:
                body = r.json()
                return f"Backend OK (status={body.get('status')}, db={body.get('database')})."
            return f"Backend merespons dengan status {r.status_code}."
        except Exception:
            return "Backend tidak bisa dijangkau."

    if cmd == "/version":
        try:
            r = requests.get(f"{API_URL}/api/version", timeout=10)
            if r.status_code == 200:
                body = r.json()
                return f"PriceDrop Tracker API v{body.get('version')} (api v{body.get('api_version')})"
            return f"Backend merespons dengan status {r.status_code}."
        except Exception:
            return "Backend tidak bisa dijangkau."

    if cmd == "/untrack":
        m = re.match(r"(\d+)", arg)
        if not m:
            return "Contoh: /untrack 3"
        product_id = int(m.group(1))
        try:
            r = requests.delete(f"{API_URL}/api/products/{product_id}", timeout=15)
            if r.status_code == 200:
                return f"Produk #{product_id} dihapus dari pantauan."
            return f"Produk #{product_id} tidak ditemukan."
        except Exception:
            return "Gagal menghapus - backend aktif?"

    if cmd == "/drop":
        action = arg.strip().lower()
        if action in ("off", "nonaktif"):
            set_alerts(chat_id, False)
            return "Notifikasi harga turun untuk chat ini: NONAKTIF."
        if action in ("on", "aktif"):
            set_alerts(chat_id, True)
            return "Notifikasi harga turun untuk chat ini: AKTIF."
        current = "AKTIF" if alerts_enabled(chat_id) else "NONAKTIF"
        return f"Notifikasi harga turun chat ini: {current}.\nGunakan /drop on atau /drop off."

    if cmd == "/top":
        data = backend("/api/products")
        if data is None:
            return "Backend tidak merespons."
        return cmd_top(data.get("products", []))

    if cmd == "/recent":
        data = backend("/api/products")
        if data is None:
            return "Backend tidak merespons."
        return cmd_recent(data.get("products", []))

    if cmd == "/note":
        m = re.match(r"(\d+)\s+(.+)", arg)
        if not m:
            return "Contoh: /note 3 beli buat hadiah"
        product_id = int(m.group(1))
        note = m.group(2).strip()
        data = backend(f"/api/products/{product_id}/note", "PUT", {"note": note})
        if data:
            return f"Catatan untuk #{product_id} disimpan."
        return "Gagal menyimpan catatan - pastikan ID benar."

    if cmd == "/prune":
        m = re.match(r"(\d+)", arg)
        days = int(m.group(1)) if m else 90
        try:
            r = requests.post(
                f"{API_URL}/api/products/prune?older_than_days={days}", timeout=15
            )
            if r.status_code == 200:
                return f"Riwayat lebih dari {days} hari dibersihkan ({r.json()['deleted_points']} titik)."
            return "Gagal prune."
        except Exception:
            return "Gagal prune - backend tidak merespons."

    if cmd == "/archive":
        m = re.match(r"(\d+)", arg)
        if not m:
            return "Contoh: /archive 3"
        product_id = int(m.group(1))
        try:
            r = requests.post(f"{API_URL}/api/products/{product_id}/archive", timeout=15)
            if r.status_code == 200:
                return f"Produk #{product_id} diarsipkan (tidak muncul di daftar)."
            return f"Produk #{product_id} tidak ditemukan."
        except Exception:
            return "Gagal mengarsipkan - backend aktif?"

    return "Perintah tidak dikenal. Ketik /help"


def send_inline_keyboard(chat_id):
    """Send the main menu as an inline keyboard."""
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "Daftar produk", "callback_data": "/list"},
                {"text": "Statistik", "callback_data": "/stats"},
            ],
            [
                {"text": "Bantuan", "callback_data": "/help"},
            ],
        ]
    }
    tg("sendMessage", chat_id=chat_id, text="Menu PriceDrop Tracker:", reply_markup=reply_markup)


def main():
    offset = 0
    print("PriceDrop Tracker bot running...")
    while True:
        updates = tg("getUpdates", offset=offset, timeout=30)
        if not updates.get("ok"):
            continue
        for upd in updates.get("result", []):
            offset = upd["update_id"] + 1

            if "callback_query" in upd:
                cb = upd["callback_query"]
                chat_id = cb.get("message", {}).get("chat", {}).get("id")
                cmd = cb.get("data", "")
                if chat_id and cmd:
                    reply = handle_message(chat_id, cmd)
                    if reply:
                        tg("sendMessage", chat_id=chat_id, text=reply)
                continue

            msg = upd.get("message", {})
            text = msg.get("text")
            chat_id = msg.get("chat", {}).get("id")
            if not text or not chat_id:
                continue

            if text in ("/menu", "/panduan"):
                send_inline_keyboard(chat_id)
                continue

            reply = handle_message(chat_id, text)
            if reply:
                tg("sendMessage", chat_id=chat_id, text=reply)


if __name__ == "__main__":
    main()
