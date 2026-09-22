from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
import sqlite3
import uuid
from pathlib import Path
from typing import Optional, List, Dict
from app.database import get_db
from app.models.settings import (
    StoreSettingsUpdate, StoreSettingsResponse,
    ReceiptSettingsUpdate, ReceiptSettingsResponse,
    AccountProfileUpdate
)

router = APIRouter(prefix="/settings", tags=["Store & System Settings"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "static" / "img" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_RECEIPT_SETTINGS = {
    "receipt_header": "TERAS MANIS CAFE & RESTO",
    "receipt_footer": "Terima kasih atas kunjungan Anda! Follow IG: @terasmanis.cafe",
    "show_logo": "true",
    "show_wifi": "true",
    "wifi_ssid": "TerasManis_Guest",
    "wifi_password": "kopiterasmanis",
    "tax_id": "01.892.481.0-421.000",
    "instagram": "@terasmanis.cafe",
    "tax_enabled": "true",
    "tax_rate": "10.0",
    "tax_name": "PB1 / Pajak Restoran",
    "show_tax_on_receipt": "true",
    "paper_width": "58mm"
}

@router.get("/store", response_model=StoreSettingsResponse)
def get_store_settings(outlet_id: int = 1, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT o.id AS outlet_id, o.brand_id, o.name, b.name AS brand_name,
               o.address, o.phone, o.email, b.logo, b.description
        FROM outlets o
        JOIN brands b ON o.brand_id = b.id
        WHERE o.id = ?
    """, (outlet_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Data outlet / toko tidak ditemukan")
    return dict(row)

@router.put("/store", response_model=StoreSettingsResponse)
def update_store_settings(data: StoreSettingsUpdate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT brand_id FROM outlets WHERE id = ?", (data.outlet_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Data outlet tidak ditemukan")
    brand_id = row["brand_id"]

    cursor.execute("""
        UPDATE outlets
        SET name = ?, address = ?, phone = ?, email = ?
        WHERE id = ?
    """, (data.name, data.address, data.phone, data.email, data.outlet_id))

    brand_name = data.brand_name or data.name
    logo_val = data.logo.strip() if (data.logo and data.logo.strip()) else None
    if logo_val:
        cursor.execute("""
            UPDATE brands
            SET name = ?, logo = ?, description = ?
            WHERE id = ?
        """, (brand_name, logo_val, data.description, brand_id))
    else:
        cursor.execute("""
            UPDATE brands
            SET name = ?, description = ?
            WHERE id = ?
        """, (brand_name, data.description, brand_id))

    db.commit()

    cursor.execute("""
        SELECT o.id AS outlet_id, o.brand_id, o.name, b.name AS brand_name,
               o.address, o.phone, o.email, b.logo, b.description
        FROM outlets o
        JOIN brands b ON o.brand_id = b.id
        WHERE o.id = ?
    """, (data.outlet_id,))
    return dict(cursor.fetchone())

@router.get("/receipt", response_model=ReceiptSettingsResponse)
def get_receipt_settings(outlet_id: int = 1, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT setting_key, setting_value FROM settings WHERE outlet_id = ?", (outlet_id,))
    stored = {r["setting_key"]: r["setting_value"] for r in cursor.fetchall()}

    merged = {**DEFAULT_RECEIPT_SETTINGS, **stored}

    # Query tax settings from taxes table for sync
    cursor.execute("SELECT id, name, rate_percent, is_active FROM taxes WHERE outlet_id = ? ORDER BY id ASC LIMIT 1", (outlet_id,))
    tax_row = cursor.fetchone()
    if tax_row:
        tax_enabled = (tax_row["is_active"] == 1)
        tax_rate = float(tax_row["rate_percent"])
        tax_name = tax_row["name"] or "PB1 / Pajak Restoran"
    else:
        tax_enabled = merged.get("tax_enabled", "true").lower() in ("true", "1", "yes")
        try:
            tax_rate = float(merged.get("tax_rate", "10.0"))
        except (ValueError, TypeError):
            tax_rate = 10.0
        tax_name = merged.get("tax_name", DEFAULT_RECEIPT_SETTINGS["tax_name"])

    return {
        "outlet_id": outlet_id,
        "receipt_header": merged.get("receipt_header", DEFAULT_RECEIPT_SETTINGS["receipt_header"]),
        "receipt_footer": merged.get("receipt_footer", DEFAULT_RECEIPT_SETTINGS["receipt_footer"]),
        "show_logo": merged.get("show_logo", "true").lower() in ("true", "1", "yes"),
        "show_wifi": merged.get("show_wifi", "true").lower() in ("true", "1", "yes"),
        "wifi_ssid": merged.get("wifi_ssid", DEFAULT_RECEIPT_SETTINGS["wifi_ssid"]),
        "wifi_password": merged.get("wifi_password", DEFAULT_RECEIPT_SETTINGS["wifi_password"]),
        "tax_id": merged.get("tax_id", DEFAULT_RECEIPT_SETTINGS["tax_id"]),
        "instagram": merged.get("instagram", DEFAULT_RECEIPT_SETTINGS["instagram"]),
        "tax_enabled": tax_enabled,
        "tax_rate": tax_rate,
        "tax_name": tax_name,
        "show_tax_on_receipt": merged.get("show_tax_on_receipt", "true").lower() in ("true", "1", "yes"),
        "paper_width": merged.get("paper_width", DEFAULT_RECEIPT_SETTINGS["paper_width"])
    }

@router.get("/account")
def get_account_profile(employee_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT e.id, e.name, e.phone, e.role_id, r.name AS role_name,
               o.id AS outlet_id, o.name AS outlet_name, b.name AS brand_name
        FROM employees e
        LEFT JOIN roles r ON e.role_id = r.id
        LEFT JOIN outlets o ON e.outlet_id = o.id
        LEFT JOIN brands b ON o.brand_id = b.id
        WHERE e.id = ?
    """, (employee_id,))
    emp = cursor.fetchone()
    if not emp:
        raise HTTPException(status_code=404, detail="Akun karyawan tidak ditemukan")
    return dict(emp)

@router.put("/receipt", response_model=ReceiptSettingsResponse)
def update_receipt_settings(data: ReceiptSettingsUpdate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    settings_dict = {
        "receipt_header": data.receipt_header,
        "receipt_footer": data.receipt_footer,
        "show_logo": "true" if data.show_logo else "false",
        "show_wifi": "true" if data.show_wifi else "false",
        "wifi_ssid": data.wifi_ssid,
        "wifi_password": data.wifi_password,
        "tax_id": data.tax_id,
        "instagram": data.instagram,
        "tax_enabled": "true" if data.tax_enabled else "false",
        "tax_rate": str(data.tax_rate if data.tax_rate is not None else 10.0),
        "tax_name": data.tax_name or "PB1 / Pajak Restoran",
        "show_tax_on_receipt": "true" if data.show_tax_on_receipt else "false",
        "paper_width": data.paper_width or "58mm"
    }

    for key, val in settings_dict.items():
        if val is not None:
            cursor.execute("""
                INSERT INTO settings (outlet_id, setting_key, setting_value)
                VALUES (?, ?, ?)
                ON CONFLICT(outlet_id, setting_key) DO UPDATE SET setting_value = excluded.setting_value
            """, (data.outlet_id, key, str(val)))

    # Synchronize with taxes table for POS transaction engine
    if data.tax_rate is not None or data.tax_enabled is not None or data.tax_name is not None:
        cursor.execute("SELECT id FROM taxes WHERE outlet_id = ? ORDER BY id ASC LIMIT 1", (data.outlet_id,))
        tax_row = cursor.fetchone()
        t_active = 1 if data.tax_enabled else 0
        t_rate = float(data.tax_rate if data.tax_rate is not None else 10.0)
        t_name = (data.tax_name or "PB1 / Pajak Restoran").strip()
        if tax_row:
            cursor.execute("""
                UPDATE taxes
                SET name = ?, rate_percent = ?, is_active = ?
                WHERE id = ?
            """, (t_name, t_rate, t_active, tax_row["id"]))
        else:
            cursor.execute("""
                INSERT INTO taxes (outlet_id, name, rate_percent, is_inclusive, is_active)
                VALUES (?, ?, ?, 0, ?)
            """, (data.outlet_id, t_name, t_rate, t_active))

    db.commit()
    return get_receipt_settings(outlet_id=data.outlet_id, db=db)

@router.put("/account")
def update_account_profile(data: AccountProfileUpdate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT e.id, e.name, e.pin, e.phone, e.role_id, r.name AS role_name
        FROM employees e
        LEFT JOIN roles r ON e.role_id = r.id
        WHERE e.id = ?
    """, (data.employee_id,))
    emp = cursor.fetchone()
    if not emp:
        raise HTTPException(status_code=404, detail="Akun karyawan tidak ditemukan")

    pin_to_save = emp["pin"]
    if data.new_pin:
        clean_new_pin = str(data.new_pin).strip()
        if not clean_new_pin.isdigit() or len(clean_new_pin) < 4 or len(clean_new_pin) > 6:
            raise HTTPException(status_code=400, detail="PIN baru harus berupa 4-6 digit angka")
        
        # Verify current pin if provided
        if data.current_pin:
            clean_curr_pin = str(data.current_pin).strip()
            if clean_curr_pin != str(emp["pin"]).strip():
                raise HTTPException(status_code=400, detail="PIN lama yang dimasukkan tidak cocok")
        pin_to_save = clean_new_pin

    cursor.execute("""
        UPDATE employees
        SET name = ?, phone = ?, pin = ?
        WHERE id = ?
    """, (data.name.strip(), data.phone, pin_to_save, data.employee_id))
    db.commit()

    cursor.execute("""
        SELECT e.id, e.name, e.pin, e.phone, e.role_id, r.name AS role_name
        FROM employees e
        LEFT JOIN roles r ON e.role_id = r.id
        WHERE e.id = ?
    """, (data.employee_id,))
    updated_emp = dict(cursor.fetchone())

    return {
        "success": True,
        "message": "Profil akun berhasil diperbarui",
        "employee": updated_emp
    }

@router.post("/upload-logo")
async def upload_logo(file: UploadFile = File(...)):
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp", ".svg"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Format logo harus berupa JPG, PNG, WEBP, atau SVG")

    unique_filename = f"logo_{uuid.uuid4().hex[:8]}{ext}"
    file_path = UPLOAD_DIR / unique_filename

    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    return {
        "success": True,
        "image_url": f"/static/img/uploads/{unique_filename}",
        "filename": unique_filename
    }
