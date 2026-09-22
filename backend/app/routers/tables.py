from fastapi import APIRouter, Depends, HTTPException
import sqlite3
from typing import List
from app.database import get_db
from app.models.table import (
    TableGroupResponse, TableCreate, TableResponse,
    TableUpdateLayout, TableStatusUpdate
)

router = APIRouter(prefix="/tables", tags=["Tables & Floor Management"])

@router.get("/groups", response_model=List[TableGroupResponse])
def get_table_groups(outlet_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, outlet_id, name, description FROM table_groups WHERE outlet_id = ?", (outlet_id,))
    return [dict(r) for r in cursor.fetchall()]

@router.get("", response_model=List[TableResponse])
def get_tables(outlet_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT t.id, t.group_id, tg.name AS group_name, t.outlet_id, 
               t.table_number, t.capacity, t.pos_x, t.pos_y, t.status, t.current_transaction_id
        FROM tables t
        LEFT JOIN table_groups tg ON t.group_id = tg.id
        WHERE t.outlet_id = ?
        ORDER BY t.table_number ASC
    """, (outlet_id,))
    return [dict(r) for r in cursor.fetchall()]

@router.post("", response_model=TableResponse)
def create_table(data: TableCreate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO tables (group_id, outlet_id, table_number, capacity, pos_x, pos_y, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (data.group_id, data.outlet_id, data.table_number, data.capacity, data.pos_x, data.pos_y, data.status))
    t_id = cursor.lastrowid
    db.commit()
    cursor.execute("""
        SELECT t.id, t.group_id, tg.name AS group_name, t.outlet_id, 
               t.table_number, t.capacity, t.pos_x, t.pos_y, t.status, t.current_transaction_id
        FROM tables t
        LEFT JOIN table_groups tg ON t.group_id = tg.id
        WHERE t.id = ?
    """, (t_id,))
    return dict(cursor.fetchone())

@router.put("/{table_id}/layout")
def update_table_layout(table_id: int, data: TableUpdateLayout, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("UPDATE tables SET pos_x = ?, pos_y = ? WHERE id = ?", (data.pos_x, data.pos_y, table_id))
    db.commit()
    return {"success": True, "table_id": table_id, "pos_x": data.pos_x, "pos_y": data.pos_y}

@router.put("/{table_id}/status")
def update_table_status(table_id: int, data: TableStatusUpdate, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        UPDATE tables 
        SET status = ?, current_transaction_id = ? 
        WHERE id = ?
    """, (data.status, data.current_transaction_id, table_id))
    db.commit()
    return {"success": True, "table_id": table_id, "status": data.status}
