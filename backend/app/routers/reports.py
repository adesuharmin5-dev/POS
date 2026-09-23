from fastapi import APIRouter, Depends
import sqlite3
from typing import Optional
from app.database import get_db
from app.services.report_service import (
    get_dashboard_summary,
    get_sales_report,
    get_table_report,
    get_daily_report,
    get_monthly_report,
    get_custom_report,
    get_profit_report,
    get_stock_value_report,
)

router = APIRouter(prefix="/reports", tags=["Analytics & Reports"])

@router.get("/dashboard")
def get_dashboard(
    outlet_id: int = 1,
    period: Optional[str] = "today",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: sqlite3.Connection = Depends(get_db)
):
    return get_dashboard_summary(db, outlet_id, period, start_date, end_date)

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

@router.get("/daily")
def get_daily(
    outlet_id: int = 1,
    date: Optional[str] = None,
    db: sqlite3.Connection = Depends(get_db)
):
    return get_daily_report(db, outlet_id, date)

@router.get("/monthly")
def get_monthly(
    outlet_id: int = 1,
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: sqlite3.Connection = Depends(get_db)
):
    return get_monthly_report(db, outlet_id, year, month)

@router.get("/custom")
def get_custom(
    outlet_id: int = 1,
    start_date: str = None,
    end_date: str = None,
    db: sqlite3.Connection = Depends(get_db)
):
    if not start_date or not end_date:
        return {"error": "start_date dan end_date wajib diisi"}
    return get_custom_report(db, outlet_id, start_date, end_date)

@router.get("/profit")
def get_profit(
    outlet_id: int = 1,
    period: Optional[str] = "this_month",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: sqlite3.Connection = Depends(get_db)
):
    return get_profit_report(db, outlet_id, start_date, end_date, period)

@router.get("/stock-value")
def get_stock_value(
    outlet_id: int = 1,
    db: sqlite3.Connection = Depends(get_db)
):
    return get_stock_value_report(db, outlet_id)
