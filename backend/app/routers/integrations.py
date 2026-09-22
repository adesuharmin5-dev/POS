from fastapi import APIRouter, Depends, HTTPException
import sqlite3
import json
from typing import List
from app.database import get_db
from app.models.integration import (
    MobileOrderCreate, MobileOrderResponse,
    GoFoodConfig, PartnerResponse
)

router = APIRouter(prefix="/integrations", tags=["Integrations & Mobile Orders"])

# --- Mobile / QR Order (Moke Order) ---
@router.post("/orders/mobile", response_model=MobileOrderResponse)
def submit_mobile_order(data: MobileOrderCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    items_str = json.dumps(data.items)

    cursor.execute("""
        INSERT INTO mobile_orders (outlet_id, table_id, customer_name, customer_phone, items_json, total_amount, status)
        VALUES (?, ?, ?, ?, ?, ?, 'pending')
    """, (data.outlet_id, data.table_id, data.customer_name, data.customer_phone, items_str, data.total_amount))
    order_id = cursor.lastrowid
    db.commit()

    cursor.execute("""
        SELECT id, outlet_id, table_id, customer_name, customer_phone, items_json, total_amount, status, created_at
        FROM mobile_orders WHERE id = ?
    """, (order_id,))
    return dict(cursor.fetchone())

@router.get("/orders/mobile", response_model=List[MobileOrderResponse])
def get_mobile_orders(outlet_id: int, status: str = "pending", db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, outlet_id, table_id, customer_name, customer_phone, items_json, total_amount, status, created_at
        FROM mobile_orders 
        WHERE outlet_id = ? AND status = ?
        ORDER BY id DESC
    """, (outlet_id, status))
    return [dict(r) for r in cursor.fetchall()]

@router.put("/orders/mobile/{order_id}/status")
def update_mobile_order_status(order_id: int, status: str, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("UPDATE mobile_orders SET status = ? WHERE id = ?", (status, order_id))
    db.commit()
    return {"success": True, "order_id": order_id, "status": status}

# --- GoFood Integration ---
@router.get("/gofood", response_model=GoFoodConfig)
def get_gofood_config(outlet_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT outlet_id, store_id, is_integrated, auto_accept_order FROM gofood_integrations WHERE outlet_id = ?", (outlet_id,))
    row = cursor.fetchone()
    if not row:
        return {"outlet_id": outlet_id, "store_id": "GOFOOD-AURORA-01", "is_integrated": True, "auto_accept_order": True}
    return dict(row)

# --- Partners ---
@router.get("/partners", response_model=List[PartnerResponse])
def get_partners(brand_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, brand_id, partner_name, partner_type, status FROM partners WHERE brand_id = ?", (brand_id,))
    return [dict(r) for r in cursor.fetchall()]
