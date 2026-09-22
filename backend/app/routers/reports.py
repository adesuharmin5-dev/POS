from fastapi import APIRouter, Depends
import sqlite3
from typing import Optional
from app.database import get_db
from app.services.report_service import get_dashboard_summary, get_sales_report, get_table_report

router = APIRouter(prefix="/reports", tags=["Analytics & Reports"])

@router.get("/dashboard")
def get_dashboard(outlet_id: int, db: sqlite3.Connection = Depends(get_db)):
    return get_dashboard_summary(db, outlet_id)

@router.get("/sales")
def get_sales(
    outlet_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: sqlite3.Connection = Depends(get_db)
):
    return get_sales_report(db, outlet_id, start_date, end_date)

@router.get("/tables")
def get_table_analytics(outlet_id: int, db: sqlite3.Connection = Depends(get_db)):
    return get_table_report(db, outlet_id)
