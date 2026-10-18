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
   Root Directory `bot`, Variables: `TELEGRAM_BOT_TOKEN`, `BACKEND_URL` (domain dari langkah 3), dan `API_KEY` (sama dengan backend, jika backend memakainya).
7. Ekstensi Chrome: Load unpacked folder `extension/`, arahkan URL backend ke domain Railway.

Cek: buka `https://<domain-railway>/health` → harus `{"status":"ok"}`.

## Deteksi error & troubleshooting

Aplikasi punya pemeriksa konfigurasi sendiri:

- **Dashboard → Pengaturan → Diagnostik**: daftar pemeriksaan (database, volume, API key, Telegram, affiliate, error server) lengkap dengan saran perbaikan.
- **`GET /api/diagnostics`** (butuh header `X-API-Key` jika `API_KEY` diisi): data yang sama dalam JSON.
- **Log deploy Railway**: saat startup, setiap masalah tercetak dengan awalan `DIAGNOSTIK [warn|error]` beserta "Perbaikan: ...".

| Gejala | Penyebab umum | Perbaikan |
|---|---|---|
| Deploy gagal di healthcheck | Service belum listen di `$PORT` | Pastikan memakai `Dockerfile` repo ini (sudah membaca `$PORT`); cek log build |
| Dashboard "Perlu API key" | `API_KEY` diisi di Railway | Dashboard → Pengaturan → isi API key yang sama → Simpan |
| Bot Telegram: "Backend menolak: API_KEY salah" | Service bot tidak punya `API_KEY` | Tambahkan variable `API_KEY` yang sama di service bot |
| Diagnostik: "Penyimpanan permanen" peringatan | Volume belum dipasang | Volumes → New Volume → mount path `/data` |
| Diagnostik: database ERROR | `/data` tidak bisa ditulis | Pasang Volume `/data` atau perbaiki `DATABASE_URL` (`sqlite:////data/pricedrop.db`) |
| Dashboard "Offline" | Domain salah / deploy mati | Cek Deployments → View logs, lalu buka `/health` |
| "Dibatasi" (429) | Lebih dari 60 request/menit | Tunggu semenit, atau naikkan `RATE_LIMIT_REQUESTS` |
