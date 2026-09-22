import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "aurora_cafe.db"
OUTPUT_SCHEMA_SQL = BASE_DIR / "schema_mysql.sql"
OUTPUT_SEED_SQL = BASE_DIR / "seed_mysql.sql"

MYSQL_DDL = """-- ==========================================================
-- Aurora Cafe POS - MySQL / MariaDB Relational Database Schema
-- Synchronized 41 Modules
-- Compatible with MySQL 5.7, 8.0, and MariaDB 10+
-- ==========================================================

SET FOREIGN_KEY_CHECKS = 0;
DROP DATABASE IF EXISTS aurora_cafe;
CREATE DATABASE aurora_cafe CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE aurora_cafe;

-- 1. Brand & Outlet Management
CREATE TABLE brands (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    logo VARCHAR(255) NULL,
    description TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE outlets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    brand_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    address TEXT NULL,
    phone VARCHAR(50) NULL,
    email VARCHAR(100) NULL,
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    outlet_id INT NULL,
    setting_key VARCHAR(100) NOT NULL,
    setting_value TEXT NOT NULL,
    description TEXT NULL,
    UNIQUE KEY uq_outlet_key (outlet_id, setting_key),
    FOREIGN KEY (outlet_id) REFERENCES outlets(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE billing_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    brand_id INT NOT NULL,
    plan_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    billing_cycle VARCHAR(50) DEFAULT 'monthly',
    start_date DATE NULL,
    end_date DATE NULL,
    price DECIMAL(15,2) DEFAULT 0.00,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Access & Employee Management
CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NULL,
    permissions LONGTEXT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    brand_id INT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    role_id INT NULL,
    phone VARCHAR(50) NULL,
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE SET NULL,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    outlet_id INT NOT NULL,
    user_id INT NULL,
    name VARCHAR(200) NOT NULL,
    pin VARCHAR(10) NOT NULL,
    role_id INT NULL,
    phone VARCHAR(50) NULL,
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (outlet_id) REFERENCES outlets(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE employee_slots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    outlet_id INT NOT NULL UNIQUE,
    max_slots INT DEFAULT 5,
    used_slots INT DEFAULT 0,
    FOREIGN KEY (outlet_id) REFERENCES outlets(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Product Catalog
CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    brand_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT NULL,
    is_active TINYINT(1) DEFAULT 1,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT NULL,
    sku VARCHAR(100) UNIQUE NULL,
    price DECIMAL(15,2) NOT NULL,
    cost_price DECIMAL(15,2) DEFAULT 0.00,
    image_url VARCHAR(255) NULL,
    is_active TINYINT(1) DEFAULT 1,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE modifiers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    brand_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    min_selection INT DEFAULT 0,
    max_selection INT DEFAULT 1,
    is_active TINYINT(1) DEFAULT 1,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE modifier_options (
    id INT AUTO_INCREMENT PRIMARY KEY,
    modifier_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    additional_price DECIMAL(15,2) DEFAULT 0.00,
    FOREIGN KEY (modifier_id) REFERENCES modifiers(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE item_modifiers (
    item_id INT NOT NULL,
    modifier_id INT NOT NULL,
    PRIMARY KEY (item_id, modifier_id),
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    FOREIGN KEY (modifier_id) REFERENCES modifiers(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE bundle_packages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    brand_id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    price DECIMAL(15,2) NOT NULL,
    description TEXT NULL,
    is_active TINYINT(1) DEFAULT 1,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE bundle_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bundle_id INT NOT NULL,
    item_id INT NOT NULL,
    quantity INT DEFAULT 1,
    FOREIGN KEY (bundle_id) REFERENCES bundle_packages(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Inventory, Recipes & Supply Chain
CREATE TABLE ingredient_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    brand_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT NULL,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ingredients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NULL,
    name VARCHAR(200) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    cost_per_unit DECIMAL(15,2) DEFAULT 0.00,
    min_stock_alert DECIMAL(15,2) DEFAULT 10.00,
    is_active TINYINT(1) DEFAULT 1,
    FOREIGN KEY (category_id) REFERENCES ingredient_categories(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE outlet_ingredient_stocks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    outlet_id INT NOT NULL,
    ingredient_id INT NOT NULL,
    current_stock DECIMAL(15,2) DEFAULT 0.00,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_outlet_ing (outlet_id, ingredient_id),
    FOREIGN KEY (outlet_id) REFERENCES outlets(id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE recipes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT NOT NULL,
    ingredient_id INT NOT NULL,
    quantity_used DECIMAL(15,2) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    UNIQUE KEY uq_item_ingredient (item_id, ingredient_id),
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE suppliers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    brand_id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    contact_person VARCHAR(150) NULL,
    phone VARCHAR(50) NULL,
    email VARCHAR(100) NULL,
    address TEXT NULL,
    is_active TINYINT(1) DEFAULT 1,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE purchase_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    po_number VARCHAR(100) NOT NULL UNIQUE,
    supplier_id INT NOT NULL,
    outlet_id INT NOT NULL,
    order_date DATE NOT NULL,
    expected_date DATE NULL,
    status VARCHAR(50) DEFAULT 'draft',
    total_amount DECIMAL(15,2) DEFAULT 0.00,
    notes TEXT NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE RESTRICT,
    FOREIGN KEY (outlet_id) REFERENCES outlets(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE purchase_order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    po_id INT NOT NULL,
    ingredient_id INT NOT NULL,
    quantity DECIMAL(15,2) NOT NULL,
    unit_price DECIMAL(15,2) NOT NULL,
    subtotal DECIMAL(15,2) NOT NULL,
    FOREIGN KEY (po_id) REFERENCES purchase_orders(id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE stock_adjustments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    outlet_id INT NOT NULL,
    date DATE NOT NULL,
    reason TEXT NOT NULL,
    adjusted_by VARCHAR(150) NOT NULL,
    status VARCHAR(50) DEFAULT 'completed',
    FOREIGN KEY (outlet_id) REFERENCES outlets(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE stock_adjustment_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    adjustment_id INT NOT NULL,
    ingredient_id INT NOT NULL,
    system_stock DECIMAL(15,2) NOT NULL,
    actual_stock DECIMAL(15,2) NOT NULL,
    difference DECIMAL(15,2) NOT NULL,
    FOREIGN KEY (adjustment_id) REFERENCES stock_adjustments(id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE stock_transfers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transfer_number VARCHAR(100) NOT NULL UNIQUE,
    source_outlet_id INT NOT NULL,
    target_outlet_id INT NOT NULL,
    transfer_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    notes TEXT NULL,
    FOREIGN KEY (source_outlet_id) REFERENCES outlets(id) ON DELETE RESTRICT,
    FOREIGN KEY (target_outlet_id) REFERENCES outlets(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE stock_transfer_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transfer_id INT NOT NULL,
    ingredient_id INT NOT NULL,
    quantity DECIMAL(15,2) NOT NULL,
    FOREIGN KEY (transfer_id) REFERENCES stock_transfers(id) ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Table & Floor Management
CREATE TABLE table_groups (
    id INT AUTO_INCREMENT PRIMARY KEY,
    outlet_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT NULL,
    FOREIGN KEY (outlet_id) REFERENCES outlets(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE tables (
    id INT AUTO_INCREMENT PRIMARY KEY,
    group_id INT NULL,
    outlet_id INT NOT NULL,
    table_number VARCHAR(50) NOT NULL,
    capacity INT DEFAULT 4,
    pos_x DECIMAL(10,2) DEFAULT 0.00,
    pos_y DECIMAL(10,2) DEFAULT 0.00,
    status VARCHAR(50) DEFAULT 'available',
    current_transaction_id INT NULL,
    UNIQUE KEY uq_outlet_table (outlet_id, table_number),
    FOREIGN KEY (group_id) REFERENCES table_groups(id) ON DELETE SET NULL,
    FOREIGN KEY (outlet_id) REFERENCES outlets(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Taxes, Gratuity & Payments
CREATE TABLE taxes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    outlet_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    rate_percent DECIMAL(5,2) NOT NULL,
    is_inclusive TINYINT(1) DEFAULT 0,
    is_active TINYINT(1) DEFAULT 1,
    FOREIGN KEY (outlet_id) REFERENCES outlets(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE gratuities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    outlet_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    rate_percent DECIMAL(5,2) NOT NULL,
    is_active TINYINT(1) DEFAULT 1,
    FOREIGN KEY (outlet_id) REFERENCES outlets(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE bank_accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    outlet_id INT NOT NULL,
    bank_name VARCHAR(100) NOT NULL,
    account_number VARCHAR(100) NOT NULL,
    account_holder VARCHAR(150) NOT NULL,
    is_active TINYINT(1) DEFAULT 1,
    FOREIGN KEY (outlet_id) REFERENCES outlets(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE qris_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    outlet_id INT NOT NULL UNIQUE,
    merchant_name VARCHAR(150) NOT NULL,
    merchant_id VARCHAR(100) NOT NULL,
    nmid VARCHAR(100) NOT NULL,
    api_key VARCHAR(255) NULL,
    is_active TINYINT(1) DEFAULT 1,
    FOREIGN KEY (outlet_id) REFERENCES outlets(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE qris_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id INT NULL,
    qr_string TEXT NOT NULL,
    transaction_reference VARCHAR(100) NOT NULL UNIQUE,
    amount DECIMAL(15,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    expiry_time VARCHAR(50) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Promotions, Discounts & Loyalty
CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    brand_id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    phone VARCHAR(50) UNIQUE NULL,
    email VARCHAR(100) NULL,
    loyalty_points INT DEFAULT 0,
    total_spent DECIMAL(15,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE discounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    brand_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    discount_type VARCHAR(50) NOT NULL,
    value DECIMAL(15,2) NOT NULL,
    min_order_amount DECIMAL(15,2) DEFAULT 0.00,
    is_active TINYINT(1) DEFAULT 1,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE promos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    brand_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    promo_code VARCHAR(50) NOT NULL UNIQUE,
    discount_type VARCHAR(50) NOT NULL,
    discount_value DECIMAL(15,2) NOT NULL,
    start_date DATE NULL,
    end_date DATE NULL,
    quota INT DEFAULT 100,
    used_count INT DEFAULT 0,
    is_active TINYINT(1) DEFAULT 1,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE campaigns (
    id INT AUTO_INCREMENT PRIMARY KEY,
    brand_id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    target_audience TEXT NULL,
    message TEXT NULL,
    start_date DATE NULL,
    end_date DATE NULL,
    status VARCHAR(50) DEFAULT 'active',
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. POS Transactions, Shifts & Invoicing
CREATE TABLE shifts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    outlet_id INT NOT NULL,
    employee_id INT NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    initial_cash DECIMAL(15,2) DEFAULT 0.00,
    expected_cash DECIMAL(15,2) DEFAULT 0.00,
    actual_cash DECIMAL(15,2) NULL,
    difference DECIMAL(15,2) NULL,
    notes TEXT NULL,
    status VARCHAR(50) DEFAULT 'open',
    FOREIGN KEY (outlet_id) REFERENCES outlets(id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE sales_types (
    id INT AUTO_INCREMENT PRIMARY KEY,
    outlet_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_active TINYINT(1) DEFAULT 1,
    UNIQUE KEY uq_outlet_sales_type (outlet_id, name),
    FOREIGN KEY (outlet_id) REFERENCES outlets(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_number VARCHAR(100) NOT NULL UNIQUE,
    outlet_id INT NOT NULL,
    shift_id INT NULL,
    cashier_id INT NULL,
    customer_id INT NULL,
    table_id INT NULL,
    sales_type_id INT NULL,
    subtotal DECIMAL(15,2) NOT NULL,
    discount_amount DECIMAL(15,2) DEFAULT 0.00,
    tax_amount DECIMAL(15,2) DEFAULT 0.00,
    gratuity_amount DECIMAL(15,2) DEFAULT 0.00,
    total_amount DECIMAL(15,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    payment_status VARCHAR(50) DEFAULT 'paid',
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (outlet_id) REFERENCES outlets(id) ON DELETE RESTRICT,
    FOREIGN KEY (shift_id) REFERENCES shifts(id) ON DELETE SET NULL,
    FOREIGN KEY (cashier_id) REFERENCES employees(id) ON DELETE SET NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
    FOREIGN KEY (table_id) REFERENCES tables(id) ON DELETE SET NULL,
    FOREIGN KEY (sales_type_id) REFERENCES sales_types(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE transaction_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id INT NOT NULL,
    item_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(15,2) NOT NULL,
    subtotal_price DECIMAL(15,2) NOT NULL,
    notes TEXT NULL,
    FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE transaction_item_modifiers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_item_id INT NOT NULL,
    modifier_option_id INT NOT NULL,
    additional_price DECIMAL(15,2) DEFAULT 0.00,
    FOREIGN KEY (transaction_item_id) REFERENCES transaction_items(id) ON DELETE CASCADE,
    FOREIGN KEY (modifier_option_id) REFERENCES modifier_options(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE invoices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_number VARCHAR(100) NOT NULL UNIQUE,
    transaction_id INT NOT NULL,
    issue_date DATE NOT NULL,
    due_date DATE NULL,
    status VARCHAR(50) DEFAULT 'paid',
    total_amount DECIMAL(15,2) NOT NULL,
    FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. Integrations & Mobile Orders
CREATE TABLE mobile_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    outlet_id INT NOT NULL,
    table_id INT NULL,
    customer_name VARCHAR(150) NOT NULL,
    customer_phone VARCHAR(50) NULL,
    items_json LONGTEXT NOT NULL,
    total_amount DECIMAL(15,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (outlet_id) REFERENCES outlets(id) ON DELETE CASCADE,
    FOREIGN KEY (table_id) REFERENCES tables(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE gofood_integrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    outlet_id INT NOT NULL UNIQUE,
    store_id VARCHAR(100) NOT NULL,
    is_integrated TINYINT(1) DEFAULT 0,
    auto_accept_order TINYINT(1) DEFAULT 1,
    last_sync_at TIMESTAMP NULL,
    FOREIGN KEY (outlet_id) REFERENCES outlets(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE partners (
    id INT AUTO_INCREMENT PRIMARY KEY,
    brand_id INT NOT NULL,
    partner_name VARCHAR(150) NOT NULL,
    partner_type VARCHAR(50) NOT NULL,
    api_key VARCHAR(255) NULL,
    webhook_url VARCHAR(255) NULL,
    status VARCHAR(50) DEFAULT 'active',
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 10. Sync Logs
CREATE TABLE sync_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    outlet_id INT NULL,
    entity_name VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    entity_id INT NOT NULL,
    payload LONGTEXT NULL,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (outlet_id) REFERENCES outlets(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;
"""

def export_all():
    print("Exporting MySQL Schema DDL...")
    with open(OUTPUT_SCHEMA_SQL, "w", encoding="utf-8") as f:
        f.write(MYSQL_DDL)
    print(f"Generated: {OUTPUT_SCHEMA_SQL}")

    print("Dumping seed data into seed_mysql.sql...")
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    tables = [
        "brands", "outlets", "settings", "billing_plans", "roles", "users",
        "employees", "employee_slots", "categories", "items", "modifiers",
        "modifier_options", "item_modifiers", "bundle_packages", "bundle_items",
        "ingredient_categories", "ingredients", "outlet_ingredient_stocks",
        "recipes", "suppliers", "table_groups", "tables", "taxes", "gratuities",
        "bank_accounts", "qris_configs", "customers", "discounts", "promos",
        "campaigns", "sales_types", "shifts", "gofood_integrations", "partners"
    ]

    with open(OUTPUT_SEED_SQL, "w", encoding="utf-8") as f:
        f.write("USE aurora_cafe;\nSET FOREIGN_KEY_CHECKS = 0;\n\n")
        for tbl in tables:
            cursor.execute(f"SELECT * FROM {tbl}")
            rows = cursor.fetchall()
            if not rows:
                continue

            cursor.execute(f"PRAGMA table_info({tbl})")
            cols = [col[1] for col in cursor.fetchall()]
            col_list = ", ".join(f"`{c}`" for c in cols)

            f.write(f"-- Data for {tbl}\n")
            for r in rows:
                vals = []
                for v in r:
                    if v is None:
                        vals.append("NULL")
                    elif isinstance(v, (int, float)):
                        vals.append(str(v))
                    else:
                        escaped = str(v).replace("'", "\\'")
                        vals.append(f"'{escaped}'")
                val_list = ", ".join(vals)
                f.write(f"INSERT INTO `{tbl}` ({col_list}) VALUES ({val_list});\n")
            f.write("\n")
        f.write("SET FOREIGN_KEY_CHECKS = 1;\n")

    conn.close()
    print(f"Generated: {OUTPUT_SEED_SQL}")

if __name__ == "__main__":
    export_all()
