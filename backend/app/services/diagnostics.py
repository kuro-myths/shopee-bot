"""Self-diagnostics: detect common misconfiguration and suggest fixes.

Each check returns {id, title, status, detail, fix}. status is one of
ok | info | warn | error. Secrets are never included in the output.
"""
import os
import re

from .. import db as dbmod
from ..config import settings
from . import errorlog

TOKEN_RE = re.compile(r"^\d{6,}:[A-Za-z0-9_-]{30,}$")


def _check(id_, title, status, detail, fix=""):
    return {"id": id_, "title": title, "status": status, "detail": detail, "fix": fix}


def on_railway() -> bool:
    return any(k in os.environ for k in ("RAILWAY_ENVIRONMENT", "RAILWAY_PROJECT_ID", "RAILWAY_SERVICE_NAME"))


def _database_checks():
    out = []
    path = dbmod.DB_PATH
    if dbmod.DB_FALLBACK_REASON:
        out.append(_check(
            "database", "Database", "error",
            f"Lokasi database yang dikonfigurasi tidak bisa ditulis. {dbmod.DB_FALLBACK_REASON}",
            "Di Railway: tambahkan Volume dengan mount path /data, atau set DATABASE_URL ke path yang bisa ditulis.",
        ))
    else:
        try:
            with dbmod.db() as conn:
                conn.execute("SELECT 1").fetchone()
            out.append(_check("database", "Database", "ok", f"SQLite terhubung ({path})."))
        except Exception as exc:  # pragma: no cover - defensive
            out.append(_check("database", "Database", "error", f"Tidak bisa query database: {exc}",
                              "Periksa DATABASE_URL dan izin tulis pada direktorinya."))

    if on_railway():
        volume = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", "")
        directory = os.path.dirname(os.path.abspath(path))
        persistent = bool(volume) and os.path.abspath(path).startswith(os.path.abspath(volume))
        if persistent:
            out.append(_check("persistence", "Penyimpanan permanen", "ok", f"Database berada di Volume ({volume})."))
        else:
            out.append(_check(
                "persistence", "Penyimpanan permanen", "warn",
                f"Database di {directory} tidak berada di Railway Volume, sehingga akan HILANG setiap redeploy.",
                "Railway -> service -> Volumes -> New Volume, mount path /data. DATABASE_URL harus sqlite:////data/pricedrop.db.",
            ))
    return out


def run_checks() -> dict:
    checks = _database_checks()

    from .. import main as _main  # import lambat: hindari siklus saat modul dimuat
    if _main._dashboard_dir:
        checks.append(_check("dashboard", "Dashboard", "ok", f"File dashboard ditemukan ({_main._dashboard_dir})."))
    else:
        checks.append(_check("dashboard", "Dashboard", "error", "Folder dashboard (web/) tidak ada di server, /dashboard akan 404.",
                             "Pastikan Dockerfile memuat 'COPY web/ ./web/', lalu deploy ulang."))

    if settings.api_key:
        checks.append(_check("api_key", "Autentikasi API", "ok", "API_KEY aktif; endpoint /api dilindungi."))
    else:
        checks.append(_check(
            "api_key", "Autentikasi API", "warn" if on_railway() else "info",
            "API_KEY kosong: siapa pun yang tahu URL bisa membaca dan menulis data.",
            "Isi variable API_KEY di Railway dengan string acak, lalu masukkan key yang sama di Pengaturan dashboard dan ekstensi.",
        ))

    token, chat = settings.telegram_bot_token, settings.telegram_chat_id
    if not token and not chat:
        checks.append(_check("telegram", "Alert Telegram", "info", "Belum dikonfigurasi; notifikasi penurunan harga nonaktif.",
                             "Isi TELEGRAM_BOT_TOKEN dan TELEGRAM_CHAT_ID jika ingin alert."))
    elif token and not chat:
        checks.append(_check("telegram", "Alert Telegram", "warn", "TELEGRAM_BOT_TOKEN diisi tapi TELEGRAM_CHAT_ID kosong; alert tidak akan terkirim.",
                             "Isi TELEGRAM_CHAT_ID (kirim pesan ke bot, lalu cek chat id via @userinfobot)."))
    elif chat and not token:
        checks.append(_check("telegram", "Alert Telegram", "warn", "TELEGRAM_CHAT_ID diisi tapi TELEGRAM_BOT_TOKEN kosong.",
                             "Isi TELEGRAM_BOT_TOKEN dari @BotFather."))
    elif not TOKEN_RE.match(token):
        checks.append(_check("telegram", "Alert Telegram", "warn", "Format TELEGRAM_BOT_TOKEN tidak sesuai (harus seperti 123456:ABC...).",
                             "Salin ulang token dari @BotFather tanpa spasi atau tanda kutip."))
    else:
        checks.append(_check("telegram", "Alert Telegram", "ok", "Token dan chat id terisi dengan format valid."))

    shopee = [settings.shopee_app_id, settings.shopee_app_secret]
    if any(shopee) and not all(shopee):
        checks.append(_check("affiliate", "Affiliate Shopee", "warn", "Kredensial Shopee terisi sebagian; link/pencarian affiliate tidak aktif.",
                             "Lengkapi SHOPEE_APP_ID dan SHOPEE_APP_SECRET (dari panel Open API portal affiliate Shopee)."))
    elif all(shopee):
        checks.append(_check("affiliate", "Affiliate Shopee", "ok", "App ID dan Secret terisi."))
    else:
        checks.append(_check("affiliate", "Affiliate Shopee", "info", "Belum dikonfigurasi (opsional; gratis setelah akun affiliate disetujui)."))

    if settings.piloterr_api_key:
        checks.append(_check("piloterr", "Piloterr (promo web)", "ok",
                             f"API key terisi; batas {settings.piloterr_daily_limit} panggilan/hari untuk menjaga kredit gratis."))
    else:
        checks.append(_check("piloterr", "Piloterr (promo web)", "info", "PILOTERR_API_KEY kosong; sumber promo web nonaktif."))

    if settings.checker_enabled:
        checks.append(_check("checker", "Pengecek harga", "ok", f"Aktif, interval {settings.checker_interval_seconds}s."))
    else:
        checks.append(_check("checker", "Pengecek harga", "info", "Nonaktif (CHECKER_ENABLED=false)."))

    n = errorlog.count()
    if n:
        checks.append(_check("errors", "Error server", "warn", f"{n} error tercatat sejak server start.",
                             "Lihat daftar recent_errors di bawah, atau log service di Railway (tab Deployments -> View logs)."))
    else:
        checks.append(_check("errors", "Error server", "ok", "Tidak ada error tercatat."))

    statuses = {c["status"] for c in checks}
    overall = "error" if "error" in statuses else "warn" if "warn" in statuses else "ok"
    return {"overall": overall, "platform": "railway" if on_railway() else "lokal",
            "checks": checks, "recent_errors": errorlog.recent()}
