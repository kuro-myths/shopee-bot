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

## Deploy otomatis lewat GitHub Actions

Workflow `.github/workflows/deploy.yml` berjalan di setiap push ke `main`:
tes -> `railway up` -> `scripts/check_deploy.py` (menunggu `/health`, lalu membaca `/api/diagnostics`).
Jika ada error, run ditandai gagal, penyebab + saran perbaikan tampil di ringkasan run, dan 150 baris log Railway dicetak.
`monitor.yml` mengecek aplikasi tiap 30 menit; jika gagal, GitHub mengirim email.

Setup satu kali di GitHub: **Settings -> Secrets and variables -> Actions**

| Nama | Jenis | Isi |
|---|---|---|
| `RAILWAY_TOKEN` | Secret (wajib) | Railway -> Project -> Settings -> Tokens -> Create Project Token |
| `APP_API_KEY` | Secret | Sama dengan variable `API_KEY` di Railway (jika dipakai) |
| `RAILWAY_SERVICE` | Variable | Nama service di Railway (default `shopee-bot`) |
| `RAILWAY_URL` | Variable | Mis. `https://xxx.up.railway.app` (jika kosong dicari otomatis) |

Prasyarat di Railway: project + service sudah dibuat sekali (langkah 1-5 di atas), karena CLI hanya
mengirim kode ke service yang sudah ada. Setelah itu deploy berikutnya otomatis. Bisa juga dijalankan
manual: tab **Actions -> Deploy to Railway -> Run workflow**.

Cek lokal terhadap server mana pun:

    python scripts/check_deploy.py --url https://<domain> --api-key <API_KEY>
