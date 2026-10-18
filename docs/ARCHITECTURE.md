# Arsitektur

Dokumen ini menjelaskan komponen PriceDrop Tracker dan bagaimana mereka
saling terhubung.

## Komponen

| Komponen | Lokasi | Peran |
|---|---|---|
| Ekstensi Chrome | `extension/` | Membaca harga dari halaman produk, menampilkan widget track, popup manajemen |
| Backend API | `backend/` | Menyimpan produk & riwayat harga, deteksi penurunan, generate link affiliate |
| Bot Telegram | `bot/` | Perintah interaktif dan notifikasi harga turun |
| SQLite | `backend/pricedrop.db` | Penyimpanan persisten |

## Alur data

1. Pengguna membuka halaman produk di Shopee/TikTok Shop
2. Content script mengekstrak nama, harga, dan gambar produk
3. Pengguna klik "Track price" pada widget melayang
4. Background service worker mengirim produk ke `POST /api/products`
5. Backend menyimpan produk (upsert by URL) dan mencatat titik harga
6. Backend membandingkan harga baru dengan harga minimum historis
7. Jika turun melebihi threshold, notifikasi dikirim via Telegram
8. Popup ekstensi menampilkan daftar, grafik riwayat, dan link affiliate

## Keputusan desain

### Harga diambil client-side (bukan server-side scraping)

Marketplace seperti Shopee memiliki proteksi anti-bot yang agresif
(Cloudflare, captcha, rate limiting). Dengan membaca harga langsung dari
halaman yang sedang dibuka pengguna, ekstensi memakai sesi dan IP
residential pengguna sehingga tidak terblokir. Backend tetap menyediakan
`fetcher.py` untuk pengecekan ulang best-effort via meta tags.

### SQLite tanpa ORM

Database memakai `sqlite3` dari standard library untuk menghindari
dependency tambahan. Skema kecil dan stabil sehingga tidak membutuhkan
ORM. Migrasi ringan dilakukan dengan memeriksa kolom yang ada.

### Komunikasi ekstensi-backend via HTTP JSON

Ekstensi berbicara ke backend melalui REST API sederhana. Endpoint
ditentukan di `background.js` (sisi klien) dan `routers/products.py`
(sisi server). API key opsional melindungi endpoint ketika backend
dipublikasikan.

## Struktur backend

```
backend/
├── app/
│   ├── main.py              entrypoint FastAPI + lifespan
│   ├── config.py            konfigurasi dari environment
│   ├── db.py                koneksi & migrasi SQLite
│   ├── models.py            skema Pydantic
│   ├── routers/
│   │   └── products.py      endpoint produk
│   ├── services/
│   │   ├── affiliate.py     klien API affiliate
│   │   ├── checker.py       scheduler background
│   │   ├── detector.py      logika deteksi penurunan harga
│   │   ├── export.py        serialisasi CSV/JSON
│   │   ├── fetcher.py       pembaca harga best-effort
│   │   ├── filters.py       search/filter/pagination
│   │   ├── health.py        health check
│   │   ├── notifier.py      pengirim notifikasi Telegram
│   │   └── targets.py       logika target harga
│   └── middleware/
│       ├── logging.py       logging request
│       └── security.py      API key + rate limiting
└── tests/                   suite pytest
```
