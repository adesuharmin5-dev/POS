from fastapi import APIRouter, Depends, HTTPException
import sqlite3
from typing import List, Optional
from app.database import get_db
from app.models.pos import CheckoutRequest, SalesTypeResponse
from app.services.pos_service import process_checkout
from app.services.inventory_service import restore_stock_for_transaction

router = APIRouter(prefix="/pos", tags=["POS Transactions & Invoicing"])

# --- Sales Types ---
@router.get("/sales-types", response_model=List[SalesTypeResponse])
def get_sales_types(outlet_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, outlet_id, name, is_active FROM sales_types WHERE outlet_id = ?", (outlet_id,))
    return [dict(r) for r in cursor.fetchall()]

# --- POS Checkout ---
@router.post("/checkout")
def checkout(data: CheckoutRequest, db: sqlite3.Connection = Depends(get_db)):
    try:
        res = process_checkout(db, data)
        return res
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# --- Transactions List ---
@router.get("/transactions")
def get_transactions(
    outlet_id: int,
    date: Optional[str] = None,
    limit: int = 50,
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    query = """
        SELECT t.id, t.transaction_number, t.outlet_id, t.shift_id, e.name AS cashier_name,
               c.name AS customer_name, tbl.table_number, st.name AS sales_type_name,
               t.subtotal, t.discount_amount, t.tax_amount, t.gratuity_amount, t.total_amount,
               t.payment_method, t.payment_status, t.created_at, inv.invoice_number
        FROM transactions t
        LEFT JOIN employees e ON t.cashier_id = e.id
        LEFT JOIN customers c ON t.customer_id = c.id
        LEFT JOIN tables tbl ON t.table_id = tbl.id
        LEFT JOIN sales_types st ON t.sales_type_id = st.id
        LEFT JOIN invoices inv ON t.id = inv.transaction_id
        WHERE t.outlet_id = ?
    """
    params = [outlet_id]
    if date:
        query += " AND date(t.created_at) = ?"
        params.append(date)

    query += " ORDER BY t.id DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    trxs = [dict(r) for r in cursor.fetchall()]

    for trx in trxs:
        cursor.execute("""
            SELECT ti.item_id, i.name AS item_name, ti.quantity, ti.unit_price, ti.subtotal_price, ti.notes
            FROM transaction_items ti
            JOIN items i ON ti.item_id = i.id
            WHERE ti.transaction_id = ?
        """, (trx["id"],))
        trx["items"] = [dict(i) for i in cursor.fetchall()]

    return trxs

# --- Void Transaction (Cancel & Restore Stock) ---
@router.post("/transactions/{transaction_id}/void")
def void_transaction(transaction_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, outlet_id, table_id, payment_status, total_amount, payment_method, shift_id FROM transactions WHERE id = ?", (transaction_id,))
    trx = cursor.fetchone()
    if not trx or trx["payment_status"] == "cancelled":
        raise HTTPException(status_code=400, detail="Transaction not found or already cancelled")

    # 1. Update status
    cursor.execute("UPDATE transactions SET payment_status = 'cancelled' WHERE id = ?", (transaction_id,))
    cursor.execute("UPDATE invoices SET status = 'void' WHERE transaction_id = ?", (transaction_id,))

    # 2. Release table if assigned
    if trx["table_id"]:
        cursor.execute("UPDATE tables SET status = 'available', current_transaction_id = NULL WHERE id = ?", (trx["table_id"],))

    # 3. Restore Stock
    restore_stock_for_transaction(db, transaction_id)

    # 4. If cash and shift active, deduct from shift expected cash
    if trx["shift_id"] and trx["payment_method"].lower() == "cash":
        cursor.execute("UPDATE shifts SET expected_cash = expected_cash - ? WHERE id = ?", (trx["total_amount"], trx["shift_id"]))

    db.commit()
    return {"success": True, "transaction_id": transaction_id, "status": "cancelled"}

# --- Invoices List ---
@router.get("/invoices")
def get_invoices(outlet_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT inv.id, inv.invoice_number, inv.transaction_id, t.transaction_number,
               inv.issue_date, inv.status, inv.total_amount, t.payment_method
        FROM invoices inv
        JOIN transactions t ON inv.transaction_id = t.id
        WHERE t.outlet_id = ?
        ORDER BY inv.id DESC
    """, (outlet_id,))
    return [dict(r) for r in cursor.fetchall()]
