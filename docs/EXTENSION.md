# Ekstensi Chrome

## Cara kerja

Ekstensi berjalan pada halaman produk Shopee dan TikTok Shop. Ketika
halaman dibuka, content script mengekstrak metadata produk (nama, harga,
gambar) dari DOM dan menampilkan widget melayang "Track price" di
kanan bawah.

Mengklik "Track price" mengirim produk ke background service worker,
yang meneruskan ke backend API. Harga tercatat sebagai titik baru dalam
riwayat harga produk.

## File

```
extension/
├── manifest.json         Manifes Manifest V3
├── background.js         Service worker: jembatan API, badge, notifikasi
├── content/
│   ├── shopee.js         Content script Shopee
│   └── tiktok.js         Content script TikTok Shop
├── popup/
│   ├── popup.html        Popup utama
│   ├── popup.css         Styling popup
│   ├── popup.js          Logika popup
│   ├── settings.html     Halaman pengaturan (options page)
│   └── settings.js       Logika pengaturan
└── icons/                Ikon ekstensi
```

## Fitur popup

- Daftar produk yang dipantau dengan harga saat ini, harga minimum, dan
  badge penurunan
- Pencarian produk (search)
- Grafik riwayat harga (sparkline)
- Set target harga via dialog
- Salin link affiliate ke clipboard
- Buka halaman produk saat mengklik nama produk
- Tombol refresh dan buka dokumentasi backend

## Pengaturan

Buka `chrome://extensions` lalu "Details" -> "Extension options" atau
klik ikon gear di popup.

| Pengaturan | Deskripsi |
|---|---|
| URL backend | Alamat server API (default http://localhost:8000) |
| API key | Dikirim sebagai header X-API-Key jika backend memproteksi |
| Ambang notifikasi | Persentase penurunan sebelum notifikasi |
| Buka produk saat klik | Membuka tautan produk di tab baru |

## Pesan background

`background.js` menangani pesan berikut:

| Type | Payload | Fungsi |
|---|---|---|
| TRACK_PRODUCT | product | Upsert produk + catat harga |
| IS_TRACKED | url | Cek apakah produk sudah dipantau |
| LIST_PRODUCTS | search | Daftar produk |
| PRODUCT_HISTORY | id | Riwayat harga |
| SET_TARGET / CLEAR_TARGET | id, price | Kelola target |
| GET_AFFILIATE | id | Generate link affiliate |
| GET_SETTINGS | - | Ambil pengaturan |

## Instalasi

1. Buka `chrome://extensions`
2. Aktifkan "Developer mode"
3. Klik "Load unpacked"
4. Pilih folder `extension/`
