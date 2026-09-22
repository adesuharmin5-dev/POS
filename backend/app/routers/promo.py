from fastapi import APIRouter, Depends, HTTPException
import sqlite3
from typing import List
from app.database import get_db
from app.models.promo import (
    CustomerCreate, CustomerResponse,
    DiscountBase, DiscountResponse,
    PromoBase, PromoResponse,
    CampaignBase, CampaignResponse
)

router = APIRouter(prefix="/promo", tags=["Promotions, Discounts & Customers"])

# --- Customers (Konsumen List) ---
@router.get("/customers", response_model=List[CustomerResponse])
def get_customers(brand_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, brand_id, name, phone, email, loyalty_points, total_spent, created_at
        FROM customers WHERE brand_id = ?
        ORDER BY total_spent DESC
    """, (brand_id,))
    return [dict(r) for r in cursor.fetchall()]

@router.post("/customers", response_model=CustomerResponse)
def create_customer(data: CustomerCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    try:
        cursor.execute("""
            INSERT INTO customers (brand_id, name, phone, email)
            VALUES (?, ?, ?, ?)
        """, (data.brand_id, data.name, data.phone, data.email))
        c_id = cursor.lastrowid
        db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Nomor telepon pelanggan sudah terdaftar")

    cursor.execute("SELECT id, brand_id, name, phone, email, loyalty_points, total_spent, created_at FROM customers WHERE id = ?", (c_id,))
    return dict(cursor.fetchone())

# --- Discounts (Diskon) ---
@router.get("/discounts", response_model=List[DiscountResponse])
def get_discounts(brand_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, brand_id, name, discount_type, value, min_order_amount, is_active FROM discounts WHERE brand_id = ?", (brand_id,))
    return [dict(r) for r in cursor.fetchall()]

@router.post("/discounts", response_model=DiscountResponse)
def create_discount(data: DiscountBase, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO discounts (brand_id, name, discount_type, value, min_order_amount, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (data.brand_id, data.name, data.discount_type, data.value, data.min_order_amount, 1 if data.is_active else 0))
    d_id = cursor.lastrowid
    db.commit()
    cursor.execute("SELECT id, brand_id, name, discount_type, value, min_order_amount, is_active FROM discounts WHERE id = ?", (d_id,))
    return dict(cursor.fetchone())

# --- Promos ---
@router.get("/promos", response_model=List[PromoResponse])
def get_promos(brand_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, brand_id, name, promo_code, discount_type, discount_value, start_date, end_date, quota, used_count, is_active FROM promos WHERE brand_id = ?", (brand_id,))
    return [dict(r) for r in cursor.fetchall()]

@router.post("/promos", response_model=PromoResponse)
def create_promo(data: PromoBase, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO promos (brand_id, name, promo_code, discount_type, discount_value, start_date, end_date, quota, used_count, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data.brand_id, data.name, data.promo_code, data.discount_type, data.discount_value, data.start_date, data.end_date, data.quota, data.used_count, 1 if data.is_active else 0))
    p_id = cursor.lastrowid
    db.commit()
    cursor.execute("SELECT id, brand_id, name, promo_code, discount_type, discount_value, start_date, end_date, quota, used_count, is_active FROM promos WHERE id = ?", (p_id,))
    return dict(cursor.fetchone())

# --- Campaigns ---
@router.get("/campaigns", response_model=List[CampaignResponse])
def get_campaigns(brand_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, brand_id, name, target_audience, message, start_date, end_date, status FROM campaigns WHERE brand_id = ?", (brand_id,))
    return [dict(r) for r in cursor.fetchall()]
