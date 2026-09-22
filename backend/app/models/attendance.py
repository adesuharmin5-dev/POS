from typing import Optional, List
from pydantic import BaseModel

class ClockInRequest(BaseModel):
    outlet_id: int
    employee_id: int
    pin: Optional[str] = None
    notes: Optional[str] = None
    shift_id: Optional[int] = None
    status: Optional[str] = "present"

class ClockOutRequest(BaseModel):
    notes: Optional[str] = None

class AttendanceRecord(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    role_name: Optional[str] = None
    outlet_id: int
    clock_in: str
    clock_out: Optional[str] = None
    shift_id: Optional[int] = None
    work_minutes: Optional[int] = None
    notes: Optional[str] = None
    status: str
    date: str

class EmployeeAttendanceStatus(BaseModel):
    employee_id: int
    name: str
    phone: Optional[str] = None
    role_name: Optional[str] = None
    is_active: bool = True
    attendance_status: str  # 'not_clocked_in', 'working', 'clocked_out'
    current_attendance_id: Optional[int] = None
    clock_in: Optional[str] = None
    clock_out: Optional[str] = None
    work_minutes: Optional[int] = None
    notes: Optional[str] = None

class AttendanceDayResponse(BaseModel):
    date: str
    total_employees: int
    present_count: int
    active_working_count: int
    completed_count: int
    records: List[AttendanceRecord]
    employees: List[EmployeeAttendanceStatus]

class AttendanceSummaryItem(BaseModel):
    employee_id: int
    employee_name: str
    role_name: Optional[str] = None
    total_days_present: int
    total_work_minutes: int
    total_work_hours: float
    late_count: int
    records_count: int

class AttendanceSummaryResponse(BaseModel):
    outlet_id: int
    month: str # YYYY-MM
    items: List[AttendanceSummaryItem]
