# Keamanan

## Model ancaman

PriceDrop Tracker berjalan sebagai aplikasi personal/self-hosted.
Pengguna meng-host backend sendiri dan menghubungkan ekstensi Chrome ke
backend tersebut.

## Proteksi yang tersedia

### API key

Set `API_KEY` di environment untuk mewajibkan autentikasi pada semua
endpoint kecuali `/health` dan `/docs`. Kirim key via header
`X-API-Key` atau parameter query `token`.

### Rate limiting

Middleware keamanan membatasi 60 request per 60 detik per klien (IP
atau API key). Melampaui batas menghasilkan `429 Too Many Requests`
dengan header `X-RateLimit-Limit`, `X-RateLimit-Remaining`, dan
`X-RateLimit-Reset`. Ambang batas dapat disesuaikan lewat
`RATE_LIMIT_REQUESTS` dan `RATE_LIMIT_WINDOW_SECONDS`.

### Parameterized SQL

Semua query database menggunakan parameter binding — tidak ada
concatenation string, sehingga aman dari SQL injection.

### CORS

CORS diatur ke `*` untuk kemudahan development. Jika backend di-publish
ke internet, batasi `allow_origins` sesuai domain ekstensi/klien kamu.

## Praktik yang disarankan

1. Selalu set `API_KEY` saat backend diakses dari luar localhost
2. Simpan kredensial affiliate di environment, bukan di source code
3. Jangan commit file `.env`
4. Jalankan di balik HTTPS (reverse proxy seperti Caddy/Nginx) di
   production
5. Update dependensi secara berkala
6. Set `CORS_ORIGINS` ke daftar domain eksplisit (bukan `*`) saat
   backend diakses publik
7. Gunakan `LOG_FORMAT=json` untuk audit log yang mudah diparsing

## Pelaporan kerentanan

Laporkan kerentanan melalui issue repository dengan label `security`.
Jangan mengungkapkan detail sebelum ada perbaikan.
