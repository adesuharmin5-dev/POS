import sqlite3
import hashlib
import secrets
from typing import Generator
from app.config import DB_PATH

def hash_password(password: str) -> str:
    salt = secrets.token_hex(8)
    h = hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()
    return f"{salt}${h}"

def verify_password(password: str, hashed: str) -> bool:
    try:
        if not hashed:
            return False
        if "$" in hashed:
            salt, h = hashed.split("$", 1)
            expected = hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()
            return secrets.compare_digest(h, expected)
        # Fallback for plain text demo passwords
        return password == hashed
    except Exception:
        return False

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    -- 1. Brand & Outlet Management (Brand, Outlet, Setting, Billing)
    CREATE TABLE IF NOT EXISTS brands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        logo TEXT,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS outlets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        address TEXT,
        phone TEXT,
        email TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        outlet_id INTEGER REFERENCES outlets(id) ON DELETE CASCADE,
        setting_key TEXT NOT NULL,
        setting_value TEXT NOT NULL,
        description TEXT,
        UNIQUE(outlet_id, setting_key)
    );

    CREATE TABLE IF NOT EXISTS billing_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
        plan_name TEXT NOT NULL,
        status TEXT DEFAULT 'active', -- active, expired, pending
        billing_cycle TEXT DEFAULT 'monthly', -- monthly, yearly
        start_date TEXT,
        end_date TEXT,
        price REAL DEFAULT 0
    );

    -- 2. Access & Employee Management (Akun, Role, Employee slot, Employee akses, Pin akses)
    CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        permissions TEXT -- JSON string of permissions
    );

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand_id INTEGER REFERENCES brands(id) ON DELETE SET NULL,
        username TEXT UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role_id INTEGER REFERENCES roles(id) ON DELETE SET NULL,
        phone TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        outlet_id INTEGER NOT NULL REFERENCES outlets(id) ON DELETE CASCADE,
        user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
        name TEXT NOT NULL,
        pin TEXT NOT NULL, -- 4-6 digit numeric pin for POS fast switch
        role_id INTEGER REFERENCES roles(id) ON DELETE SET NULL,
        phone TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS employee_slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        outlet_id INTEGER NOT NULL UNIQUE REFERENCES outlets(id) ON DELETE CASCADE,
        max_slots INTEGER DEFAULT 5,
        used_slots INTEGER DEFAULT 0
    );

    -- 3. Product Catalog (Kategori, Item library, Modifikasi, Bundle package)
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        description TEXT,
        is_active INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
        name TEXT NOT NULL,
        description TEXT,
        sku TEXT UNIQUE,
        price REAL NOT NULL,
        cost_price REAL DEFAULT 0,
        image_url TEXT,
        is_active INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS modifiers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        min_selection INTEGER DEFAULT 0,
        max_selection INTEGER DEFAULT 1,
        is_active INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS modifier_options (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        modifier_id INTEGER NOT NULL REFERENCES modifiers(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        additional_price REAL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS item_modifiers (
        item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
        modifier_id INTEGER NOT NULL REFERENCES modifiers(id) ON DELETE CASCADE,
        PRIMARY KEY (item_id, modifier_id)
    );

    CREATE TABLE IF NOT EXISTS bundle_packages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        description TEXT,
        is_active INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS bundle_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bundle_id INTEGER NOT NULL REFERENCES bundle_packages(id) ON DELETE CASCADE,
        item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
        quantity INTEGER DEFAULT 1
    );

    -- 4. Inventory, Recipes & Supply Chain (Ingredient library, Ingredient kategori, Recipes, Supplier, PO, Adjusment, Transfer)
    CREATE TABLE IF NOT EXISTS ingredient_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        description TEXT
    );

    CREATE TABLE IF NOT EXISTS ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER REFERENCES ingredient_categories(id) ON DELETE SET NULL,
        name TEXT NOT NULL,
        unit TEXT NOT NULL, -- gr, ml, pcs, kg, etc.
        cost_per_unit REAL DEFAULT 0,
        min_stock_alert REAL DEFAULT 10,
        is_active INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS outlet_ingredient_stocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        outlet_id INTEGER NOT NULL REFERENCES outlets(id) ON DELETE CASCADE,
        ingredient_id INTEGER NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
        current_stock REAL DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(outlet_id, ingredient_id)
    );

    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
        ingredient_id INTEGER NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
        quantity_used REAL NOT NULL,
        unit TEXT NOT NULL,
        UNIQUE(item_id, ingredient_id)
    );

    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        contact_person TEXT,
        phone TEXT,
        email TEXT,
        address TEXT,
        is_active INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS purchase_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        po_number TEXT NOT NULL UNIQUE,
        supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE RESTRICT,
        outlet_id INTEGER NOT NULL REFERENCES outlets(id) ON DELETE CASCADE,
        order_date TEXT NOT NULL,
        expected_date TEXT,
        status TEXT DEFAULT 'draft', -- draft, ordered, received, cancelled
        total_amount REAL DEFAULT 0,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS purchase_order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        po_id INTEGER NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
        ingredient_id INTEGER NOT NULL REFERENCES ingredients(id) ON DELETE RESTRICT,
        quantity REAL NOT NULL,
        unit_price REAL NOT NULL,
        subtotal REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS stock_adjustments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        outlet_id INTEGER NOT NULL REFERENCES outlets(id) ON DELETE CASCADE,
        date TEXT NOT NULL,
        reason TEXT NOT NULL,
        adjusted_by TEXT NOT NULL,
        status TEXT DEFAULT 'completed'
    );

    CREATE TABLE IF NOT EXISTS stock_adjustment_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        adjustment_id INTEGER NOT NULL REFERENCES stock_adjustments(id) ON DELETE CASCADE,
        ingredient_id INTEGER NOT NULL REFERENCES ingredients(id) ON DELETE RESTRICT,
        system_stock REAL NOT NULL,
        actual_stock REAL NOT NULL,
        difference REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS stock_transfers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transfer_number TEXT NOT NULL UNIQUE,
        source_outlet_id INTEGER NOT NULL REFERENCES outlets(id) ON DELETE RESTRICT,
        target_outlet_id INTEGER NOT NULL REFERENCES outlets(id) ON DELETE RESTRICT,
        transfer_date TEXT NOT NULL,
        status TEXT DEFAULT 'pending', -- pending, in_transit, received, rejected
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS stock_transfer_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transfer_id INTEGER NOT NULL REFERENCES stock_transfers(id) ON DELETE CASCADE,
        ingredient_id INTEGER NOT NULL REFERENCES ingredients(id) ON DELETE RESTRICT,
        quantity REAL NOT NULL
    );

    -- 5. Table & Floor Management (Table grup, Table maps, Table report)
    CREATE TABLE IF NOT EXISTS table_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        outlet_id INTEGER NOT NULL REFERENCES outlets(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        description TEXT
    );

    CREATE TABLE IF NOT EXISTS tables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER REFERENCES table_groups(id) ON DELETE SET NULL,
        outlet_id INTEGER NOT NULL REFERENCES outlets(id) ON DELETE CASCADE,
        table_number TEXT NOT NULL,
        capacity INTEGER DEFAULT 4,
        pos_x REAL DEFAULT 0,
        pos_y REAL DEFAULT 0,
        status TEXT DEFAULT 'available', -- available, occupied, reserved
        current_transaction_id INTEGER,
        UNIQUE(outlet_id, table_number)
    );

    -- 6. Taxes, Gratuity, Bank & Payments (Pajak, Gratuity, Bank akun, QRIS config, QRIS)
    CREATE TABLE IF NOT EXISTS taxes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        outlet_id INTEGER NOT NULL REFERENCES outlets(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        rate_percent REAL NOT NULL,
        is_inclusive INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS gratuities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        outlet_id INTEGER NOT NULL REFERENCES outlets(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        rate_percent REAL NOT NULL,
        is_active INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS bank_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        outlet_id INTEGER NOT NULL REFERENCES outlets(id) ON DELETE CASCADE,
        bank_name TEXT NOT NULL,
        account_number TEXT NOT NULL,
        account_holder TEXT NOT NULL,
        is_active INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS qris_configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        outlet_id INTEGER NOT NULL UNIQUE REFERENCES outlets(id) ON DELETE CASCADE,
        merchant_name TEXT NOT NULL,
        merchant_id TEXT NOT NULL,
        nmid TEXT NOT NULL,
        api_key TEXT,
        is_active INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS qris_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id INTEGER,
        qr_string TEXT NOT NULL,
        transaction_reference TEXT NOT NULL UNIQUE,
        amount REAL NOT NULL,
        status TEXT DEFAULT 'pending', -- pending, paid, expired
        expiry_time TEXT
    );

    -- 7. Promotions, Discounts & Loyalty (Diskon, Promo, Campaign, Konsumen list)
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        phone TEXT UNIQUE,
        email TEXT,
        loyalty_points INTEGER DEFAULT 0,
        total_spent REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS discounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        discount_type TEXT NOT NULL, -- percentage, fixed
        value REAL NOT NULL,
        min_order_amount REAL DEFAULT 0,
        is_active INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS promos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        promo_code TEXT NOT NULL UNIQUE,
        discount_type TEXT NOT NULL, -- percentage, fixed
        discount_value REAL NOT NULL,
        start_date TEXT,
        end_date TEXT,
        quota INTEGER DEFAULT 100,
        used_count INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS campaigns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        target_audience TEXT,
        message TEXT,
        start_date TEXT,
        end_date TEXT,
        status TEXT DEFAULT 'active' -- active, completed, draft
    );

    -- 8. POS Transactions, Shifts & Invoicing (Shift, Sales type, Transaksi, Invoice, Sales, Summary)
    CREATE TABLE IF NOT EXISTS shifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        outlet_id INTEGER NOT NULL REFERENCES outlets(id) ON DELETE CASCADE,
        employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE RESTRICT,
        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_time TIMESTAMP,
        initial_cash REAL NOT NULL DEFAULT 0,
        expected_cash REAL DEFAULT 0,
        actual_cash REAL,
        difference REAL,
        notes TEXT,
        status TEXT DEFAULT 'open' -- open, closed
    );

    CREATE TABLE IF NOT EXISTS attendances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
        outlet_id INTEGER NOT NULL REFERENCES outlets(id) ON DELETE CASCADE,
        clock_in TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        clock_out TIMESTAMP,
        shift_id INTEGER REFERENCES shifts(id) ON DELETE SET NULL,
        work_minutes INTEGER,
        notes TEXT,
        status TEXT DEFAULT 'present', -- present, late, absent, half_day
        date TEXT NOT NULL            -- YYYY-MM-DD
    );

    CREATE TABLE IF NOT EXISTS sales_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        outlet_id INTEGER NOT NULL REFERENCES outlets(id) ON DELETE CASCADE,
        name TEXT NOT NULL, -- Dine In, Take Away, Delivery, Online
        is_active INTEGER DEFAULT 1,
        UNIQUE(outlet_id, name)
    );

    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_number TEXT NOT NULL UNIQUE,
        outlet_id INTEGER NOT NULL REFERENCES outlets(id) ON DELETE RESTRICT,
        shift_id INTEGER REFERENCES shifts(id) ON DELETE SET NULL,
        cashier_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,
        customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
        table_id INTEGER REFERENCES tables(id) ON DELETE SET NULL,
        sales_type_id INTEGER REFERENCES sales_types(id) ON DELETE SET NULL,
        subtotal REAL NOT NULL,
        discount_amount REAL DEFAULT 0,
        tax_amount REAL DEFAULT 0,
        gratuity_amount REAL DEFAULT 0,
        total_amount REAL NOT NULL,
        payment_method TEXT NOT NULL, -- Cash, QRIS, Debit/Credit, GoFood
        payment_status TEXT DEFAULT 'paid', -- paid, pending, cancelled, refunded
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS transaction_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id INTEGER NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
        item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE RESTRICT,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        subtotal_price REAL NOT NULL,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS transaction_item_modifiers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_item_id INTEGER NOT NULL REFERENCES transaction_items(id) ON DELETE CASCADE,
        modifier_option_id INTEGER NOT NULL REFERENCES modifier_options(id) ON DELETE RESTRICT,
        additional_price REAL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT NOT NULL UNIQUE,
        transaction_id INTEGER NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
        issue_date TEXT NOT NULL,
        due_date TEXT,
        status TEXT DEFAULT 'paid', -- paid, pending, void
        total_amount REAL NOT NULL
    );

    -- 9. Integrations & Mobile Orders (Moke order, Go food, Partner)
    CREATE TABLE IF NOT EXISTS mobile_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        outlet_id INTEGER NOT NULL REFERENCES outlets(id) ON DELETE CASCADE,
        table_id INTEGER REFERENCES tables(id) ON DELETE SET NULL,
        customer_name TEXT NOT NULL,
        customer_phone TEXT,
        items_json TEXT NOT NULL,
        total_amount REAL NOT NULL,
        status TEXT DEFAULT 'pending', -- pending, confirmed, preparing, served, completed, cancelled
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS gofood_integrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        outlet_id INTEGER NOT NULL UNIQUE REFERENCES outlets(id) ON DELETE CASCADE,
        store_id TEXT NOT NULL,
        is_integrated INTEGER DEFAULT 0,
        auto_accept_order INTEGER DEFAULT 1,
        last_sync_at TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS partners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
        partner_name TEXT NOT NULL,
        partner_type TEXT NOT NULL, -- delivery, payment, accounting, loyalty
        api_key TEXT,
        webhook_url TEXT,
        status TEXT DEFAULT 'active'
    );

    -- 10. Multi-Terminal Synchronization Logs
    CREATE TABLE IF NOT EXISTS sync_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        outlet_id INTEGER REFERENCES outlets(id) ON DELETE CASCADE,
        entity_name TEXT NOT NULL, -- transaction, stock, shift, table
        action TEXT NOT NULL, -- insert, update, delete
        entity_id INTEGER NOT NULL,
        payload TEXT,
        synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Indexes for high performance queries
    CREATE INDEX IF NOT EXISTS idx_items_category ON items(category_id);
    CREATE INDEX IF NOT EXISTS idx_transactions_outlet_created ON transactions(outlet_id, created_at);
    CREATE INDEX IF NOT EXISTS idx_outlet_stocks ON outlet_ingredient_stocks(outlet_id, ingredient_id);
    CREATE INDEX IF NOT EXISTS idx_shifts_outlet_status ON shifts(outlet_id, status);
    CREATE INDEX IF NOT EXISTS idx_tables_outlet_status ON tables(outlet_id, status);
    CREATE INDEX IF NOT EXISTS idx_attendances_emp_date ON attendances(employee_id, date);
    CREATE INDEX IF NOT EXISTS idx_attendances_outlet_date ON attendances(outlet_id, date);
    """)

    # Check and migrate username column in users table if needed
    try:
        conn.execute("SELECT username FROM users LIMIT 1")
    except sqlite3.OperationalError:
        try:
            conn.execute("ALTER TABLE users ADD COLUMN username TEXT")
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username)")
            conn.commit()
        except Exception:
            pass

    # Auto seed default users if none exist
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        salt1 = secrets.token_hex(8)
        hash1 = f"{salt1}${hashlib.sha256(f'{salt1}admin123'.encode('utf-8')).hexdigest()}"
        salt2 = secrets.token_hex(8)
        hash2 = f"{salt2}${hashlib.sha256(f'{salt2}kasir123'.encode('utf-8')).hexdigest()}"

        cursor.execute("""
            INSERT INTO users (brand_id, username, email, password_hash, full_name, role_id, phone, is_active)
            VALUES (1, 'admin', 'admin@auroracafe.com', ?, 'Ade Suharmin (Owner)', 1, '081234567890', 1)
        """, (hash1,))

        cursor.execute("""
            INSERT INTO users (brand_id, username, email, password_hash, full_name, role_id, phone, is_active)
            VALUES (1, 'kasir', 'kasir@auroracafe.com', ?, 'Kasir Utama Aurora', 2, '081233334444', 1)
        """, (hash2,))

    conn.commit()
    conn.close()
