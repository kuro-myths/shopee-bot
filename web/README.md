# Web Dashboard

Dashboard admin untuk PriceDrop Tracker. Disajikan otomatis oleh backend
di `/dashboard` — jalankan backend lalu buka `http://localhost:8000/dashboard`.

## Fitur

- Ringkasan: total produk, produk dengan target, produk di bawah minimum,
  rata-rata diskon
- Tabel produk dengan pencarian dan filter marketplace
- Grafik riwayat harga per produk (klik baris produk)
- Panel informasi server (status, database, uptime)

## Development

Dashboard adalah HTML/CSS/JS murni tanpa build step. Edit file di folder
ini, refresh browser, selesai.

- `index.html` — struktur halaman
- `styles.css` — styling dark theme
- `api.js` — klien API backend
- `app.js` — logika tampilan
