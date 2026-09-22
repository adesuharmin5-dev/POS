from fastapi import APIRouter, Depends, HTTPException
import sqlite3
import uuid
import datetime
from typing import List
from app.database import get_db
from app.models.finance import (
    TaxBase, TaxResponse,
    GratuityBase, GratuityResponse,
    BankAccountBase, BankAccountResponse,
    QRISConfigBase, QRISConfigResponse,
    QRISGenerateRequest, QRISResponse
)

router = APIRouter(prefix="/finance", tags=["Taxes, Gratuity & Payments"])

# --- Taxes ---
@router.get("/taxes", response_model=List[TaxResponse])
def get_taxes(outlet_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, outlet_id, name, rate_percent, is_inclusive, is_active FROM taxes WHERE outlet_id = ?", (outlet_id,))
    return [dict(r) for r in cursor.fetchall()]

@router.post("/taxes", response_model=TaxResponse)
def create_tax(data: TaxBase, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO taxes (outlet_id, name, rate_percent, is_inclusive, is_active)
        VALUES (?, ?, ?, ?, ?)
    """, (data.outlet_id, data.name, data.rate_percent, 1 if data.is_inclusive else 0, 1 if data.is_active else 0))
    t_id = cursor.lastrowid
    db.commit()
    cursor.execute("SELECT id, outlet_id, name, rate_percent, is_inclusive, is_active FROM taxes WHERE id = ?", (t_id,))
    return dict(cursor.fetchone())

@router.put("/taxes/{tax_id}", response_model=TaxResponse)
def update_tax(tax_id: int, data: TaxBase, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        UPDATE taxes
        SET outlet_id = ?, name = ?, rate_percent = ?, is_inclusive = ?, is_active = ?
        WHERE id = ?
    """, (data.outlet_id, data.name, data.rate_percent, 1 if data.is_inclusive else 0, 1 if data.is_active else 0, tax_id))
    db.commit()
    cursor.execute("SELECT id, outlet_id, name, rate_percent, is_inclusive, is_active FROM taxes WHERE id = ?", (tax_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Data pajak tidak ditemukan")
    return dict(row)

# --- Gratuities (Service Charge) ---
@router.get("/gratuities", response_model=List[GratuityResponse])
def get_gratuities(outlet_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, outlet_id, name, rate_percent, is_active FROM gratuities WHERE outlet_id = ?", (outlet_id,))
    return [dict(r) for r in cursor.fetchall()]

@router.post("/gratuities", response_model=GratuityResponse)
def create_gratuity(data: GratuityBase, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO gratuities (outlet_id, name, rate_percent, is_active)
        VALUES (?, ?, ?, ?)
    """, (data.outlet_id, data.name, data.rate_percent, 1 if data.is_active else 0))
    g_id = cursor.lastrowid
    db.commit()
    cursor.execute("SELECT id, outlet_id, name, rate_percent, is_active FROM gratuities WHERE id = ?", (g_id,))
    return dict(cursor.fetchone())

# --- Bank Accounts ---
@router.get("/bank-accounts", response_model=List[BankAccountResponse])
def get_bank_accounts(outlet_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, outlet_id, bank_name, account_number, account_holder, is_active FROM bank_accounts WHERE outlet_id = ?", (outlet_id,))
    return [dict(r) for r in cursor.fetchall()]

# --- QRIS Config & Generation ---
@router.get("/qris/config", response_model=QRISConfigResponse)
def get_qris_config(outlet_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, outlet_id, merchant_name, merchant_id, nmid, api_key, is_active FROM qris_configs WHERE outlet_id = ?", (outlet_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="QRIS configuration not found for this outlet")
    return dict(row)

@router.post("/qris/generate", response_model=QRISResponse)
def generate_qris(data: QRISGenerateRequest, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT merchant_name, nmid FROM qris_configs WHERE outlet_id = ? AND is_active = 1", (data.outlet_id,))
    cfg = cursor.fetchone()
    if not cfg:
        merchant_name = "Aurora Cafe"
        nmid = "ID1020000123456"
    else:
        merchant_name = cfg["merchant_name"]
        nmid = cfg["nmid"]

    ref = f"QRIS-{datetime.date.today().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    # Standard QRIS EMVCo simulation string
    qr_string = f"00020101021226610014ID.LINKAJA.WWW01189360091800000000010215{nmid}51440014ID.CO.QRIS.WWW0215{nmid}520458125303360540{int(data.amount)}5802ID5911{merchant_name}6007BANDUNG62180714{ref}6304"
    expiry = (datetime.datetime.now() + datetime.timedelta(minutes=15)).isoformat()

    cursor.execute("""
        INSERT INTO qris_transactions (transaction_id, qr_string, transaction_reference, amount, status, expiry_time)
        VALUES (?, ?, ?, ?, 'pending', ?)
    """, (data.transaction_id, qr_string, ref, data.amount, expiry))
    q_id = cursor.lastrowid
    db.commit()

    return {
        "id": q_id,
        "transaction_reference": ref,
        "qr_string": qr_string,
        "amount": data.amount,
        "status": "pending",
        "expiry_time": expiry
    }

@router.get("/qris/check/{reference}")
def check_qris_status(reference: str, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, transaction_reference, amount, status, expiry_time FROM qris_transactions WHERE transaction_reference = ?", (reference,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="QRIS transaction reference not found")
    return dict(row)
