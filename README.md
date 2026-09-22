# Teras Manis / Aurora Cafe POS & Management System

Sistem Kasir (Point of Sale) & Manajemen Operasional Cafe berbasis web responsif dengan backend FastAPI dan integrasi 41 modul operasional.

## Fitur Utama

- **Point of Sale (POS) Kilat**: Pencatatan pesanan cepat, modifikasi item (level gula, ukuran, topping), dan kalkulasi otomatis.
- **Multi-Payment**: Mendukung QRIS, Tunai dengan kalkulator kembalian otomatis, dan Transfer Bank.
- **Manajemen Meja (Table Layout)**: Visualisasi status meja real-time, gabung meja, dan kelola tagihan dine-in.
- **Inventori & Resep**: Pemotongan stok bahan otomatis berdasarkan resep menu yang terjual.
- **Shift Kasir & Absensi**: Pembukaan shift, rekonsiliasi kas harian, dan pencatatan kehadiran karyawan.
- **Master Data**: Pengaturan kategori, barang/menu, ukuran, topping, level gula, dan jabatan.
- **Kepatuhan Anti-Slop UI**: Desain responsif, kontras tinggi WCAG AAA, dan dukungan tema terang dan gelap.

## Struktur Direktori

```text
Cafe/
|-- backend/
|   |-- app/
|   |   |-- models/         # Pydantic & database models
|   |   |-- routers/        # API route handlers (auth, catalog, transactions, dll)
|   |   |-- static/         # Frontend HTML, CSS, JS, dan aset grafis
|   |   |-- main.py         # Entry point FastAPI & static server
|   |   `-- config.py       # Konfigurasi sistem
|   |-- data/               # Database SQLite
|   |-- Dockerfile          # Konfigurasi container untuk cloud deployment
|   |-- requirements.txt    # Dependensi Python
|   `-- run_server.bat      # Script peluncur lokal Windows
|-- Buka_Aplikasi_POS.bat   # Pintasan desktop peluncur sistem
`-- README.md
```

## Menjalankan Secara Lokal

1. Masuk ke direktori `backend`:
   ```bash
   cd backend
   ```
2. Pasang dependensi:
   ```bash
   pip install -r requirements.txt
   ```
3. Jalankan server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
4. Buka di browser: `http://localhost:8000`

## Menjalankan dengan Docker

```bash
cd backend
docker build -t terasmanis-pos .
docker run -p 8000:8000 terasmanis-pos
```
