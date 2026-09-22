import sqlite3
import datetime
from app.models.pos import CheckoutRequest
from app.services.inventory_service import deduct_stock_for_transaction

def process_checkout(conn: sqlite3.Connection, data: CheckoutRequest) -> dict:
    cursor = conn.cursor()

    # 1. Calculate items subtotal and modifiers
    subtotal = 0.0
    processed_items = []

    for item_input in data.items:
        cursor.execute("SELECT id, name, price FROM items WHERE id = ?", (item_input.item_id,))
        item_row = cursor.fetchone()
        if not item_row:
            continue

        item_price = item_row["price"]
        item_total = item_price * item_input.quantity

        mod_total = 0.0
        applied_mods = []
        if item_input.modifiers:
            for m in item_input.modifiers:
                cursor.execute("SELECT id, name, additional_price FROM modifier_options WHERE id = ?", (m.modifier_option_id,))
                mod_row = cursor.fetchone()
                if mod_row:
                    mod_total += mod_row["additional_price"] * item_input.quantity
                    applied_mods.append({
                        "option_id": mod_row["id"],
                        "name": mod_row["name"],
                        "price": mod_row["additional_price"]
                    })

        line_subtotal = item_total + mod_total
        subtotal += line_subtotal
        processed_items.append({
            "item_id": item_row["id"],
            "name": item_row["name"],
            "quantity": item_input.quantity,
            "unit_price": item_price,
            "subtotal": line_subtotal,
            "notes": item_input.notes,
            "modifiers": applied_mods
        })

    # 2. Calculate discounts / promo
    discount_amount = 0.0
    if data.discount_id:
        cursor.execute("SELECT discount_type, value, min_order_amount FROM discounts WHERE id = ? AND is_active = 1", (data.discount_id,))
        disc = cursor.fetchone()
        if disc and subtotal >= disc["min_order_amount"]:
            if disc["discount_type"] == "percentage":
                discount_amount = (subtotal * disc["value"]) / 100.0
            else:
                discount_amount = min(disc["value"], subtotal)

    if data.promo_code:
        cursor.execute("""
            SELECT id, discount_type, discount_value, quota, used_count 
            FROM promos 
            WHERE promo_code = ? AND is_active = 1
        """, (data.promo_code,))
        promo = cursor.fetchone()
        if promo and promo["used_count"] < promo["quota"]:
            p_val = 0.0
            if promo["discount_type"] == "percentage":
                p_val = (subtotal * promo["discount_value"]) / 100.0
            else:
                p_val = min(promo["discount_value"], subtotal)
            discount_amount = max(discount_amount, p_val)
            cursor.execute("UPDATE promos SET used_count = used_count + 1 WHERE id = ?", (promo["id"],))

    taxable_amount = max(0.0, subtotal - discount_amount)

    # 3. Calculate Gratuity / Service charge
    gratuity_amount = 0.0
    cursor.execute("SELECT rate_percent FROM gratuities WHERE outlet_id = ? AND is_active = 1", (data.outlet_id,))
    grat_row = cursor.fetchone()
    if grat_row:
        gratuity_amount = (taxable_amount * grat_row["rate_percent"]) / 100.0

    # 4. Calculate Taxes (PPN / PB1)
    tax_amount = 0.0
    cursor.execute("SELECT rate_percent, is_inclusive FROM taxes WHERE outlet_id = ? AND is_active = 1", (data.outlet_id,))
    tax_row = cursor.fetchone()
    if tax_row:
        if not tax_row["is_inclusive"]:
            tax_amount = ((taxable_amount + gratuity_amount) * tax_row["rate_percent"]) / 100.0

    total_amount = round(taxable_amount + gratuity_amount + tax_amount, 2)

    # 5. Generate unique transaction number & invoice
    today_str = datetime.date.today().strftime("%Y%m%d")
    cursor.execute("SELECT COUNT(*) AS cnt FROM transactions WHERE date(created_at) = date('now')")
    count_today = cursor.fetchone()["cnt"] + 1
    trx_number = f"TRX-{today_str}-{count_today:04d}"
    inv_number = f"INV-{today_str}-{count_today:04d}"

    # 6. Insert Transaction
    cursor.execute("""
        INSERT INTO transactions (
            transaction_number, outlet_id, shift_id, cashier_id, customer_id,
            table_id, sales_type_id, subtotal, discount_amount, tax_amount,
            gratuity_amount, total_amount, payment_method, payment_status, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'paid', ?)
    """, (
        trx_number, data.outlet_id, data.shift_id, data.cashier_id, data.customer_id,
        data.table_id, data.sales_type_id, subtotal, discount_amount, tax_amount,
        gratuity_amount, total_amount, data.payment_method, data.notes
    ))
    trx_id = cursor.lastrowid

    # 7. Insert Transaction Items & Modifiers
    for itm in processed_items:
        cursor.execute("""
            INSERT INTO transaction_items (transaction_id, item_id, quantity, unit_price, subtotal_price, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (trx_id, itm["item_id"], itm["quantity"], itm["unit_price"], itm["subtotal"], itm["notes"]))
        t_item_id = cursor.lastrowid

        for mod in itm["modifiers"]:
            cursor.execute("""
                INSERT INTO transaction_item_modifiers (transaction_item_id, modifier_option_id, additional_price)
                VALUES (?, ?, ?)
            """, (t_item_id, mod["option_id"], mod["price"]))

    # 8. Create Invoice
    cursor.execute("""
        INSERT INTO invoices (invoice_number, transaction_id, issue_date, status, total_amount)
        VALUES (?, ?, date('now'), 'paid', ?)
    """, (inv_number, trx_id, total_amount))

    # 9. Update Table Status if table_id is given
    if data.table_id:
        cursor.execute("""
            UPDATE tables 
            SET status = 'occupied', current_transaction_id = ? 
            WHERE id = ?
        """, (trx_id, data.table_id))

    # 10. Auto-Deduct Inventory via Recipes (BOM)
    deduct_stock_for_transaction(conn, trx_id)

    # 11. If Shift is active and payment is Cash, update shift expected_cash
    if data.shift_id and data.payment_method.lower() == "cash":
        cursor.execute("""
            UPDATE shifts 
            SET expected_cash = expected_cash + ? 
            WHERE id = ?
        """, (total_amount, data.shift_id))

    # 12. Update Customer Loyalty & Total Spent if customer_id given
    if data.customer_id:
        points_earned = int(total_amount // 10000) # 1 point per 10k IDR
        cursor.execute("""
            UPDATE customers 
            SET loyalty_points = loyalty_points + ?, total_spent = total_spent + ?
            WHERE id = ?
        """, (points_earned, total_amount, data.customer_id))

    # 13. Log Sync
    cursor.execute("""
        INSERT INTO sync_logs (outlet_id, entity_name, action, entity_id, payload)
        VALUES (?, 'transaction', 'insert', ?, ?)
    """, (data.outlet_id, trx_id, f"Trx {trx_number} Total {total_amount}"))

    conn.commit()

    change_amount = max(0.0, (data.cash_received or 0.0) - total_amount) if data.payment_method.lower() == "cash" else 0.0

    return {
        "id": trx_id,
        "transaction_number": trx_number,
        "invoice_number": inv_number,
        "outlet_id": data.outlet_id,
        "subtotal": subtotal,
        "discount_amount": discount_amount,
        "tax_amount": tax_amount,
        "gratuity_amount": gratuity_amount,
        "total_amount": total_amount,
        "payment_method": data.payment_method,
        "payment_status": "paid",
        "cash_received": data.cash_received,
        "change_amount": change_amount,
        "created_at": datetime.datetime.now().isoformat(),
        "items": processed_items
    }
