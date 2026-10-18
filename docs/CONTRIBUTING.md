# Kontribusi

Terima kasih sudah ingin berkontribusi ke PriceDrop Tracker.

## Setup development

```bash
git clone <repo-url>
cd price-drop-tracker
make install     # install backend + dev dependencies
make test        # jalankan test suite
```

## Alur kerja

1. Buat branch fitur: `git checkout -b feat/nama-fitur`
2. Kerjakan perubahan dengan commit kecil dan deskriptif
3. Jalankan test: `make test`
4. Buat pull request ke branch `main`

## Panduan commit

Gunakan prefiks konvensional:

- `feat:` fitur baru
- `fix:` perbaikan bug
- `test:` penambahan test
- `docs:` perubahan dokumentasi
- `refactor:` perubahan struktur tanpa mengubah perilaku
- `build:` perubahan build/deployment
- `ci:` perubahan pipeline CI
- `style:` perubahan format/style
- `chore:` tugas rutin

Contoh: `feat: add target price endpoint`

## Menjalankan test

```bash
cd backend
CHECKER_ENABLED=false python -m pytest tests/
```

Pastikan semua test lulus sebelum mengirim PR. Tambahkan test untuk
fitur baru.

## Gaya kode

- Python: ikuti PEP 8, gunakan type hints
- JavaScript: ikuti gaya yang ada di file terkait
- Tulis docstring singkat pada fungsi publik
