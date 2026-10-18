# Deploy ke Railway

1. Push folder ini ke repo `kuro-myths/shopee-bot` (branch `main`).
2. Railway → **New Project → Deploy from GitHub repo** → pilih `shopee-bot`.
   Railway membaca `railway.json` + `Dockerfile` dan memakai `/health` sebagai healthcheck.
3. **Settings → Networking → Generate Domain** → dapat URL publik.
4. **Volumes → New Volume**, mount path `/data` (supaya database SQLite tidak hilang saat redeploy).
5. **Variables** (sesuai kebutuhan):
   - `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (dari @BotFather)
   - `API_KEY` (disarankan, karena URL publik)
   - `SHOPEE_APP_ID`, `SHOPEE_APP_SECRET`, `SHOPEE_PARTNER_ID` (opsional, link affiliate)
6. Bot Telegram interaktif = service kedua: **New Service → repo yang sama**,
   Root Directory `bot`, Variables: `TELEGRAM_BOT_TOKEN` + `BACKEND_URL` (domain dari langkah 3).
7. Ekstensi Chrome: Load unpacked folder `extension/`, arahkan URL backend ke domain Railway.

Cek: buka `https://<domain-railway>/health` → harus `{"status":"ok"}`.
