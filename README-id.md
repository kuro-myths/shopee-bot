# PriceDrop Tracker

> [English](README.md)

Pantau harga produk di Shopee dan TikTok Shop, dapatkan notifikasi saat harga turun, dan buat link affiliate — semua dari ekstensi Chrome yang didukung API kecil di belakangnya.

## Kenapa

Harga di marketplace bergerak terus-menerus, terutama saat flash sale. Daripada buka halaman produk tiap hari, biarkan ekstensi browser mencatat harga setiap kali kamu membuka halaman produk, lalu dapatkan alert Telegram begitu harganya turun di bawah harga terendah yang pernah tercatat.

## Fitur

- Ekstensi Chrome (Manifest V3) yang membaca harga langsung dari halaman yang sedang kamu buka — tanpa scraping di sisi server, sehingga aman dari proteksi anti-bot
- Mendukung halaman produk Shopee dan TikTok Shop
- Track sekali klik lewat widget melayang di setiap halaman produk
- Riwayat harga tersimpan per produk, lengkap dengan grafik garis di popup dan web dashboard
- Deteksi penurunan harga: alert ketika harga turun melebihi ambang batas yang bisa diatur dari harga terendah sepanjang masa
- Target harga per produk dengan notifikasi saat tercapai
- Bot Telegram dengan perintah `/track`, `/list`, `/search`, `/target`, `/stats`, `/price`, `/history`, `/note`, `/archive`, `/restore`, `/prune`, dan `/untrack`, plus menu inline dan alias bahasa Indonesia
- Pembuatan link affiliate lewat Shopee AMS Open API dan TikTok Shop Partner API resmi (fallback ke URL asli jika kredensial belum diatur)
- Pencarian produk, filter marketplace, sorting, target harga, catatan, arsip (soft delete), export CSV/JSON, dan web dashboard di `/dashboard` dengan grafik harga
- Background checker harga, autentikasi API key opsional, rate limiting dengan header respons, dan structured logging
- Cooldown notifikasi per produk dan retry dengan backoff untuk alert Telegram
- Dokumentasi dua bahasa: [English](README.md) dan [Bahasa Indonesia](README-id.md)

## Arsitektur

```
Ekstensi Chrome  ──►  Backend FastAPI  ──►  SQLite
 (baca harga)          (riwayat, drop)      (produk + riwayat harga)
        │                       │
        │                       └──► Bot Telegram (alert harga turun)
        └──► popup: daftar, grafik, link affiliate
```

## Struktur project

```
price-drop-tracker/
├── extension/          Ekstensi Chrome (Manifest V3)
│   ├── manifest.json
│   ├── background.js   jembatan API + penanganan pesan
│   ├── content/        content scripts (shopee.js, tiktok.js)
│   └── popup/          UI popup ekstensi
├── backend/            Aplikasi FastAPI
│   ├── app/
│   │   ├── main.py     entrypoint aplikasi
│   │   ├── routers/    endpoint produk & harga
│   │   └── services/   detektor drop, notifier, klien affiliate
│   └── requirements.txt
└── bot/                Bot Telegram
    ├── bot.py
    └── requirements.txt
```

## Memulai

### 1. Jalankan backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env      # opsional: tambahkan kredensial Telegram + affiliate
uvicorn app.main:app --port 8000
```

API tersedia di `http://localhost:8000` dengan dokumentasi interaktif di `/docs`.

### 2. Pasang ekstensi

1. Buka `chrome://extensions`
2. Aktifkan "Developer mode" (kanan atas)
3. Klik "Load unpacked" dan pilih folder `extension/`

Buka halaman produk apa pun di Shopee atau TikTok Shop. Tombol "Track price" muncul di kanan bawah — klik untuk mulai memantau.

### 3. Aktifkan alert Telegram (opsional)

Buat bot dengan [@BotFather](https://t.me/BotFather), lalu isi di `backend/.env`:

```
TELEGRAM_BOT_TOKEN=token_bot_kamu
TELEGRAM_CHAT_ID=id_chat_kamu
```

Ketika harga produk yang dipantau turun melebihi `DROP_THRESHOLD_PCT` (default 5) dari harga terendah sebelumnya, bot mengirim alert.

Untuk menjalankan bot interaktif:

```bash
cd bot
pip install -r requirements.txt
TELEGRAM_BOT_TOKEN=token_bot_kamu python bot.py
```

### 4. Aktifkan link affiliate (opsional)

**Shopee:** daftar di [Shopee Affiliate Program](https://affiliate.shopee.co.id), ajukan akses Open Platform, lalu isi di `backend/.env`:

```
SHOPEE_APP_ID=...
SHOPEE_APP_SECRET=...
SHOPEE_PARTNER_ID=...
```

**TikTok Shop:** daftar sebagai developer aplikasi affiliate di [TikTok Shop Partner Center](https://partner.tiktokshop.com), lalu isi:

```
TIKTOK_APP_KEY=...
TIKTOK_APP_SECRET=...
TIKTOK_SHOP_ID=...
```

Tanpa kredensial, tombol "Link affiliate" mengembalikan URL produk asli.

## API

| Metode | Path | Deskripsi |
|---|---|---|
| POST | `/api/products` | Buat/perbarui produk, catat harga, deteksi drop |
| GET | `/api/products` | Daftar produk (search, filter, pagination) |
| GET | `/api/products/{id}` | Ambil satu produk |
| GET | `/api/products/{id}/history` | Riwayat harga (dengan limit) |
| GET | `/api/products/{id}/summary` | Min/max/avg/count riwayat |
| PUT | `/api/products/{id}/target` | Set target harga |
| DELETE | `/api/products/{id}/target` | Hapus target harga |
| PUT | `/api/products/{id}/note` | Tambahkan catatan pada produk |
| POST | `/api/products/{id}/affiliate` | Buat link affiliate |
| POST | `/api/products/{id}/archive` | Arsipkan produk (soft delete) |
| POST | `/api/products/{id}/restore` | Pulihkan produk yang diarsipkan |
| POST | `/api/products/prune` | Bersihkan riwayat harga lama |
| GET | `/api/stats` | Statistik agregat pemantauan |
| GET | `/api/products/export/{fmt}` | Export produk aktif (CSV/JSON) |
| DELETE | `/api/products/{id}` | Hapus produk permanen |
| GET | `/health` | Health check dengan versi dan uptime |

## Roadmap

- Kanal notifikasi lain (email, Discord)
- Ekspansi marketplace (Tokopedia, Lazada)
- Kebijakan pemangkasan / retensi riwayat harga
- Dukungan multi-pengguna

## Lisensi

MIT
