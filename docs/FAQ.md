# FAQ

## Harga tidak terbaca di halaman produk?

Content script mencoba beberapa cara: meta tags OpenGraph, elemen dengan
class "price", dan teks halaman. Jika harga tidak terbaca, pastikan
halaman sudah selesai dimuat lalu buka kembali widget. Beberapa halaman
Shopee merender harga setelah interaksi (pilih variasi produk dulu).

## Backend tidak merespons di popup?

1. Pastikan backend berjalan: `uvicorn app.main:app --port 8000`
2. Periksa URL backend di pengaturan ekstensi (default
   `http://localhost:8000`)
3. Jika backend memakai API key, isi juga di pengaturan ekstensi

## Notifikasi Telegram tidak terkirim?

Notifikasi membutuhkan `TELEGRAM_BOT_TOKEN` dan `TELEGRAM_CHAT_ID` di
`backend/.env`. Token didapat dari @BotFather, dan chat ID bisa didapat
dengan mengirim pesan ke bot lalu melihat update via getUpdates.

## Link affiliate tetap URL asli?

Backend mengembalikan URL asli ketika kredensial affiliate belum
dikonfigurasi. Daftar di Shopee Affiliate Program / TikTok Shop Partner
Center lalu isi kredensial di `backend/.env` (lihat DEPLOYMENT.md).

## Apakah ini melanggar ToS marketplace?

Ekstensi membaca harga dari halaman yang sedang kamu buka sendiri, tanpa
scraping massal dari server. Ini jauh lebih etis daripada crawler.
Tetap gunakan secara wajar dan patuhi ToS masing-masing platform.

## Bagaimana cara menghapus semua data?

Hapus file `backend/pricedrop.db`, lalu restart backend. Tabel akan
dibuat ulang otomatis.
