# Referensi API

Base URL: `http://localhost:8000`
Dokumentasi interaktif: `/docs` (Swagger UI)

## Autentikasi

Jika `API_KEY` diset di environment, semua endpoint (kecuali `/health`
dan `/docs`) mengharuskan header:

```
X-API-Key: <api_key>
```

Alternatif: parameter query `?token=<api_key>`.

## Produk

### POST /api/products

Membuat atau memperbarui produk (upsert berdasarkan URL) dan mencatat
titik harga.

```json
{
  "url": "https://shopee.co.id/example-i.123.456",
  "name": "Contoh Produk",
  "marketplace": "shopee",
  "image": "https://...",
  "current_price": 100000
}
```

Response (200): objek produk lengkap dengan `min_price`, `max_price`,
`target_price`, dan `target_reached`.

### GET /api/products

Daftar produk dengan search, filter, dan pagination.

| Parameter | Tipe | Deskripsi |
|---|---|---|
| `search` | string | Cari berdasarkan nama atau URL |
| `marketplace` | string | `shopee` atau `tiktok` |
| `has_target` | bool | Hanya produk dengan target |
| `page` | int | Nomor halaman (default 1) |
| `page_size` | int | Ukuran halaman (default 50, max 200) |

Response:

```json
{
  "products": [...],
  "total": 12,
  "page": 1,
  "page_size": 50,
  "pages": 1,
  "has_next": false,
  "has_prev": false
}
```

Semua response juga menyertakan header rate limit:
`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.

### GET /api/products/{id}

Ambil satu produk.

### GET /api/products/{id}/history

Riwayat harga dalam urutan kronologis. Parameter query `limit` (default 500, max 5000).

### GET /api/products/{id}/summary

Ringkasan riwayat: `min`, `max`, `avg`, `count`.

### PUT /api/products/{id}/target

Set target harga. Body: `{"target_price": 45000}`

### DELETE /api/products/{id}/target

Hapus target harga.

### PUT /api/products/{id}/note

Simpan catatan produk. Body: `{"note": "beli buat hadiah"}`

### POST /api/products/{id}/archive

Arsipkan produk (soft delete — tidak muncul di daftar/export).

### POST /api/products/{id}/restore

Kembalikan produk yang diarsipkan.

### POST /api/products/prune

Bersihkan riwayat harga lebih tua dari `older_than_days` (default 90).
Mempertahankan titik harga terbaru per produk.

### POST /api/products/{id}/affiliate

Generate link affiliate. Response:

```json
{
  "url": "https://s.shopee.co.id/...",
  "source": "shopee_api",
  "note": "..."
}
```

Tanpa kredensial affiliate, `source` bernilai `original` dan `url`
adalah URL produk asli.

### DELETE /api/products/{id}

Hentikan pemantauan produk (menghapus riwayat harga terkait).

## Lainnya

### GET /api/stats

Statistik agregat: total produk, produk dengan target, produk di bawah
minimum, sebaran marketplace.

### GET /health

Status kesehatan: database connectivity, uptime, versi, dan schema version.

### GET /api/products/export/{fmt}

Export produk aktif (non-arsip) sebagai `csv` atau `json`.

## Dashboard

Dashboard web di `http://localhost:8000/dashboard` (overview, tabel
produk, grafik riwayat harga, pengaturan server).
