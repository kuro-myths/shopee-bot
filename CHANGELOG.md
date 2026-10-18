# Changelog

## [0.3.0] - 2026-08-12

### Ditambahkan
- Web dashboard admin di `/dashboard` (overview, tabel produk, grafik riwayat harga)
- Endpoint agregasi statistik `/api/stats`
- Ringkasan riwayat harga per produk (`/api/products/{id}/summary`)
- Arsip/restore produk (soft delete) dan filter arsip dari daftar/export
- Endpoint prune riwayat harga dengan retention window
- Catatan (note) per produk + endpoint nota
- Pagination metadata pada listing, rate limit headers, CORS configurable
- Structured logging (JSON lines) dan retry dengan backoff untuk notifikasi
- Health check diperkaya (versi, schema version, uptime)
- Perintah bot baru: /price, /history, /restore, /settings, /prune, /note, /top, /recent
- Alias bahasa Indonesia pada bot, tombol buka produk, inline menu
- Ekstensi v1.1: polling alarm 15 menit, cooldown notifikasi, filter marketplace, tema light/dark, sorting, export CSV, tombol arsip/hapus, tes koneksi di pengaturan
- Suite test diperluas (160+ test backend, 13 test bot)

### Diperbaiki
- Pruning mempertahankan titik harga terbaru per produk (window function)
- Ordering riwayat pakai id monotonik (deterministik)
- Validasi harga negatif ditolak, target price positif
- Isolasi test dedupe dari modul lain
- Notifier tidak menelan kegagalan diam-diam — di-retry dengan backoff

## [0.2.0] - 2026-08-12

### Ditambahkan
- Fitur target harga per produk (set, hapus, deteksi tercapai)
- Background price checker dengan interval yang dapat dikonfigurasi
- Endpoint health check
- Export produk ke CSV dan JSON
- Search, filter marketplace, filter has-target, dan pagination pada daftar produk
- Autentikasi API key dan rate limiting
- Logging request
- Halaman pengaturan ekstensi (URL backend, API key, threshold)
- Badge ekstensi dengan jumlah produk yang dipantau
- Notifikasi browser saat harga turun
- Pencarian produk di popup ekstensi
- Modal onboarding pengguna baru
- Perintah bot baru: /search, /stats, /export, /ping, /target
- Menu inline keyboard pada bot
- Dockerfile backend dan bot, docker-compose, GitHub Actions CI
- Dokumentasi lengkap (API, arsitektur, deployment, kontribusi)
- Suite test (58 test backend + 5 test bot)

### Diperbaiki
- Deteksi penurunan harga membandingkan dengan minimum sebelumnya
- Parser harga mendukung format desimal dan ribuan
- Kontrak listing API disesuaikan ke envelope ter-paginasi

## [0.1.0] - 2026-08-12

### Ditambahkan
- Ekstensi Chrome (Manifest V3) untuk Shopee dan TikTok Shop
- Backend FastAPI dengan SQLite
- Deteksi penurunan harga dengan notifikasi Telegram
- Integrasi affiliate Shopee AMS dan TikTok Shop Partner API
- Bot Telegram dasar (/track, /list, /untrack)
- README dua bahasa (EN/ID)
