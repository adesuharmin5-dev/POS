from fastapi import APIRouter, Depends, HTTPException, Query
import sqlite3
import datetime
from typing import List, Optional
from app.database import get_db
from app.models.attendance import (
    ClockInRequest,
    ClockOutRequest,
    AttendanceRecord,
    EmployeeAttendanceStatus,
    AttendanceDayResponse,
    AttendanceSummaryResponse,
    AttendanceSummaryItem
)

router = APIRouter(prefix="/attendance", tags=["Employee Attendance"])

def get_current_date_str() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d")

def get_current_time_str() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def parse_datetime(dt_str: str) -> datetime.datetime:
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            return datetime.datetime.strptime(dt_str, fmt)
        except ValueError:
            pass
    # Fallback to date only
    return datetime.datetime.strptime(dt_str[:10], "%Y-%m-%d")

@router.get("", response_model=AttendanceDayResponse)
@router.get("/day", response_model=AttendanceDayResponse)
def get_daily_attendance(
    outlet_id: int = 1,
    date: Optional[str] = None,
    db: sqlite3.Connection = Depends(get_db)
):
    target_date = date or get_current_date_str()
    cursor = db.cursor()

    # 1. Fetch all active employees for this outlet
    cursor.execute("""
        SELECT e.id, e.name, e.phone, e.is_active, r.name AS role_name
        FROM employees e
        LEFT JOIN roles r ON e.role_id = r.id
        WHERE e.outlet_id = ? AND e.is_active = 1
        ORDER BY e.name ASC
    """, (outlet_id,))
    employees_rows = cursor.fetchall()

    # 2. Fetch all attendance records for this date and outlet
    cursor.execute("""
        SELECT a.id, a.employee_id, e.name AS employee_name, r.name AS role_name,
               a.outlet_id, a.clock_in, a.clock_out, a.shift_id, a.work_minutes,
               a.notes, a.status, a.date
        FROM attendances a
        JOIN employees e ON a.employee_id = e.id
        LEFT JOIN roles r ON e.role_id = r.id
        WHERE a.outlet_id = ? AND a.date = ?
        ORDER BY a.clock_in DESC
    """, (outlet_id, target_date))
    records_rows = cursor.fetchall()
    records = [AttendanceRecord(**dict(r)) for r in records_rows]

    # Map the latest attendance record per employee for this day
    emp_latest_att = {}
    for r in records_rows:
        emp_id = r["employee_id"]
        if emp_id not in emp_latest_att:
            emp_latest_att[emp_id] = r

    # Build employee status list
    employee_statuses = []
    present_count = 0
    active_working_count = 0
    completed_count = 0

    for emp in employees_rows:
        emp_id = emp["id"]
        att = emp_latest_att.get(emp_id)

        if not att:
            status_text = "not_clocked_in"
            att_id = None
            clock_in = None
            clock_out = None
            work_mins = None
            notes = None
        else:
            present_count += 1
            att_id = att["id"]
            clock_in = att["clock_in"]
            clock_out = att["clock_out"]
            work_mins = att["work_minutes"]
            notes = att["notes"]
            if clock_out:
                status_text = "clocked_out"
                completed_count += 1
            else:
                status_text = "working"
                active_working_count += 1

        employee_statuses.append(EmployeeAttendanceStatus(
            employee_id=emp_id,
            name=emp["name"],
            phone=emp["phone"],
            role_name=emp["role_name"],
            is_active=bool(emp["is_active"]),
            attendance_status=status_text,
            current_attendance_id=att_id,
            clock_in=clock_in,
            clock_out=clock_out,
            work_minutes=work_mins,
            notes=notes
        ))

    return AttendanceDayResponse(
        date=target_date,
        total_employees=len(employees_rows),
        present_count=present_count,
        active_working_count=active_working_count,
        completed_count=completed_count,
        records=records,
        employees=employee_statuses
    )

@router.post("/clock-in", response_model=AttendanceRecord)
def clock_in(data: ClockInRequest, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()

    # Verify employee exists and is active
    cursor.execute("SELECT id, name, pin, is_active FROM employees WHERE id = ? AND outlet_id = ?", (data.employee_id, data.outlet_id))
    emp = cursor.fetchone()
    if not emp:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan di outlet ini")
    if not emp["is_active"]:
        raise HTTPException(status_code=400, detail=f"Karyawan '{emp['name']}' sedang tidak aktif")

    # If pin is provided, verify it
    if data.pin:
        if str(emp["pin"]).strip() != str(data.pin).strip():
            raise HTTPException(status_code=400, detail="PIN karyawan salah")

    today_str = get_current_date_str()
    now_str = get_current_time_str()

    # Check if there is already an active (unclosed) clock in for this employee today
    cursor.execute("""
        SELECT id, clock_in FROM attendances
        WHERE employee_id = ? AND outlet_id = ? AND date = ? AND clock_out IS NULL
        ORDER BY id DESC LIMIT 1
    """, (data.employee_id, data.outlet_id, today_str))
    active_att = cursor.fetchone()
    if active_att:
        raise HTTPException(
            status_code=400,
            detail=f"{emp['name']} sudah melakukan Clock In pada {active_att['clock_in']} dan belum Clock Out."
        )

    # Insert new attendance record
    cursor.execute("""
        INSERT INTO attendances (employee_id, outlet_id, clock_in, shift_id, notes, status, date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data.employee_id,
        data.outlet_id,
        now_str,
        data.shift_id,
        data.notes,
        data.status or "present",
        today_str
    ))
    new_id = cursor.lastrowid
    db.commit()

    # Fetch inserted record
    cursor.execute("""
        SELECT a.id, a.employee_id, e.name AS employee_name, r.name AS role_name,
               a.outlet_id, a.clock_in, a.clock_out, a.shift_id, a.work_minutes,
               a.notes, a.status, a.date
        FROM attendances a
        JOIN employees e ON a.employee_id = e.id
        LEFT JOIN roles r ON e.role_id = r.id
        WHERE a.id = ?
    """, (new_id,))
    return AttendanceRecord(**dict(cursor.fetchone()))

@router.put("/{attendance_id}/clock-out", response_model=AttendanceRecord)
def clock_out(
    attendance_id: int,
    data: Optional[ClockOutRequest] = None,
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    cursor.execute("SELECT id, employee_id, clock_in, clock_out, notes FROM attendances WHERE id = ?", (attendance_id,))
    att = cursor.fetchone()
    if not att:
        raise HTTPException(status_code=404, detail="Data absensi tidak ditemukan")
    if att["clock_out"]:
        raise HTTPException(status_code=400, detail="Absensi ini sudah selesai (sudah Clock Out)")

    now_dt = datetime.datetime.now()
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

    clock_in_dt = parse_datetime(att["clock_in"])
    diff_seconds = max(0, (now_dt - clock_in_dt).total_seconds())
    work_minutes = max(1, int(diff_seconds / 60))

    extra_notes = data.notes if data and data.notes else att["notes"]

    cursor.execute("""
        UPDATE attendances
        SET clock_out = ?, work_minutes = ?, notes = ?
        WHERE id = ?
    """, (now_str, work_minutes, extra_notes, attendance_id))
    db.commit()

    cursor.execute("""
        SELECT a.id, a.employee_id, e.name AS employee_name, r.name AS role_name,
               a.outlet_id, a.clock_in, a.clock_out, a.shift_id, a.work_minutes,
               a.notes, a.status, a.date
        FROM attendances a
        JOIN employees e ON a.employee_id = e.id
        LEFT JOIN roles r ON e.role_id = r.id
        WHERE a.id = ?
    """, (attendance_id,))
    return AttendanceRecord(**dict(cursor.fetchone()))

@router.post("/clock-out-by-employee", response_model=AttendanceRecord)
def clock_out_by_employee(
    employee_id: int = Query(...),
    outlet_id: int = Query(1),
    notes: Optional[str] = None,
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    today_str = get_current_date_str()
    cursor.execute("""
        SELECT id FROM attendances
        WHERE employee_id = ? AND outlet_id = ? AND date = ? AND clock_out IS NULL
        ORDER BY id DESC LIMIT 1
    """, (employee_id, outlet_id, today_str))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=400, detail="Tidak ada absensi aktif untuk karyawan ini hari ini")

    return clock_out(attendance_id=row["id"], data=ClockOutRequest(notes=notes), db=db)

@router.get("/summary", response_model=AttendanceSummaryResponse)
def get_attendance_summary(
    outlet_id: int = 1,
    month: Optional[str] = None,
    db: sqlite3.Connection = Depends(get_db)
):
    target_month = month or datetime.datetime.now().strftime("%Y-%m")
    cursor = db.cursor()

    cursor.execute("""
        SELECT e.id AS employee_id, e.name AS employee_name, r.name AS role_name,
               COUNT(DISTINCT a.date) AS total_days_present,
               COALESCE(SUM(a.work_minutes), 0) AS total_work_minutes,
               COUNT(CASE WHEN a.status = 'late' THEN 1 END) AS late_count,
               COUNT(a.id) AS records_count
        FROM employees e
        LEFT JOIN roles r ON e.role_id = r.id
        LEFT JOIN attendances a ON a.employee_id = e.id 
             AND a.outlet_id = ? 
             AND a.date LIKE ?
        WHERE e.outlet_id = ? AND e.is_active = 1
        GROUP BY e.id, e.name, r.name
        ORDER BY total_days_present DESC, e.name ASC
    """, (outlet_id, f"{target_month}%", outlet_id))

    rows = cursor.fetchall()
    items = []
    for r in rows:
        mins = r["total_work_minutes"] or 0
        items.append(AttendanceSummaryItem(
            employee_id=r["employee_id"],
            employee_name=r["employee_name"],
            role_name=r["role_name"],
            total_days_present=r["total_days_present"] or 0,
            total_work_minutes=mins,
            total_work_hours=round(mins / 60.0, 1),
            late_count=r["late_count"] or 0,
            records_count=r["records_count"] or 0
        ))

    return AttendanceSummaryResponse(
        outlet_id=outlet_id,
        month=target_month,
        items=items
    )

@router.get("/history", response_model=List[AttendanceRecord])
def get_attendance_history(
    outlet_id: int = 1,
    employee_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: sqlite3.Connection = Depends(get_db)
):
    cursor = db.cursor()
    query = """
        SELECT a.id, a.employee_id, e.name AS employee_name, r.name AS role_name,
               a.outlet_id, a.clock_in, a.clock_out, a.shift_id, a.work_minutes,
               a.notes, a.status, a.date
        FROM attendances a
        JOIN employees e ON a.employee_id = e.id
        LEFT JOIN roles r ON e.role_id = r.id
        WHERE a.outlet_id = ?
    """
    params = [outlet_id]

    if employee_id:
        query += " AND a.employee_id = ?"
        params.append(employee_id)
    if start_date:
        query += " AND a.date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND a.date <= ?"
        params.append(end_date)

    query += " ORDER BY a.clock_in DESC LIMIT 100"

    cursor.execute(query, tuple(params))
    return [AttendanceRecord(**dict(r)) for r in cursor.fetchall()]

@router.delete("/{attendance_id}")
def delete_attendance(attendance_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id FROM attendances WHERE id = ?", (attendance_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Data absensi tidak ditemukan")
    cursor.execute("DELETE FROM attendances WHERE id = ?", (attendance_id,))
    db.commit()
    return {"success": True, "message": "Data absensi berhasil dihapus"}
