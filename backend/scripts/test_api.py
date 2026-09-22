import sys
from pathlib import Path

# Add backend to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db_connection

def run_tests():
    client = TestClient(app)
    print("=== TEST 1: Health & Root ===")
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    print("Health response:", data)
    assert data["modules_covered"] == 41

    print("\n=== TEST 2: Product Catalog & Modifiers ===")
    res = client.get("/api/catalog/items")
    assert res.status_code == 200
    items = res.json()
    print(f"Loaded {len(items)} items.")
    kopi_susu = next(i for i in items if "Kopi Susu" in i["name"])
    print(f"Selected: {kopi_susu['name']} (Price: Rp {kopi_susu['price']:,})")
    assert len(kopi_susu["modifiers"]) > 0

    print("\n=== TEST 3: Pre-Checkout Stock Inspection ===")
    res = client.get("/api/inventory/ingredients?outlet_id=1")
    assert res.status_code == 200
    ingredients = {i["name"]: i["current_stock"] for i in res.json()}
    kopi_stock_before = ingredients["Biji Kopi Arabika House Blend"]
    susu_stock_before = ingredients["Fresh Milk UHT Full Cream"]
    print(f"Biji Kopi before: {kopi_stock_before} gr")
    print(f"Fresh Milk before: {susu_stock_before} ml")

    print("\n=== TEST 4: Table Map Before Checkout ===")
    conn = get_db_connection()
    conn.execute("UPDATE tables SET status = 'available' WHERE table_number = 'Meja 01'")
    conn.commit()
    conn.close()

    res = client.get("/api/tables?outlet_id=1")
    assert res.status_code == 200
    tables = res.json()
    meja1 = next(t for t in tables if t["table_number"] == "Meja 01")
    print(f"Meja 01 status before: {meja1['status']}")
    assert meja1["status"] == "available"

    print("\n=== TEST 5: POS Checkout Pipeline ===")
    # Order: 2x Kopi Susu (with Extra Espresso Shot) + 1x Butter Croissant
    extra_shot_option_id = 4 # Extra Espresso Shot
    checkout_payload = {
        "outlet_id": 1,
        "shift_id": 1,
        "cashier_id": 2, # Siti Aminah
        "customer_id": 1, # Dimas Aditya
        "table_id": meja1["id"],
        "sales_type_id": 1, # Dine In
        "payment_method": "Cash",
        "cash_received": 100000.0,
        "items": [
            {
                "item_id": kopi_susu["id"],
                "quantity": 2,
                "unit_price": kopi_susu["price"],
                "notes": "Less ice, extra hot",
                "modifiers": [
                    {"modifier_option_id": extra_shot_option_id, "additional_price": 5000.0}
                ]
            },
            {
                "item_id": 4, # Butter Croissant French
                "quantity": 1,
                "unit_price": 22000.0,
                "notes": "Hangatkan"
            }
        ],
        "notes": "Pesanan Meja 01"
    }

    res = client.post("/api/pos/checkout", json=checkout_payload)
    print("Checkout HTTP status:", res.status_code)
    assert res.status_code == 200
    trx = res.json()
    print("Transaction Success!")
    print(f"Trx Number: {trx['transaction_number']}")
    print(f"Invoice Number: {trx['invoice_number']}")
    print(f"Subtotal: Rp {trx['subtotal']:,}")
    print(f"Tax: Rp {trx['tax_amount']:,}")
    print(f"Gratuity: Rp {trx['gratuity_amount']:,}")
    print(f"Total Amount: Rp {trx['total_amount']:,}")
    print(f"Change: Rp {trx['change_amount']:,}")

    print("\n=== TEST 6: Recipe BOM Stock Auto-Deduction Verification ===")
    res = client.get("/api/inventory/ingredients?outlet_id=1")
    ingredients_after = {i["name"]: i["current_stock"] for i in res.json()}
    kopi_stock_after = ingredients_after["Biji Kopi Arabika House Blend"]
    susu_stock_after = ingredients_after["Fresh Milk UHT Full Cream"]
    print(f"Biji Kopi after: {kopi_stock_after} gr (Deducted: {kopi_stock_before - kopi_stock_after} gr)")
    print(f"Fresh Milk after: {susu_stock_after} ml (Deducted: {susu_stock_before - susu_stock_after} ml)")
    # Expected: 2 Kopi Susu = 36 gr kopi, 300 ml susu
    assert (kopi_stock_before - kopi_stock_after) == 36.0
    assert (susu_stock_before - susu_stock_after) == 300.0

    print("\n=== TEST 7: Table Status Update Verification ===")
    res = client.get("/api/tables?outlet_id=1")
    tables_after = res.json()
    meja1_after = next(t for t in tables_after if t["table_number"] == "Meja 01")
    print(f"Meja 01 status after: {meja1_after['status']}")
    assert meja1_after["status"] == "occupied"

    print("\n=== TEST 8: Dashboard & Sales Analytics ===")
    res = client.get("/api/reports/dashboard?outlet_id=1")
    assert res.status_code == 200
    dash = res.json()
    print("Dashboard Data:")
    print(f"- Today Sales: Rp {dash['today_sales']:,}")
    print(f"- Today Transactions: {dash['today_transactions']}")
    print(f"- Top Selling: {[i['name'] for i in dash['top_selling_items']]}")

    print("\n=== TEST 9: QRIS Generation ===")
    res = client.post("/api/finance/qris/generate", json={"outlet_id": 1, "amount": 50000.0})
    assert res.status_code == 200
    qris = res.json()
    print("Generated QRIS Reference:", qris["transaction_reference"])
    print("QR String:", qris["qr_string"][:40] + "...")

    print("\n=== TEST 10: Multi-Terminal Sync Status ===")
    res = client.get("/api/sync/status?outlet_id=1")
    assert res.status_code == 200
    sync_stat = res.json()
    print("Sync Status:", sync_stat)
    assert sync_stat["sync_health"] == "healthy"

    print("\n=== TEST 11: Master User / Employee CRUD Pipeline ===")
    # 1. Get Roles
    roles_res = client.get("/api/auth/roles")
    assert roles_res.status_code == 200
    roles = roles_res.json()
    print(f"Loaded {len(roles)} roles: {[r['name'] for r in roles]}")

    # 2. Create User
    new_user_payload = {
        "outlet_id": 1,
        "name": "Budi Santoso (Barista)",
        "pin": "9988",
        "role_id": 3,
        "phone": "081299998888",
        "is_active": True
    }
    create_res = client.post("/api/auth/employees", json=new_user_payload)
    assert create_res.status_code == 200
    new_user = create_res.json()
    new_user_id = new_user["id"]
    print(f"Created User: ID={new_user_id}, Name={new_user['name']}, Role={new_user['role_name']}, PIN={new_user['pin']}")
    assert new_user["name"] == "Budi Santoso (Barista)"
    assert new_user["pin"] == "9988"

    # 3. Update User
    update_payload = {
        "name": "Budi Santoso (Senior Barista)",
        "pin": "9977",
        "role_id": 2,
        "phone": "081277778888",
        "is_active": True
    }
    update_res = client.put(f"/api/auth/employees/{new_user_id}", json=update_payload)
    assert update_res.status_code == 200
    updated_user = update_res.json()
    print(f"Updated User: ID={updated_user['id']}, Name={updated_user['name']}, Role={updated_user['role_name']}, PIN={updated_user['pin']}")
    assert updated_user["name"] == "Budi Santoso (Senior Barista)"
    assert updated_user["pin"] == "9977"
    assert updated_user["role_name"] == "Store Manager"

    # 4. Verify PIN Login with updated PIN
    pin_res = client.post("/api/auth/employees/verify-pin", json={"outlet_id": 1, "pin": "9977", "employee_id": new_user_id})
    assert pin_res.status_code == 200
    assert pin_res.json()["success"] is True
    print("PIN Login Verification Succeeded for Updated User!")

    # 5. Safe Deletion Protection Guard for User with Shift
    del_guard_res = client.delete("/api/auth/employees/2")
    assert del_guard_res.status_code == 400
    print("Safe Deletion Guard verified: Shift protection prevented accidental deletion of active user.")

    # 6. Delete User
    del_res = client.delete(f"/api/auth/employees/{new_user_id}")
    assert del_res.status_code == 200
    print("Deleted User Response:", del_res.json())

    # 7. Verify User is removed
    get_res = client.get("/api/auth/employees?outlet_id=1")
    assert get_res.status_code == 200
    all_emps = get_res.json()
    assert not any(e["id"] == new_user_id for e in all_emps)
    print(f"Verified user ID={new_user_id} completely removed from database.")

    print("\n=== TEST 12: Master Ukuran & Varian (Modifier) CRUD Pipeline ===")
    # 1. Get Modifiers
    mod_res = client.get("/api/catalog/modifiers?brand_id=1")
    assert mod_res.status_code == 200
    mods = mod_res.json()
    print(f"Initial modifiers count: {len(mods)} ({[m['name'] for m in mods]})")

    # 2. Create Modifier
    create_mod_payload = {
        "brand_id": 1,
        "name": "Pilihan Susu Alternatif",
        "min_selection": 0,
        "max_selection": 1,
        "is_active": True,
        "options": [
            {"name": "Fresh Milk (Standar)", "additional_price": 0.0},
            {"name": "Oat Milk Barista", "additional_price": 8000.0},
            {"name": "Almond Milk", "additional_price": 10000.0}
        ]
    }
    create_res = client.post("/api/catalog/modifiers", json=create_mod_payload)
    assert create_res.status_code == 200
    new_mod = create_res.json()
    new_mod_id = new_mod["id"]
    print(f"Created Modifier: ID={new_mod_id}, Name={new_mod['name']}, Total Options={len(new_mod['options'])}")
    assert new_mod["name"] == "Pilihan Susu Alternatif"
    assert len(new_mod["options"]) == 3
    assert any(o["name"] == "Oat Milk Barista" and o["additional_price"] == 8000.0 for o in new_mod["options"])

    # 3. Update Modifier
    update_mod_payload = {
        "name": "Pilihan Susu Nabati Premium",
        "min_selection": 0,
        "max_selection": 1,
        "is_active": True,
        "options": [
            {"name": "Fresh Milk (Standar)", "additional_price": 0.0},
            {"name": "Oat Milk Oatside", "additional_price": 7000.0}
        ]
    }
    update_res = client.put(f"/api/catalog/modifiers/{new_mod_id}", json=update_mod_payload)
    assert update_res.status_code == 200
    updated_mod = update_res.json()
    print(f"Updated Modifier: ID={updated_mod['id']}, Name={updated_mod['name']}, Options count={len(updated_mod['options'])}")
    assert updated_mod["name"] == "Pilihan Susu Nabati Premium"
    assert len(updated_mod["options"]) == 2

    # 4. Delete Modifier
    delete_res = client.delete(f"/api/catalog/modifiers/{new_mod_id}")
    assert delete_res.status_code == 200
    print("Deleted Modifier Response:", delete_res.json())

    # 5. Verify Deletion
    mod_check_res = client.get("/api/catalog/modifiers?brand_id=1")
    assert mod_check_res.status_code == 200
    all_mods = mod_check_res.json()
    assert not any(m["id"] == new_mod_id for m in all_mods)
    print(f"Verified modifier ID={new_mod_id} completely removed from database.")

    print("\n>>> ALL 12 TESTS PASSED SUCCESSFULLY! FULL SYSTEM SYNCHRONIZED! <<<")

if __name__ == "__main__":
    run_tests()
