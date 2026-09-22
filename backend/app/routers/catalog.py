from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
import sqlite3
import uuid
import shutil
from pathlib import Path
from typing import List, Optional
from app.database import get_db
from app.models.catalog import (
    CategoryCreate, CategoryUpdate, CategoryResponse,
    ItemCreate, ItemUpdate, ItemResponse, PriceUpdate,
    ModifierCreate, ModifierUpdate, ModifierResponse,
    BundlePackageCreate, BundlePackageResponse
)

router = APIRouter(prefix="/catalog", tags=["Product Catalog"])

# Ensure uploads directory exists
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "static" / "img" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Format gambar harus berupa JPG, PNG, WEBP, atau GIF")

    unique_filename = f"{uuid.uuid4().hex[:10]}_{Path(file.filename).name}"
    safe_name = "".join(c for c in unique_filename if c.isalnum() or c in "._-")
    file_path = UPLOAD_DIR / safe_name

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "success": True,
        "filename": safe_name,
        "url": f"/static/img/uploads/{safe_name}"
    }

# --- Categories ---
@router.get("/categories", response_model=List[CategoryResponse])
def get_categories(brand_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, brand_id, name, description, is_active FROM categories WHERE brand_id = ?", (brand_id,))
    return [dict(r) for r in cursor.fetchall()]

@router.post("/categories", response_model=CategoryResponse)
def create_category(data: CategoryCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO categories (brand_id, name, description, is_active)
        VALUES (?, ?, ?, ?)
    """, (data.brand_id, data.name, data.description, 1 if data.is_active else 0))
    cat_id = cursor.lastrowid
    db.commit()
    cursor.execute("SELECT id, brand_id, name, description, is_active FROM categories WHERE id = ?", (cat_id,))
    return dict(cursor.fetchone())

@router.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, data: CategoryUpdate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, brand_id, name, description, is_active FROM categories WHERE id = ?", (category_id,))
    existing = cursor.fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Kategori tidak ditemukan")

    name = data.name if data.name is not None else existing["name"]
    description = data.description if data.description is not None else existing["description"]
    is_active = (1 if data.is_active else 0) if data.is_active is not None else existing["is_active"]

    cursor.execute("""
        UPDATE categories SET name = ?, description = ?, is_active = ?
        WHERE id = ?
    """, (name, description, is_active, category_id))
    db.commit()

    cursor.execute("SELECT id, brand_id, name, description, is_active FROM categories WHERE id = ?", (category_id,))
    return dict(cursor.fetchone())

@router.delete("/categories/{category_id}")
def delete_category(category_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    db.commit()
    return {"success": True, "message": "Kategori berhasil dihapus"}

# --- Modifiers ---
@router.get("/modifiers", response_model=List[ModifierResponse])
def get_modifiers(brand_id: int = 1, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, brand_id, name, min_selection, max_selection, is_active FROM modifiers WHERE brand_id = ? ORDER BY id ASC", (brand_id,))
    modifiers = [dict(r) for r in cursor.fetchall()]

    for mod in modifiers:
        cursor.execute("SELECT id, modifier_id, name, additional_price FROM modifier_options WHERE modifier_id = ? ORDER BY id ASC", (mod["id"],))
        mod["options"] = [dict(opt) for opt in cursor.fetchall()]

    return modifiers

@router.post("/modifiers", response_model=ModifierResponse)
def create_modifier(data: ModifierCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO modifiers (brand_id, name, min_selection, max_selection, is_active)
        VALUES (?, ?, ?, ?, ?)
    """, (data.brand_id, data.name, data.min_selection, data.max_selection, 1 if data.is_active else 0))
    mod_id = cursor.lastrowid

    created_options = []
    for opt in data.options:
        cursor.execute("""
            INSERT INTO modifier_options (modifier_id, name, additional_price)
            VALUES (?, ?, ?)
        """, (mod_id, opt.name, opt.additional_price))
        created_options.append({
            "id": cursor.lastrowid,
            "modifier_id": mod_id,
            "name": opt.name,
            "additional_price": opt.additional_price
        })

    db.commit()
    cursor.execute("SELECT id, brand_id, name, min_selection, max_selection, is_active FROM modifiers WHERE id = ?", (mod_id,))
    res = dict(cursor.fetchone())
    res["options"] = created_options
    return res

@router.put("/modifiers/{modifier_id}", response_model=ModifierResponse)
def update_modifier(modifier_id: int, data: ModifierUpdate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, brand_id, name, min_selection, max_selection, is_active FROM modifiers WHERE id = ?", (modifier_id,))
    existing = cursor.fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Varian / Modifier tidak ditemukan")

    name = data.name if data.name is not None else existing["name"]
    min_selection = data.min_selection if data.min_selection is not None else existing["min_selection"]
    max_selection = data.max_selection if data.max_selection is not None else existing["max_selection"]
    is_active = (1 if data.is_active else 0) if data.is_active is not None else existing["is_active"]

    cursor.execute("""
        UPDATE modifiers SET name = ?, min_selection = ?, max_selection = ?, is_active = ?
        WHERE id = ?
    """, (name, min_selection, max_selection, is_active, modifier_id))

    if data.options is not None:
        cursor.execute("DELETE FROM modifier_options WHERE modifier_id = ?", (modifier_id,))
        for opt in data.options:
            cursor.execute("""
                INSERT INTO modifier_options (modifier_id, name, additional_price)
                VALUES (?, ?, ?)
            """, (modifier_id, opt.name, opt.additional_price))

    db.commit()

    cursor.execute("SELECT id, brand_id, name, min_selection, max_selection, is_active FROM modifiers WHERE id = ?", (modifier_id,))
    res = dict(cursor.fetchone())
    cursor.execute("SELECT id, modifier_id, name, additional_price FROM modifier_options WHERE modifier_id = ? ORDER BY id ASC", (modifier_id,))
    res["options"] = [dict(opt) for opt in cursor.fetchall()]
    return res

@router.delete("/modifiers/{modifier_id}")
def delete_modifier(modifier_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, name FROM modifiers WHERE id = ?", (modifier_id,))
    existing = cursor.fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Varian / Modifier tidak ditemukan")

    cursor.execute("DELETE FROM item_modifiers WHERE modifier_id = ?", (modifier_id,))
    cursor.execute("DELETE FROM modifier_options WHERE modifier_id = ?", (modifier_id,))
    cursor.execute("DELETE FROM modifiers WHERE id = ?", (modifier_id,))
    db.commit()
    return {"success": True, "message": f"Varian '{existing['name']}' berhasil dihapus"}

# --- Items (Item Library) ---
@router.get("/items", response_model=List[ItemResponse])
def get_items(category_id: Optional[int] = None, brand_id: Optional[int] = None, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    query = """
        SELECT i.id, i.category_id, c.name AS category_name, i.name, i.description, 
               i.sku, i.price, i.cost_price, i.image_url, i.is_active
        FROM items i
        LEFT JOIN categories c ON i.category_id = c.id
        WHERE 1=1
    """
    params = []
    if category_id:
        query += " AND i.category_id = ?"
        params.append(category_id)
    if brand_id:
        query += " AND c.brand_id = ?"
        params.append(brand_id)

    query += " ORDER BY i.id DESC"
    cursor.execute(query, params)
    items = [dict(r) for r in cursor.fetchall()]

    # Fetch attached modifiers
    for itm in items:
        cursor.execute("""
            SELECT m.id, m.brand_id, m.name, m.min_selection, m.max_selection, m.is_active
            FROM item_modifiers im
            JOIN modifiers m ON im.modifier_id = m.id
            WHERE im.item_id = ?
        """, (itm["id"],))
        mods = [dict(m) for m in cursor.fetchall()]
        for mod in mods:
            cursor.execute("SELECT id, modifier_id, name, additional_price FROM modifier_options WHERE modifier_id = ?", (mod["id"],))
            mod["options"] = [dict(opt) for opt in cursor.fetchall()]
        itm["modifiers"] = mods

    return items

def _fetch_item_modifiers(cursor, item_id: int):
    cursor.execute("""
        SELECT m.id, m.brand_id, m.name, m.min_selection, m.max_selection, m.is_active
        FROM item_modifiers im
        JOIN modifiers m ON im.modifier_id = m.id
        WHERE im.item_id = ?
    """, (item_id,))
    mods = [dict(m) for m in cursor.fetchall()]
    for mod in mods:
        cursor.execute("SELECT id, modifier_id, name, additional_price FROM modifier_options WHERE modifier_id = ?", (mod["id"],))
        mod["options"] = [dict(opt) for opt in cursor.fetchall()]
    return mods

@router.post("/items", response_model=ItemResponse)
def create_item(data: ItemCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO items (category_id, name, description, sku, price, cost_price, image_url, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (data.category_id, data.name, data.description, data.sku, data.price, data.cost_price, data.image_url, 1 if data.is_active else 0))
    item_id = cursor.lastrowid

    if data.modifier_ids:
        for mod_id in data.modifier_ids:
            cursor.execute("INSERT OR IGNORE INTO item_modifiers (item_id, modifier_id) VALUES (?, ?)", (item_id, mod_id))

    db.commit()

    cursor.execute("""
        SELECT i.id, i.category_id, c.name AS category_name, i.name, i.description, 
               i.sku, i.price, i.cost_price, i.image_url, i.is_active
        FROM items i
        LEFT JOIN categories c ON i.category_id = c.id
        WHERE i.id = ?
    """, (item_id,))
    res = dict(cursor.fetchone())
    res["modifiers"] = _fetch_item_modifiers(cursor, item_id)
    return res

@router.put("/items/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, data: ItemUpdate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    existing = cursor.fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Item tidak ditemukan")

    cat_id = data.category_id if data.category_id is not None else existing["category_id"]
    name = data.name if data.name is not None else existing["name"]
    desc = data.description if data.description is not None else existing["description"]
    sku = data.sku if data.sku is not None else existing["sku"]
    price = data.price if data.price is not None else existing["price"]
    cost_price = data.cost_price if data.cost_price is not None else existing["cost_price"]
    image_url = data.image_url if data.image_url is not None else existing["image_url"]
    is_active = (1 if data.is_active else 0) if data.is_active is not None else existing["is_active"]

    cursor.execute("""
        UPDATE items
        SET category_id = ?, name = ?, description = ?, sku = ?, price = ?, cost_price = ?, image_url = ?, is_active = ?
        WHERE id = ?
    """, (cat_id, name, desc, sku, price, cost_price, image_url, is_active, item_id))

    if data.modifier_ids is not None:
        cursor.execute("DELETE FROM item_modifiers WHERE item_id = ?", (item_id,))
        for mod_id in data.modifier_ids:
            cursor.execute("INSERT OR IGNORE INTO item_modifiers (item_id, modifier_id) VALUES (?, ?)", (item_id, mod_id))

    db.commit()

    cursor.execute("""
        SELECT i.id, i.category_id, c.name AS category_name, i.name, i.description, 
               i.sku, i.price, i.cost_price, i.image_url, i.is_active
        FROM items i
        LEFT JOIN categories c ON i.category_id = c.id
        WHERE i.id = ?
    """, (item_id,))
    res = dict(cursor.fetchone())
    res["modifiers"] = _fetch_item_modifiers(cursor, item_id)
    return res

@router.patch("/items/{item_id}/price")
def update_item_price(item_id: int, data: PriceUpdate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, price, cost_price FROM items WHERE id = ?", (item_id,))
    existing = cursor.fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Item tidak ditemukan")

    cost = data.cost_price if data.cost_price is not None else existing["cost_price"]
    cursor.execute("UPDATE items SET price = ?, cost_price = ? WHERE id = ?", (data.price, cost, item_id))
    db.commit()
    return {"success": True, "item_id": item_id, "price": data.price, "cost_price": cost}

@router.delete("/items/{item_id}")
def delete_item(item_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    cursor.execute("DELETE FROM item_modifiers WHERE item_id = ?", (item_id,))
    db.commit()
    return {"success": True, "message": "Item berhasil dihapus"}

# --- Bundle Packages ---
@router.get("/bundles", response_model=List[BundlePackageResponse])
def get_bundles(brand_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, brand_id, name, price, description, is_active FROM bundle_packages WHERE brand_id = ?", (brand_id,))
    bundles = [dict(b) for b in cursor.fetchall()]

    for b in bundles:
        cursor.execute("""
            SELECT bi.item_id, bi.quantity, i.name AS item_name, i.price AS item_price
            FROM bundle_items bi
            JOIN items i ON bi.item_id = i.id
            WHERE bi.bundle_id = ?
        """, (b["id"],))
        b["items"] = [dict(bi) for bi in cursor.fetchall()]

    return bundles

@router.post("/bundles", response_model=BundlePackageResponse)
def create_bundle(data: BundlePackageCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO bundle_packages (brand_id, name, price, description)
        VALUES (?, ?, ?, ?)
    """, (data.brand_id, data.name, data.price, data.description))
    bundle_id = cursor.lastrowid

    for bi in data.items:
        cursor.execute("INSERT INTO bundle_items (bundle_id, item_id, quantity) VALUES (?, ?, ?)", (bundle_id, bi.item_id, bi.quantity))

    db.commit()
    cursor.execute("SELECT id, brand_id, name, price, description, is_active FROM bundle_packages WHERE id = ?", (bundle_id,))
    res = dict(cursor.fetchone())
    res["items"] = []
    return res
