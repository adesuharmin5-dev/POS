import sqlite3
import datetime
import os
import sys
from pathlib import Path

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import get_db_connection, init_db

def run_seed():
    print("Initializing tables...")
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if already seeded
    cursor.execute("SELECT COUNT(*) AS cnt FROM brands")
    if cursor.fetchone()["cnt"] > 0:
        print("Database already contains data. Skipping duplicate seeding.")
        conn.close()
        return

    print("Seeding demo data for 41 Aurora Cafe modules...")

    # 1. Brands & Outlets
    cursor.execute("""
        INSERT INTO brands (name, logo, description)
        VALUES ('Aurora Coffee & Roastery', '/assets/logo.png', 'Specialty coffee & cozy work cafe')
    """)
    brand_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO outlets (brand_id, name, address, phone, email)
        VALUES 
        (?, 'Aurora Cafe - Flagship Pusat', 'Jl. R.E. Martadinata No. 45, Bandung', '022-7201234', 'martadinata@auroracafe.id'),
        (?, 'Aurora Cafe - Express Stasiun', 'Stasiun Hall Selatan No. 12, Bandung', '022-7205678', 'stasiun@auroracafe.id')
    """, (brand_id, brand_id))
    outlet1_id = 1
    outlet2_id = 2

    # Settings & Billing
    cursor.execute("""
        INSERT INTO settings (outlet_id, setting_key, setting_value, description)
        VALUES 
        (?, 'receipt_footer', 'Terima kasih atas kunjungan Anda! Follow IG: @auroracafe', 'Pesan di struk kasir'),
        (?, 'auto_print_receipt', 'true', 'Cetak struk otomatis saat pembayaran sukses')
    """, (outlet1_id, outlet1_id))

    cursor.execute("""
        INSERT INTO billing_plans (brand_id, plan_name, status, billing_cycle, start_date, end_date, price)
        VALUES (?, 'Pro Enterprise Multi-Outlet', 'active', 'yearly', date('now'), date('now', '+1 year'), 2400000)
    """, (brand_id,))

    # 2. Roles & Employees
    cursor.execute("""
        INSERT INTO roles (name, description, permissions)
        VALUES 
        ('Owner / Admin', 'Akses penuh ke semua fitur dan laporan', '["all"]'),
        ('Store Manager', 'Manajemen stok, shift, dan laporan penjualan', '["pos", "inventory", "reports", "shift"]'),
        ('Cashier / Barista', 'Operasional POS kasir, order dan update status meja', '["pos", "table", "shift_open_close"]')
    """)
    role_admin = 1
    role_manager = 2
    role_cashier = 3

    cursor.execute("""
        INSERT INTO employees (outlet_id, name, pin, role_id, phone)
        VALUES 
        (?, 'Budi Santoso (Supervisor)', '1122', ?, '081211112222'),
        (?, 'Siti Aminah (Kasir / Barista)', '1234', ?, '081233334444'),
        (?, 'Asep Setiawan (Kasir Sore)', '5678', ?, '081255556666')
    """, (outlet1_id, role_manager, outlet1_id, role_cashier, outlet1_id, role_cashier))
    emp_cashier_id = 2

    cursor.execute("""
        INSERT INTO employee_slots (outlet_id, max_slots, used_slots)
        VALUES (?, 10, 3), (?, 5, 1)
    """, (outlet1_id, outlet2_id))

    # 3. Product Catalog (Categories, Items, Modifiers, Bundles)
    cursor.execute("""
        INSERT INTO categories (brand_id, name, description)
        VALUES 
        (?, 'Signature Coffee', 'Kopi racikan khas Aurora dengan cita rasa unik'),
        (?, 'Manual Brew & Espresso', 'Kopi murni single origin nusantara'),
        (?, 'Non-Coffee & Tea', 'Minuman segar susu, matcha, dan teh artisan'),
        (?, 'Bakery & Pastry', 'Kue fresh baked setiap hari'),
        (?, 'Main Course', 'Makanan berat untuk santap siang dan malam')
    """, (brand_id, brand_id, brand_id, brand_id, brand_id))
    cat_coffee = 1
    cat_espresso = 2
    cat_noncoffee = 3
    cat_pastry = 4
    cat_food = 5

    # Modifiers
    cursor.execute("""
        INSERT INTO modifiers (brand_id, name, min_selection, max_selection)
        VALUES 
        (?, 'Level Gula (Sugar Level)', 1, 1),
        (?, 'Extra Topping & Add-ons', 0, 3)
    """, (brand_id, brand_id))
    mod_sugar = 1
    mod_topping = 2

    cursor.execute("""
        INSERT INTO modifier_options (modifier_id, name, additional_price)
        VALUES 
        (?, 'Normal Sugar (100%)', 0),
        (?, 'Less Sugar (50%)', 0),
        (?, 'No Sugar (0%)', 0),
        (?, 'Extra Espresso Shot', 5000),
        (?, 'Grass Jelly (Cincau)', 4000),
        (?, 'Ganti Susu Oat (Oatmilk)', 7000)
    """, (mod_sugar, mod_sugar, mod_sugar, mod_topping, mod_topping, mod_topping))

    # Items
    cursor.execute("""
        INSERT INTO items (category_id, name, description, sku, price, cost_price)
        VALUES 
        (?, 'Kopi Susu Gula Aren', 'Espresso, fresh milk, and premium palm sugar', 'KPS-001', 22000, 7500),
        (?, 'Espresso Double Shot', 'Double shot extracted from house blend arabica', 'ESP-002', 18000, 4000),
        (?, 'Matcha Green Tea Latte', 'Pure uji ceremonial matcha with steamed milk', 'MTC-003', 26000, 9500),
        (?, 'Butter Croissant French', 'Flaky butter croissant baked to golden perfection', 'CRS-004', 22000, 10000),
        (?, 'Nasi Goreng Spesial Aurora', 'Fried rice with chicken satay, egg, and kerupuk', 'NAS-005', 35000, 14000)
    """, (cat_coffee, cat_espresso, cat_noncoffee, cat_pastry, cat_food))
    item_kps = 1
    item_esp = 2
    item_mtc = 3
    item_crs = 4
    item_nas = 5

    # Connect modifiers to items
    cursor.execute("""
        INSERT INTO item_modifiers (item_id, modifier_id) VALUES 
        (?, ?), (?, ?), (?, ?),
        (?, ?), (?, ?), (?, ?),
        (?, ?), (?, ?), (?, ?)
    """, (
        item_kps, mod_sugar, item_kps, mod_topping, item_kps, mod_size,
        item_mtc, mod_sugar, item_mtc, mod_topping, item_mtc, mod_size,
        item_esp, mod_size, item_crs, mod_size, item_nas, mod_size
    ))

    # Bundle package
    cursor.execute("""
        INSERT INTO bundle_packages (brand_id, name, price, description)
        VALUES (?, 'Paket Ngopi Pagi (Morning Booster)', 38000, '1 Kopi Susu Gula Aren + 1 Butter Croissant French')
    """, (brand_id,))
    bundle_id = cursor.lastrowid
    cursor.execute("INSERT INTO bundle_items (bundle_id, item_id, quantity) VALUES (?, ?, 1), (?, ?, 1)",
                   (bundle_id, item_kps, bundle_id, item_crs))

    # 4. Inventory, Recipes, Suppliers, PO
    cursor.execute("""
        INSERT INTO ingredient_categories (brand_id, name, description)
        VALUES 
        (?, 'Biji Kopi (Coffee Beans)', 'Biji kopi sangrai specialty'),
        (?, 'Dairy & Pemanis', 'Susu cair, kental manis, sirup gula'),
        (?, 'Powder & Teh', 'Bubuk matcha, cokelat, teh artisan'),
        (?, 'Bahan Dapur & Bakery', 'Adonan kue dan bahan masakan')
    """, (brand_id, brand_id, brand_id, brand_id))

    cursor.execute("""
        INSERT INTO ingredients (category_id, name, unit, cost_per_unit, min_stock_alert)
        VALUES 
        (1, 'Biji Kopi Arabika House Blend', 'gr', 250, 1000),
        (2, 'Fresh Milk UHT Full Cream', 'ml', 18, 5000),
        (2, 'Gula Aren Cair Premium', 'ml', 35, 1000),
        (3, 'Matcha Powder Ceremonial', 'gr', 500, 250),
        (4, 'Adonan Croissant Beku', 'pcs', 10000, 20),
        (4, 'Beras Organik Pandan Wangi', 'gr', 15, 5000)
    """)
    ing_kopi = 1
    ing_susu = 2
    ing_aren = 3
    ing_matcha = 4
    ing_croissant = 5

    # Stock at Outlet 1 (Flagship)
    cursor.execute("""
        INSERT INTO outlet_ingredient_stocks (outlet_id, ingredient_id, current_stock)
        VALUES 
        (?, ?, 15000), -- 15 kg kopi
        (?, ?, 60000), -- 60 liter susu
        (?, ?, 12000), -- 12 liter gula aren
        (?, ?, 3000),  -- 3 kg matcha
        (?, ?, 100),   -- 100 pcs croissant
        (?, ?, 25000)  -- 25 kg beras
    """, (
        outlet1_id, ing_kopi,
        outlet1_id, ing_susu,
        outlet1_id, ing_aren,
        outlet1_id, ing_matcha,
        outlet1_id, ing_croissant,
        outlet1_id, 6
    ))

    # Recipes (Bill of Materials)
    cursor.execute("""
        INSERT INTO recipes (item_id, ingredient_id, quantity_used, unit)
        VALUES 
        (?, ?, 18, 'gr'), -- Kopi Susu: 18g kopi
        (?, ?, 150, 'ml'), -- Kopi Susu: 150ml susu
        (?, ?, 25, 'ml'),  -- Kopi Susu: 25ml gula aren
        (?, ?, 18, 'gr'),  -- Espresso: 18g kopi
        (?, ?, 15, 'gr'),  -- Matcha: 15g bubuk
        (?, ?, 200, 'ml'), -- Matcha: 200ml susu
        (?, ?, 1, 'pcs')   -- Croissant: 1 pcs
    """, (
        item_kps, ing_kopi,
        item_kps, ing_susu,
        item_kps, ing_aren,
        item_esp, ing_kopi,
        item_mtc, ing_matcha,
        item_mtc, ing_susu,
        item_crs, ing_croissant
    ))

    # Suppliers & PO
    cursor.execute("""
        INSERT INTO suppliers (brand_id, name, contact_person, phone, email, address)
        VALUES 
        (?, 'PT Roastery Kopi Nusantara', 'Hendra Wijaya', '08119876543', 'order@roasterynusantara.com', 'Kawasan Industri Cimahi No. 8'),
        (?, 'CV Sumber Dairy Segar', 'Dewi Susanti', '08128877665', 'dairy@sumbersusu.co.id', 'Lembang No. 42, Bandung Barat')
    """, (brand_id, brand_id))

    # 5. Tables & Floor Map
    cursor.execute("""
        INSERT INTO table_groups (outlet_id, name, description)
        VALUES 
        (?, 'Main Hall (Indoor AC)', 'Ruang utama bebas rokok ber-AC cocok untuk WFC'),
        (?, 'Garden Patio (Outdoor)', 'Area taman terbuka untuk santai dan merokok')
    """, (outlet1_id, outlet1_id))
    grp_indoor = 1
    grp_outdoor = 2

    cursor.execute("""
        INSERT INTO tables (group_id, outlet_id, table_number, capacity, pos_x, pos_y, status)
        VALUES 
        (?, ?, 'Meja 01', 2, 50, 50, 'available'),
        (?, ?, 'Meja 02', 4, 150, 50, 'available'),
        (?, ?, 'Meja 03', 4, 250, 50, 'available'),
        (?, ?, 'Meja 04 (Sofa)', 6, 50, 180, 'available'),
        (?, ?, 'Meja 05 (VIP)', 8, 200, 180, 'available'),
        (?, ?, 'Outdoor 01', 4, 50, 320, 'available'),
        (?, ?, 'Outdoor 02', 4, 150, 320, 'available')
    """, (
        grp_indoor, outlet1_id,
        grp_indoor, outlet1_id,
        grp_indoor, outlet1_id,
        grp_indoor, outlet1_id,
        grp_indoor, outlet1_id,
        grp_outdoor, outlet1_id,
        grp_outdoor, outlet1_id
    ))

    # 6. Taxes, Gratuity, Bank Accounts, QRIS
    cursor.execute("""
        INSERT INTO taxes (outlet_id, name, rate_percent, is_inclusive, is_active)
        VALUES (?, 'PB1 / Pajak Restoran', 10.0, 0, 1)
    """, (outlet1_id,))

    cursor.execute("""
        INSERT INTO gratuities (outlet_id, name, rate_percent, is_active)
        VALUES (?, 'Service Charge', 5.0, 1)
    """, (outlet1_id,))

    cursor.execute("""
        INSERT INTO bank_accounts (outlet_id, bank_name, account_number, account_holder)
        VALUES 
        (?, 'Bank Central Asia (BCA)', '8420192831', 'PT AURORA CAFE NUSANTARA'),
        (?, 'Bank Mandiri', '1310029381290', 'PT AURORA CAFE NUSANTARA')
    """, (outlet1_id, outlet1_id))

    cursor.execute("""
        INSERT INTO qris_configs (outlet_id, merchant_name, merchant_id, nmid, is_active)
        VALUES (?, 'Aurora Coffee Martadinata', 'MID-AURORA-001', 'ID1020023456789', 1)
    """, (outlet1_id,))

    # 7. Customers, Discounts, Promos, Campaigns
    cursor.execute("""
        INSERT INTO customers (brand_id, name, phone, email, loyalty_points, total_spent)
        VALUES 
        (?, 'Dimas Aditya', '081299887766', 'dimas@gmail.com', 45, 450000),
        (?, 'Clarissa Putri', '085712345678', 'clarissa@yahoo.com', 28, 280000)
    """, (brand_id, brand_id))

    cursor.execute("""
        INSERT INTO discounts (brand_id, name, discount_type, value, min_order_amount)
        VALUES 
        (?, 'Diskon Mahasiswa 10%', 'percentage', 10, 30000),
        (?, 'Potongan Rp 15.000', 'fixed', 15000, 60000)
    """, (brand_id, brand_id))

    cursor.execute("""
        INSERT INTO promos (brand_id, name, promo_code, discount_type, discount_value, quota, is_active)
        VALUES (?, 'Promo Hemat Mantap', 'AURORAPAS', 'fixed', 10000, 500, 1)
    """, (brand_id,))

    cursor.execute("""
        INSERT INTO campaigns (brand_id, name, target_audience, message, start_date, end_date)
        VALUES (?, 'Promo Coffee Week 2026', 'Semua Pelanggan Terdaftar', 'Dapatkan cashback poin 2x lipat setiap pembelian Kopi Susu!', date('now'), date('now', '+14 days'))
    """, (brand_id,))

    # 8. Sales Types
    cursor.execute("""
        INSERT INTO sales_types (outlet_id, name)
        VALUES 
        (?, 'Dine In (Makan di Tempat)'),
        (?, 'Take Away (Bungkus)'),
        (?, 'Delivery Online (GoFood / Grab)')
    """, (outlet1_id, outlet1_id, outlet1_id))

    # 9. Shifts: Open morning shift
    cursor.execute("""
        INSERT INTO shifts (outlet_id, employee_id, initial_cash, expected_cash, status)
        VALUES (?, ?, 200000, 200000, 'open')
    """, (outlet1_id, emp_cashier_id))

    # 10. Integrations (GoFood, Partners)
    cursor.execute("""
        INSERT INTO gofood_integrations (outlet_id, store_id, is_integrated, auto_accept_order)
        VALUES (?, 'GOFOOD-BDG-AURORA-01', 1, 1)
    """, (outlet1_id,))

    cursor.execute("""
        INSERT INTO partners (brand_id, partner_name, partner_type)
        VALUES 
        (?, 'GoFood Indonesia', 'delivery'),
        (?, 'GrabFood Merchant', 'delivery'),
        (?, 'ShopeePay & QRIS', 'payment')
    """, (brand_id, brand_id, brand_id))

    conn.commit()
    conn.close()
    print("Seeding completed successfully! All 41 modules are ready.")

if __name__ == "__main__":
    run_seed()
