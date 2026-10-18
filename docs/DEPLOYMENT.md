# Deployment

## Lokal (development)

```bash
# 1. Backend
cd backend
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env   # isi sesuai kebutuhan
uvicorn app.main:app --reload --port 8000

# 2. Ekstensi Chrome
# Buka chrome://extensions -> Developer mode -> Load unpacked -> pilih extension/

# 3. Bot Telegram (opsional)
cd bot
pip install -r requirements.txt
TELEGRAM_BOT_TOKEN=xxx python bot.py
```

## Docker

```bash
# Build & jalankan backend
docker compose up -d --build

# Hentikan
docker compose down
```

Volume `./data` menyimpan database SQLite agar tetap persisten antar
restart.

## Production (VPS)

1. Clone repository dan buat file `.env` di `backend/`
2. Set variabel wajib: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
3. Set `API_KEY` untuk melindungi endpoint publik
4. Jalankan dengan Docker atau systemd

Contoh unit systemd (`/etc/systemd/system/pricedrop.service`):

```ini
[Unit]
Description=PriceDrop Tracker API
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/price-drop-tracker/backend
EnvironmentFile=/opt/price-drop-tracker/backend/.env
ExecStart=/usr/local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

## CI/CD

`.github/workflows/ci.yml` menjalankan test backend pada setiap push.
`.github/workflows/docker.yml` membangun dan mempublikasikan image
Docker ke GHCR ketika tag `v*` di-push.

## Variabel environment backend

| Variabel | Default | Deskripsi |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./pricedrop.db` | Lokasi database |
| `TELEGRAM_BOT_TOKEN` | - | Token bot untuk notifikasi |
| `TELEGRAM_CHAT_ID` | - | Chat target notifikasi |
| `DROP_THRESHOLD_PCT` | `5` | Ambang penurunan harga |
| `CHECKER_ENABLED` | `true` | Aktifkan background checker |
| `CHECKER_INTERVAL_SECONDS` | `21600` | Interval cek ulang (6 jam) |
| `API_KEY` | - | Proteksi endpoint |
| `RATE_LIMIT_REQUESTS` | `60` | Maksimal request per window |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Window rate limit |
| `CORS_ORIGINS` | `*` | Origin yang diizinkan (pisah koma) |
| `LOG_LEVEL` | `INFO` | Level log |
| `LOG_FORMAT` | `text` | `text` atau `json` (structured logging) |
| `NOTIFY_RETRIES` | `3` | Retry notifikasi Telegram |
| `NOTIFY_BACKOFF` | `0.5` | Backoff awal retry (detik) |
| `NOTIFY_COOLDOWN_SECONDS` | `86400` | Cooldown notifikasi per produk |
| `DEDUPE_WINDOW_SECONDS` | `3600` | Jendela dedupe harga identik |
| `SHOPEE_APP_ID` | - | Kredensial affiliate Shopee |
| `SHOPEE_APP_SECRET` | - | Kredensial affiliate Shopee |
| `SHOPEE_PARTNER_ID` | - | Partner ID Shopee |
| `TIKTOK_APP_KEY` | - | Kredensial affiliate TikTok |
| `TIKTOK_APP_SECRET` | - | Kredensial affiliate TikTok |
| `TIKTOK_SHOP_ID` | - | Shop ID TikTok |
