import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db

client = TestClient(app)

def test_receipt_and_tax_flow():
    print("=== 1. Testing GET /api/settings/receipt (Initial) ===")
    res = client.get("/api/settings/receipt?outlet_id=1")
    assert res.status_code == 200, f"Error: {res.text}"
    data = res.json()
    print("Initial Receipt Settings:", data)
    assert "tax_enabled" in data
    assert "tax_rate" in data
    assert "tax_name" in data
    assert "show_tax_on_receipt" in data
    assert "paper_width" in data

    print("\n=== 2. Testing PUT /api/settings/receipt (Disable Tax: Opsi Bebas Pajak) ===")
    update_payload = {
        "outlet_id": 1,
        "receipt_header": "TERAS MANIS CAFE TEST",
        "tax_id": "01.892.481.0-421.000",
        "show_logo": True,
        "show_wifi": True,
        "wifi_ssid": "TerasManis_Free",
        "wifi_password": "ngopiyuk",
        "instagram": "@terasmanis.test",
        "receipt_footer": "Struk Uji Coba Bebas Pajak",
        "tax_enabled": False,
        "tax_rate": 0.0,
        "tax_name": "Bebas Pajak",
        "show_tax_on_receipt": False,
        "paper_width": "58mm"
    }
    put_res = client.put("/api/settings/receipt", json=update_payload)
    assert put_res.status_code == 200, f"Error: {put_res.text}"
    put_data = put_res.json()
    print("Updated Settings (Tax Disabled):", put_data)
    assert put_data["tax_enabled"] == False
    assert put_data["tax_rate"] == 0.0
    assert put_data["tax_name"] == "Bebas Pajak"

    # Check taxes table in database
    tax_res = client.get("/api/finance/taxes?outlet_id=1")
    assert tax_res.status_code == 200
    taxes = tax_res.json()
    print("Taxes table in DB after disable:", taxes)
    assert len(taxes) >= 1
    t1 = next(t for t in taxes if t["outlet_id"] == 1)
    assert t1["is_active"] == 0 or t1["is_active"] == False, "Tax should be inactive in DB"

    print("\n=== 3. Testing PUT /api/settings/receipt (Enable Tax: 11% PPN) ===")
    update_payload_ppn = {
        "outlet_id": 1,
        "receipt_header": "TERAS MANIS CAFE & ROASTERY",
        "tax_id": "01.892.481.0-421.000",
        "show_logo": True,
        "show_wifi": True,
        "wifi_ssid": "TerasManis_Guest",
        "wifi_password": "kopiterasmanis",
        "instagram": "@terasmanis.cafe",
        "receipt_footer": "Terima kasih atas kunjungan Anda!",
        "tax_enabled": True,
        "tax_rate": 11.0,
        "tax_name": "PPN 11%",
        "show_tax_on_receipt": True,
        "paper_width": "80mm"
    }
    put_res2 = client.put("/api/settings/receipt", json=update_payload_ppn)
    assert put_res2.status_code == 200, f"Error: {put_res2.text}"
    put_data2 = put_res2.json()
    print("Updated Settings (PPN 11% Active):", put_data2)
    assert put_data2["tax_enabled"] == True
    assert put_data2["tax_rate"] == 11.0
    assert put_data2["tax_name"] == "PPN 11%"
    assert put_data2["paper_width"] == "80mm"

    # Check taxes table in database again
    tax_res2 = client.get("/api/finance/taxes?outlet_id=1")
    taxes2 = tax_res2.json()
    print("Taxes table in DB after enable 11%:", taxes2)
    t2 = next(t for t in taxes2 if t["outlet_id"] == 1)
    assert t2["is_active"] == 1 or t2["is_active"] == True, "Tax should be active"
    assert t2["rate_percent"] == 11.0, "Tax rate should be 11.0%"
    assert t2["name"] == "PPN 11%"

    print("\n=== 4. Testing POS Checkout with 11% Tax Calculation ===")
    # Get active shift and active cashier
    shift_res = client.get("/api/shifts/current?outlet_id=1")
    shift_data = shift_res.json()
    if shift_data and "id" in shift_data:
        shift_id = shift_data["id"]
    else:
        open_shift = client.post("/api/shifts/open", json={
            "outlet_id": 1,
            "employee_id": 1,
            "initial_cash": 100000
        })
        shift_id = open_shift.json()["id"]

    # Checkout test: item 1 with qty 2
    items_res = client.get("/api/catalog/items?outlet_id=1")
    items = items_res.json()
    item1 = items[0]
    item1_price = item1["price"]

    checkout_payload = {
        "outlet_id": 1,
        "shift_id": shift_id,
        "cashier_id": 1,
        "sales_type_id": 1,
        "items": [
            {
                "item_id": item1["id"],
                "quantity": 2,
                "unit_price": item1_price,
                "modifiers": []
            }
        ],
        "payment_method": "Cash",
        "cash_received": 100000.0,
        "notes": "Testing tax calculation 11%"
    }
    trx_res = client.post("/api/pos/checkout", json=checkout_payload)
    assert trx_res.status_code == 200, f"Checkout failed: {trx_res.text}"
    trx_data = trx_res.json()
    print(f"Transaction Success: {trx_data['transaction_number']}")
    print(f"Subtotal: {trx_data['subtotal']}")
    print(f"Gratuity: {trx_data['gratuity_amount']}")
    print(f"Tax Amount: {trx_data['tax_amount']}")
    print(f"Total Amount: {trx_data['total_amount']}")

    expected_subtotal = item1_price * 2
    expected_grat = (expected_subtotal * 5.0) / 100.0
    expected_tax = round(((expected_subtotal + expected_grat) * 11.0) / 100.0, 2)
    assert abs(trx_data["tax_amount"] - expected_tax) < 0.05, f"Tax {trx_data['tax_amount']} != expected {expected_tax}"
    print(f"Verified: Backend calculated {trx_data['tax_amount']} precisely matches 11% PPN calculation!")

    print("\n=== 5. Resetting Settings to Standard 10% PB1 ===")
    reset_payload = {
        "outlet_id": 1,
        "receipt_header": "TERAS MANIS CAFE & ROASTERY",
        "tax_id": "01.892.481.0-421.000",
        "show_logo": True,
        "show_wifi": True,
        "wifi_ssid": "TerasManis_Guest",
        "wifi_password": "kopiterasmanis",
        "instagram": "@terasmanis.cafe",
        "receipt_footer": "Terima kasih atas kunjungan Anda! Follow IG: @terasmanis.cafe",
        "tax_enabled": True,
        "tax_rate": 10.0,
        "tax_name": "PB1 / Pajak Restoran",
        "show_tax_on_receipt": True,
        "paper_width": "58mm"
    }
    reset_res = client.put("/api/settings/receipt", json=reset_payload)
    assert reset_res.status_code == 200
    print("Reset Settings Success:", reset_res.json()["tax_name"], f"{reset_res.json()['tax_rate']}%")

    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY! [OK]")

if __name__ == "__main__":
    test_receipt_and_tax_flow()
