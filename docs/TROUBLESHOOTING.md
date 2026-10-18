# Troubleshooting

## Port 8000 sudah terpakai

```bash
# Windows (netstat + taskkill)
netstat -ano | findstr :8000
taskkill /F /PID <pid>
```

Ulangi `uvicorn app.main:app --port 8000`.

## Ekstensi tidak muncul di chrome://extensions

Pastikan manifest.json valid (JSON). Klik "Load unpacked" dan pilih
folder `extension/` (bukan subfolder). Aktifkan Developer mode dulu.

## Badge menampilkan 0 padahal ada produk

Badge direfresh saat ekstensi aktif dan backend terjangkau. Buka popup
sekali untuk memaksa refresh, atau restart browser jika badge macet.

## Rate limit 429

Default: 60 request per menit per klien. Naikkan lewat env:

```
RATE_LIMIT_REQUESTS=600
```

## Database error "database is locked"

SQLite mengunci file saat ada penulisan bersamaan. Pastikan hanya satu
proses backend yang berjalan. Untuk production, jalankan lewat Docker
dengan volume tunggal.

## Grafik history kosong

Butuh minimal 2 titik harga. Buka halaman produk beberapa kali dengan
harga berbeda, atau tunggu background checker (default tiap 6 jam).

## Bot tidak merespons

1. Cek token: `/ping` dari bot membutuhkan backend aktif
2. Jalankan `python bot.py` di folder `bot/`
3. Pastikan `BACKEND_URL` menunjuk ke backend yang benar
