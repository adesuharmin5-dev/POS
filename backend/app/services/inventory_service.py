import sqlite3
from typing import List, Dict

def deduct_stock_for_transaction(conn: sqlite3.Connection, transaction_id: int):
    cursor = conn.cursor()
    # Find outlet_id of transaction
    cursor.execute("SELECT outlet_id FROM transactions WHERE id = ?", (transaction_id,))
    row = cursor.fetchone()
    if not row:
        return
    outlet_id = row["outlet_id"]

    # Get all items in transaction
    cursor.execute("""
        SELECT item_id, quantity FROM transaction_items WHERE transaction_id = ?
    """, (transaction_id,))
    items = cursor.fetchall()

    for itm in items:
        item_id = itm["item_id"]
        qty = itm["quantity"]

        # Find recipes for this item
        cursor.execute("""
            SELECT ingredient_id, quantity_used FROM recipes WHERE item_id = ?
        """, (item_id,))
        recipe_ingredients = cursor.fetchall()

        for rec in recipe_ingredients:
            ing_id = rec["ingredient_id"]
            total_deduct = rec["quantity_used"] * qty

            # Check if stock record exists
            cursor.execute("""
                SELECT current_stock FROM outlet_ingredient_stocks 
                WHERE outlet_id = ? AND ingredient_id = ?
            """, (outlet_id, ing_id))
            stock_row = cursor.fetchone()

            if stock_row:
                new_stock = stock_row["current_stock"] - total_deduct
                cursor.execute("""
                    UPDATE outlet_ingredient_stocks 
                    SET current_stock = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE outlet_id = ? AND ingredient_id = ?
                """, (new_stock, outlet_id, ing_id))
            else:
                # Initialize with negative or 0 deduction
                cursor.execute("""
                    INSERT INTO outlet_ingredient_stocks (outlet_id, ingredient_id, current_stock)
                    VALUES (?, ?, ?)
                """, (outlet_id, ing_id, -total_deduct))

def restore_stock_for_transaction(conn: sqlite3.Connection, transaction_id: int):
    cursor = conn.cursor()
    cursor.execute("SELECT outlet_id FROM transactions WHERE id = ?", (transaction_id,))
    row = cursor.fetchone()
    if not row:
        return
    outlet_id = row["outlet_id"]

    cursor.execute("""
        SELECT item_id, quantity FROM transaction_items WHERE transaction_id = ?
    """, (transaction_id,))
    items = cursor.fetchall()

    for itm in items:
        item_id = itm["item_id"]
        qty = itm["quantity"]

        cursor.execute("""
            SELECT ingredient_id, quantity_used FROM recipes WHERE item_id = ?
        """, (item_id,))
        for rec in cursor.fetchall():
            ing_id = rec["ingredient_id"]
            restore_qty = rec["quantity_used"] * qty

            cursor.execute("""
                UPDATE outlet_ingredient_stocks 
                SET current_stock = current_stock + ?, updated_at = CURRENT_TIMESTAMP
                WHERE outlet_id = ? AND ingredient_id = ?
            """, (restore_qty, outlet_id, ing_id))

def execute_stock_transfer(conn: sqlite3.Connection, transfer_id: int):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT source_outlet_id, target_outlet_id, status FROM stock_transfers WHERE id = ?
    """, (transfer_id,))
    transfer = cursor.fetchone()
    if not transfer or transfer["status"] == "received":
        return False

    src = transfer["source_outlet_id"]
    tgt = transfer["target_outlet_id"]

    cursor.execute("SELECT ingredient_id, quantity FROM stock_transfer_items WHERE transfer_id = ?", (transfer_id,))
    items = cursor.fetchall()

    for itm in items:
        ing_id = itm["ingredient_id"]
        qty = itm["quantity"]

        # Deduct from source
        cursor.execute("""
            UPDATE outlet_ingredient_stocks 
            SET current_stock = current_stock - ?, updated_at = CURRENT_TIMESTAMP
            WHERE outlet_id = ? AND ingredient_id = ?
        """, (qty, src, ing_id))

        # Add to target
        cursor.execute("""
            INSERT INTO outlet_ingredient_stocks (outlet_id, ingredient_id, current_stock)
            VALUES (?, ?, ?)
            ON CONFLICT(outlet_id, ingredient_id) DO UPDATE SET
            current_stock = current_stock + excluded.current_stock,
            updated_at = CURRENT_TIMESTAMP
        """, (tgt, ing_id, qty))

    cursor.execute("UPDATE stock_transfers SET status = 'received' WHERE id = ?", (transfer_id,))
    return True
