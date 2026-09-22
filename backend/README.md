# Aurora Cafe POS - Backend & Database Terintegrasi (41 Modul)

Backend API berbasis **FastAPI** dan Database Relasional (**SQLite + MySQL Script**) yang menyinkronkan seluruh 41 modul POS Cafe dari file referensi di folder `d:\Aurora\Cafe`.

---

## 🌟 Fitur Utama & Sinkronisasi

1. **Auto-Deduct Stok Berbasis Resep (BOM)**:
   - Setiap transaksi checkout kasir otomatis memotong stok bahan baku berdasarkan resep produk secara real-time (contoh: 1 Kopi Susu memotong 18g biji kopi, 150ml susu, 25ml gula aren).
2. **Rekonsiliasi Shift Kasir**:
   - Membuka shift dengan modal kas awal, menghitung kas masuk riil vs kas yang diharapkan (*expected cash*), serta mencatat selisih (*variance*) saat tutup shift.
3. **Manajemen Denah Meja Interaktif**:
   - Denah meja (koordinat X & Y), kapasitas, grup area (Indoor AC, Outdoor Garden), dan status meja otomatis beralih ke `occupied` saat transaksi dibuat.
4. **Integrasi Pembayaran Lengkap**:
   - Tunai (dengan hitung kembalian otomatis), QRIS dinamis (EMVCo payload simulation), Transfer Bank, dan GoFood.
5. **Multi-Outlet & Multi-Terminal Sync**:
   - Dukungan multi cabang, pengiriman & penerimaan transfer stok antar cabang, serta endpoint sinkronisasi `/api/sync/pull` dan `/api/sync/push`.
6. **Ekspor MySQL / MariaDB**:
   - Tersedia file `schema_mysql.sql` dan `seed_mysql.sql` yang siap di-import langsung ke Navicat atau phpMyAdmin.

---

## 📁 Pemetaan 41 Modul ke Sistem

| No | Modul / File TXT | Tabel Database | Endpoint API Utama |
|---|---|---|---|
| 1 | `Billing.txt` | `billing_plans` | `GET /api/auth/billing` |
| 2 | `Brand.txt` | `brands` | `GET /api/auth/brands` |
| 3 | `Bundle package.txt` | `bundle_packages`, `bundle_items` | `GET/POST /api/catalog/bundles` |
| 4 | `Dashboard.txt` | Analitik Agregat | `GET /api/reports/dashboard` |
| 5 | `Employee slot.txt` | `employee_slots` | Terintegrasi di modul Auth |
| 6 | `Ingredienty kategori.txt` | `ingredient_categories` | `GET /api/inventory/categories` |
| 7 | `Invoice.txt` | `invoices` | `GET /api/pos/invoices` |
| 8 | `Item library.txt` | `items` | `GET/POST /api/catalog/items` |
| 9 | `Kategori.txt` | `categories` | `GET/POST /api/catalog/categories` |
| 10 | `Konsumen list.txt` | `customers` | `GET/POST /api/promo/customers` |
| 11 | `Moke order.txt` | `mobile_orders` | `GET/POST /api/integrations/orders/mobile` |
| 12 | `PO.txt` | `purchase_orders`, `purchase_order_items` | `GET/POST/PUT /api/inventory/purchase-orders` |
| 13 | `Partner.txt` | `partners` | `GET /api/integrations/partners` |
| 14 | `Promo.txt` | `promos` | `GET/POST /api/promo/promos` |
| 15 | `Sales type.txt` | `sales_types` | `GET /api/pos/sales-types` |
| 16 | `Sales.txt` | `transactions` | `GET /api/reports/sales` |
| 17 | `Shift.txt` | `shifts` | `GET/POST /api/shifts/current`, `/open`, `/close` |
| 18 | `Transaksi.txt` | `transactions`, `transaction_items` | `GET /api/pos/transactions`, `POST /api/pos/checkout` |
| 19 | `adjusment.txt` | `stock_adjustments`, `stock_adjustment_items` | `POST /api/inventory/adjustments` |
| 20 | `akun.txt` | `users` | Terintegrasi di modul Auth |
| 21 | `bank akun.txt` | `bank_accounts` | `GET /api/finance/bank-accounts` |
| 22 | `campaign.txt` | `campaigns` | `GET /api/promo/campaigns` |
| 23 | `diskon.txt` | `discounts` | `GET/POST /api/promo/discounts` |
| 24 | `employee akses.txt` | `roles` | `GET /api/auth/roles` |
| 25 | `go food.txt` | `gofood_integrations` | `GET /api/integrations/gofood` |
| 26 | `gratuity.txt` | `gratuities` | `GET/POST /api/finance/gratuities` |
| 27 | `ingredient library.txt`| `ingredients`, `outlet_ingredient_stocks` | `GET/POST /api/inventory/ingredients` |
| 28 | `modifikasi.txt` | `modifiers`, `modifier_options` | `GET/POST /api/catalog/modifiers` |
| 29 | `outlet.txt` | `outlets` | `GET/POST /api/auth/outlets` |
| 30 | `pajak.txt` | `taxes` | `GET/POST /api/finance/taxes` |
| 31 | `pin akses.txt` | `employees` (PIN) | `POST /api/auth/employees/verify-pin` |
| 32 | `qris config.txt` | `qris_configs` | `GET /api/finance/qris/config` |
| 33 | `qris.txt` | `qris_transactions` | `POST /api/finance/qris/generate`, `/check` |
| 34 | `recipes.txt` | `recipes` | `GET/POST /api/inventory/recipes` |
| 35 | `setting.txt` | `settings` | Terintegrasi di Database & Outlet |
| 36 | `summary.txt` | Ringkasan Penjualan & Keuangan | `GET /api/reports/sales` |
| 37 | `supplier.txt` | `suppliers` | `GET /api/inventory/suppliers` |
| 38 | `table grup.txt` | `table_groups` | `GET /api/tables/groups` |
| 39 | `table maps.txt` | `tables` (pos_x, pos_y) | `GET /api/tables`, `PUT /api/tables/{id}/layout` |
| 40 | `table report.txt` | Laporan Utilisasi & Revenue Meja | `GET /api/reports/tables` |
| 41 | `transfer.txt` | `stock_transfers`, `stock_transfer_items` | `POST /api/inventory/transfers`, `/receive` |

---

## 🚀 Cara Menjalankan Backend

### Cara 1: Menggunakan Script Batch Windows (Satu Klik)
Cukup jalankan file:
```cmd
d:\Aurora\Cafe\backend\run_server.bat
```

### Cara 2: Menggunakan Terminal Command (`uv`)
```powershell
cd d:\Aurora\Cafe\backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Setelah server aktif, Anda dapat membuka:
- **Swagger UI Interaktif**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Dokumentasi API**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🛠️ Perintah Berguna Lainnya

1. **Menjalankan Ulang Tes Integrasi Otomatis**:
   ```powershell
   uv run python scripts/test_api.py
   ```
2. **Mengisi Ulang Data Awal (Seed Data)**:
   ```powershell
   uv run python scripts/seed_data.py
   ```
3. **Ekspor Ulang ke Format MySQL / Navicat**:
   ```powershell
   uv run python scripts/export_mysql.py
   ```
   Akan memperbarui file `schema_mysql.sql` dan `seed_mysql.sql`.
