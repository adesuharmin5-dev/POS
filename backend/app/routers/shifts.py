from fastapi import APIRouter, Depends, HTTPException
import sqlite3
import datetime
from typing import List, Optional
from app.database import get_db
from app.models.pos import ShiftOpenRequest, ShiftCloseRequest, ShiftResponse

router = APIRouter(prefix="/shifts", tags=["Cashier Shifts"])

@router.get("/current", response_model=Optional[ShiftResponse])
def get_current_shift(outlet_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT s.id, s.outlet_id, s.employee_id, e.name AS employee_name,
               s.start_time, s.end_time, s.initial_cash, s.expected_cash,
               s.actual_cash, s.difference, s.notes, s.status
        FROM shifts s
        JOIN employees e ON s.employee_id = e.id
        WHERE s.outlet_id = ? AND s.status = 'open'
        ORDER BY s.id DESC LIMIT 1
    """, (outlet_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

@router.post("/open", response_model=ShiftResponse)
def open_shift(data: ShiftOpenRequest, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    # Check if there is already an open shift
    cursor.execute("SELECT id FROM shifts WHERE outlet_id = ? AND status = 'open'", (data.outlet_id,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Shift kasir saat ini masih terbuka. Tutup shift terlebih dahulu.")

    cursor.execute("""
        INSERT INTO shifts (outlet_id, employee_id, initial_cash, expected_cash, status)
        VALUES (?, ?, ?, ?, 'open')
    """, (data.outlet_id, data.employee_id, data.initial_cash, data.initial_cash))
    shift_id = cursor.lastrowid

    # Auto clock-in attendance if not already clocked in today
    try:
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            SELECT id FROM attendances
            WHERE employee_id = ? AND outlet_id = ? AND date = ? AND clock_out IS NULL
        """, (data.employee_id, data.outlet_id, today_str))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO attendances (employee_id, outlet_id, clock_in, shift_id, notes, status, date)
                VALUES (?, ?, ?, ?, 'Buka Shift Kasir', 'present', ?)
            """, (data.employee_id, data.outlet_id, now_str, shift_id, today_str))
    except Exception as e:
        print(f"Shift auto-clockin note: {e}")

    db.commit()

    cursor.execute("""
        SELECT s.id, s.outlet_id, s.employee_id, e.name AS employee_name,
               s.start_time, s.end_time, s.initial_cash, s.expected_cash,
               s.actual_cash, s.difference, s.notes, s.status
        FROM shifts s
        JOIN employees e ON s.employee_id = e.id
        WHERE s.id = ?
    """, (shift_id,))
    return dict(cursor.fetchone())

@router.post("/{shift_id}/close", response_model=ShiftResponse)
def close_shift(shift_id: int, data: ShiftCloseRequest, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT expected_cash, status FROM shifts WHERE id = ?", (shift_id,))
    row = cursor.fetchone()
    if not row or row["status"] != "open":
        raise HTTPException(status_code=400, detail="Shift tidak ditemukan atau sudah ditutup")

    expected_cash = row["expected_cash"]
    diff = data.actual_cash - expected_cash

    cursor.execute("""
        UPDATE shifts 
        SET end_time = CURRENT_TIMESTAMP, actual_cash = ?, difference = ?, notes = ?, status = 'closed'
        WHERE id = ?
    """, (data.actual_cash, diff, data.notes, shift_id))

    # Auto clock out attendance associated with this shift if open
    try:
        cursor.execute("""
            SELECT id, clock_in, notes FROM attendances
            WHERE shift_id = ? AND clock_out IS NULL
        """, (shift_id,))
        att_row = cursor.fetchone()
        if att_row:
            att_id = att_row["id"]
            now_dt = datetime.datetime.now()
            now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
            try:
                cin_dt = datetime.datetime.strptime(att_row["clock_in"][:19], "%Y-%m-%d %H:%M:%S")
                diff_mins = max(1, int((now_dt - cin_dt).total_seconds() / 60))
            except Exception:
                diff_mins = 60
            existing_note = att_row["notes"] or ""
            updated_note = f"{existing_note} (Tutup Shift Kasir)".strip()
            cursor.execute("""
                UPDATE attendances
                SET clock_out = ?, work_minutes = ?, notes = ?
                WHERE id = ?
            """, (now_str, diff_mins, updated_note, att_id))
    except Exception as e:
        print(f"Shift auto-clockout note: {e}")

    db.commit()

    cursor.execute("""
        SELECT s.id, s.outlet_id, s.employee_id, e.name AS employee_name,
               s.start_time, s.end_time, s.initial_cash, s.expected_cash,
               s.actual_cash, s.difference, s.notes, s.status
        FROM shifts s
        JOIN employees e ON s.employee_id = e.id
        WHERE s.id = ?
    """, (shift_id,))
    return dict(cursor.fetchone())

@router.get("/history", response_model=List[ShiftResponse])
def get_shift_history(outlet_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT s.id, s.outlet_id, s.employee_id, e.name AS employee_name,
               s.start_time, s.end_time, s.initial_cash, s.expected_cash,
               s.actual_cash, s.difference, s.notes, s.status
        FROM shifts s
        JOIN employees e ON s.employee_id = e.id
        WHERE s.outlet_id = ?
        ORDER BY s.id DESC LIMIT 20
    """, (outlet_id,))
    return [dict(r) for r in cursor.fetchall()]
