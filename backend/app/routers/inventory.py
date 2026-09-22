from fastapi import APIRouter, Depends, HTTPException
import sqlite3
import datetime
from typing import List, Optional
from app.database import get_db
from app.models.inventory import (
    IngredientCategoryResponse, IngredientCreate, IngredientResponse,
    RecipeCreate, RecipeResponse, SupplierResponse,
    PurchaseOrderCreate, PurchaseOrderResponse,
    StockAdjustmentCreate, StockTransferCreate
)
from app.services.inventory_service import execute_stock_transfer

router = APIRouter(prefix="/inventory", tags=["Inventory & Recipes"])

# --- Ingredient Categories ---
@router.get("/categories", response_model=List[IngredientCategoryResponse])
def get_ingredient_categories(brand_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, brand_id, name, description FROM ingredient_categories WHERE brand_id = ?", (brand_id,))
    return [dict(r) for r in cursor.fetchall()]

# --- Ingredients ---
@router.get("/ingredients", response_model=List[IngredientResponse])
def get_ingredients(outlet_id: Optional[int] = None, brand_id: Optional[int] = None, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    query = """
        SELECT ing.id, ing.category_id, ic.name AS category_name, ing.name, ing.unit,
               ing.cost_per_unit, ing.min_stock_alert, ing.is_active,
               COALESCE(ois.current_stock, 0) AS current_stock
        FROM ingredients ing
        LEFT JOIN ingredient_categories ic ON ing.category_id = ic.id
        LEFT JOIN outlet_ingredient_stocks ois ON ing.id = ois.ingredient_id AND ois.outlet_id = ?
        WHERE 1=1
    """
    params = [outlet_id if outlet_id else 0]
    if brand_id:
        query += " AND ic.brand_id = ?"
        params.append(brand_id)

    query += " ORDER BY ing.id ASC"
    cursor.execute(query, params)
    return [dict(r) for r in cursor.fetchall()]

@router.post("/ingredients", response_model=IngredientResponse)
def create_ingredient(data: IngredientCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO ingredients (category_id, name, unit, cost_per_unit, min_stock_alert, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (data.category_id, data.name, data.unit, data.cost_per_unit, data.min_stock_alert, 1 if data.is_active else 0))
    ing_id = cursor.lastrowid

    if data.initial_stock_outlet_id and data.initial_stock:
        cursor.execute("""
            INSERT INTO outlet_ingredient_stocks (outlet_id, ingredient_id, current_stock)
            VALUES (?, ?, ?)
        """, (data.initial_stock_outlet_id, ing_id, data.initial_stock))

    db.commit()
    cursor.execute("""
        SELECT ing.id, ing.category_id, ic.name AS category_name, ing.name, ing.unit,
               ing.cost_per_unit, ing.min_stock_alert, ing.is_active,
               COALESCE(ois.current_stock, 0) AS current_stock
        FROM ingredients ing
        LEFT JOIN ingredient_categories ic ON ing.category_id = ic.id
        LEFT JOIN outlet_ingredient_stocks ois ON ing.id = ois.ingredient_id AND ois.outlet_id = ?
        WHERE ing.id = ?
    """, (data.initial_stock_outlet_id or 0, ing_id))
    return dict(cursor.fetchone())

# --- Recipes (Bill of Materials) ---
@router.get("/recipes/{item_id}", response_model=List[RecipeResponse])
def get_recipes_by_item(item_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT r.id, r.item_id, r.ingredient_id, ing.name AS ingredient_name, r.quantity_used, r.unit
        FROM recipes r
        JOIN ingredients ing ON r.ingredient_id = ing.id
        WHERE r.item_id = ?
    """, (item_id,))
    return [dict(r) for r in cursor.fetchall()]

@router.post("/recipes")
def set_item_recipe(data: RecipeCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    # Replace existing recipe
    cursor.execute("DELETE FROM recipes WHERE item_id = ?", (data.item_id,))
    for rec in data.recipes:
        cursor.execute("""
            INSERT INTO recipes (item_id, ingredient_id, quantity_used, unit)
            VALUES (?, ?, ?, ?)
        """, (data.item_id, rec.ingredient_id, rec.quantity_used, rec.unit))
    db.commit()
    return {"success": True, "item_id": data.item_id, "ingredients_count": len(data.recipes)}

# --- Suppliers ---
@router.get("/suppliers", response_model=List[SupplierResponse])
def get_suppliers(brand_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, brand_id, name, contact_person, phone, email, address, is_active FROM suppliers WHERE brand_id = ?", (brand_id,))
    return [dict(r) for r in cursor.fetchall()]

# --- Purchase Orders (PO) ---
@router.get("/purchase-orders", response_model=List[PurchaseOrderResponse])
def get_purchase_orders(outlet_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT po.id, po.po_number, po.supplier_id, s.name AS supplier_name,
               po.outlet_id, po.order_date, po.expected_date, po.status, po.total_amount, po.notes
        FROM purchase_orders po
        JOIN suppliers s ON po.supplier_id = s.id
        WHERE po.outlet_id = ?
        ORDER BY po.id DESC
    """, (outlet_id,))
    pos = [dict(r) for r in cursor.fetchall()]

    for p in pos:
        cursor.execute("""
            SELECT poi.ingredient_id, ing.name AS ingredient_name, poi.quantity, poi.unit_price, poi.subtotal
            FROM purchase_order_items poi
            JOIN ingredients ing ON poi.ingredient_id = ing.id
            WHERE poi.po_id = ?
        """, (p["id"],))
        p["items"] = [dict(i) for i in cursor.fetchall()]

    return pos

@router.post("/purchase-orders")
def create_purchase_order(data: PurchaseOrderCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    today_str = datetime.date.today().strftime("%Y%m%d")
    cursor.execute("SELECT COUNT(*) AS cnt FROM purchase_orders WHERE date(order_date) = date('now')")
    po_cnt = cursor.fetchone()["cnt"] + 1
    po_number = f"PO-{today_str}-{po_cnt:03d}"

    total_amount = sum(item.quantity * item.unit_price for item in data.items)

    cursor.execute("""
        INSERT INTO purchase_orders (po_number, supplier_id, outlet_id, order_date, expected_date, status, total_amount, notes)
        VALUES (?, ?, ?, ?, ?, 'ordered', ?, ?)
    """, (po_number, data.supplier_id, data.outlet_id, data.order_date, data.expected_date, total_amount, data.notes))
    po_id = cursor.lastrowid

    for item in data.items:
        subtotal = item.quantity * item.unit_price
        cursor.execute("""
            INSERT INTO purchase_order_items (po_id, ingredient_id, quantity, unit_price, subtotal)
            VALUES (?, ?, ?, ?, ?)
        """, (po_id, item.ingredient_id, item.quantity, item.unit_price, subtotal))

    db.commit()
    return {"id": po_id, "po_number": po_number, "total_amount": total_amount, "status": "ordered"}

@router.put("/purchase-orders/{po_id}/receive")
def receive_purchase_order(po_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT outlet_id, status FROM purchase_orders WHERE id = ?", (po_id,))
    po = cursor.fetchone()
    if not po or po["status"] == "received":
        raise HTTPException(status_code=400, detail="PO not found or already received")

    outlet_id = po["outlet_id"]

    cursor.execute("SELECT ingredient_id, quantity FROM purchase_order_items WHERE po_id = ?", (po_id,))
    items = cursor.fetchall()

    for itm in items:
        cursor.execute("""
            INSERT INTO outlet_ingredient_stocks (outlet_id, ingredient_id, current_stock)
            VALUES (?, ?, ?)
            ON CONFLICT(outlet_id, ingredient_id) DO UPDATE SET
            current_stock = current_stock + excluded.current_stock,
            updated_at = CURRENT_TIMESTAMP
        """, (outlet_id, itm["ingredient_id"], itm["quantity"]))

    cursor.execute("UPDATE purchase_orders SET status = 'received' WHERE id = ?", (po_id,))
    db.commit()
    return {"success": True, "status": "received", "po_id": po_id}

# --- Stock Adjustments (Adjusment) ---
@router.post("/adjustments")
def create_stock_adjustment(data: StockAdjustmentCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO stock_adjustments (outlet_id, date, reason, adjusted_by)
        VALUES (?, date('now'), ?, ?)
    """, (data.outlet_id, data.reason, data.adjusted_by))
    adj_id = cursor.lastrowid

    for itm in data.items:
        cursor.execute("SELECT current_stock FROM outlet_ingredient_stocks WHERE outlet_id = ? AND ingredient_id = ?", (data.outlet_id, itm.ingredient_id))
        row = cursor.fetchone()
        system_stock = row["current_stock"] if row else 0.0
        diff = itm.actual_stock - system_stock

        cursor.execute("""
            INSERT INTO stock_adjustment_items (adjustment_id, ingredient_id, system_stock, actual_stock, difference)
            VALUES (?, ?, ?, ?, ?)
        """, (adj_id, itm.ingredient_id, system_stock, itm.actual_stock, diff))

        # Update actual stock
        cursor.execute("""
            INSERT INTO outlet_ingredient_stocks (outlet_id, ingredient_id, current_stock)
            VALUES (?, ?, ?)
            ON CONFLICT(outlet_id, ingredient_id) DO UPDATE SET
            current_stock = excluded.current_stock,
            updated_at = CURRENT_TIMESTAMP
        """, (data.outlet_id, itm.ingredient_id, itm.actual_stock))

    db.commit()
    return {"success": True, "adjustment_id": adj_id}

# --- Stock Transfers (Transfer Antar Cabang) ---
@router.post("/transfers")
def create_stock_transfer(data: StockTransferCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    today_str = datetime.date.today().strftime("%Y%m%d")
    cursor.execute("SELECT COUNT(*) AS cnt FROM stock_transfers WHERE date(transfer_date) = date('now')")
    tr_cnt = cursor.fetchone()["cnt"] + 1
    transfer_number = f"TRF-{today_str}-{tr_cnt:03d}"

    cursor.execute("""
        INSERT INTO stock_transfers (transfer_number, source_outlet_id, target_outlet_id, transfer_date, status, notes)
        VALUES (?, ?, ?, date('now'), 'in_transit', ?)
    """, (transfer_number, data.source_outlet_id, data.target_outlet_id, data.notes))
    trf_id = cursor.lastrowid

    for itm in data.items:
        cursor.execute("""
            INSERT INTO stock_transfer_items (transfer_id, ingredient_id, quantity)
            VALUES (?, ?, ?)
        """, (trf_id, itm.ingredient_id, itm.quantity))

    db.commit()
    return {"success": True, "transfer_id": trf_id, "transfer_number": transfer_number, "status": "in_transit"}

@router.put("/transfers/{transfer_id}/receive")
def receive_transfer(transfer_id: int, db: sqlite3.Connection = Depends(get_db)):
    success = execute_stock_transfer(db, transfer_id)
    if not success:
        raise HTTPException(status_code=400, detail="Transfer not found or already completed")
    db.commit()
    return {"success": True, "status": "received", "transfer_id": transfer_id}
