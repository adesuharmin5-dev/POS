import sqlite3

def get_dashboard_summary(conn: sqlite3.Connection, outlet_id: int) -> dict:
    cursor = conn.cursor()

    # Total Sales Today
    cursor.execute("""
        SELECT COALESCE(SUM(total_amount), 0) AS total_sales, COUNT(*) AS trx_count
        FROM transactions
        WHERE outlet_id = ? AND date(created_at) = date('now') AND payment_status = 'paid'
    """, (outlet_id,))
    today_row = cursor.fetchone()

    # Active Shift
    cursor.execute("""
        SELECT s.id, s.start_time, s.initial_cash, s.expected_cash, e.name AS cashier_name
        FROM shifts s
        JOIN employees e ON s.employee_id = e.id
        WHERE s.outlet_id = ? AND s.status = 'open'
        ORDER BY s.id DESC LIMIT 1
    """, (outlet_id,))
    active_shift = cursor.fetchone()

    # Top Selling Items Today
    cursor.execute("""
        SELECT i.name, SUM(ti.quantity) AS qty_sold, SUM(ti.subtotal_price) AS revenue
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.id
        JOIN items i ON ti.item_id = i.id
        WHERE t.outlet_id = ? AND date(t.created_at) = date('now')
        GROUP BY i.id, i.name
        ORDER BY qty_sold DESC LIMIT 5
    """, (outlet_id,))
    top_items = [dict(row) for row in cursor.fetchall()]

    # Low Stock Alert Ingredients
    cursor.execute("""
        SELECT ing.id, ing.name, ing.unit, ois.current_stock, ing.min_stock_alert
        FROM outlet_ingredient_stocks ois
        JOIN ingredients ing ON ois.ingredient_id = ing.id
        WHERE ois.outlet_id = ? AND ois.current_stock <= ing.min_stock_alert
        ORDER BY ois.current_stock ASC LIMIT 5
    """, (outlet_id,))
    low_stocks = [dict(row) for row in cursor.fetchall()]

    # Table Occupancy
    cursor.execute("""
        SELECT 
            COUNT(*) AS total_tables,
            SUM(CASE WHEN status = 'occupied' THEN 1 ELSE 0 END) AS occupied_tables,
            SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) AS available_tables
        FROM tables WHERE outlet_id = ?
    """, (outlet_id,))
    tables_summary = cursor.fetchone()

    today_sales = float(today_row["total_sales"]) if today_row and today_row["total_sales"] is not None else 0.0
    trx_count = int(today_row["trx_count"]) if today_row and today_row["trx_count"] is not None else 0

    if trx_count == 0:
        today_sales = 0.0

    return {
        "outlet_id": outlet_id,
        "today_sales": today_sales,
        "today_transactions": trx_count,
        "total_sales_today": today_sales,
        "transaction_count_today": trx_count,
        "active_shift": dict(active_shift) if active_shift else None,
        "top_selling_items": top_items,
        "low_stock_alerts": low_stocks,
        "tables": dict(tables_summary) if tables_summary else {
            "total_tables": 0,
            "occupied_tables": 0,
            "available_tables": 0
        }
    }

def get_sales_report(conn: sqlite3.Connection, outlet_id: int, start_date: str = None, end_date: str = None) -> dict:
    cursor = conn.cursor()

    query = """
        SELECT 
            COALESCE(SUM(subtotal), 0) AS gross_sales,
            COALESCE(SUM(discount_amount), 0) AS total_discounts,
            COALESCE(SUM(tax_amount), 0) AS total_tax,
            COALESCE(SUM(gratuity_amount), 0) AS total_gratuity,
            COALESCE(SUM(total_amount), 0) AS net_sales,
            COUNT(*) AS total_transactions
        FROM transactions
        WHERE outlet_id = ? AND payment_status = 'paid'
    """
    params = [outlet_id]

    if start_date and end_date:
        query += " AND date(created_at) BETWEEN ? AND ?"
        params.extend([start_date, end_date])
    elif start_date:
        query += " AND date(created_at) >= ?"
        params.append(start_date)

    cursor.execute(query, params)
    overall = dict(cursor.fetchone())

    # Breakdown by Payment Method
    pm_query = """
        SELECT payment_method, COUNT(*) AS count, SUM(total_amount) AS total
        FROM transactions
        WHERE outlet_id = ? AND payment_status = 'paid'
    """
    pm_params = [outlet_id]
    if start_date and end_date:
        pm_query += " AND date(created_at) BETWEEN ? AND ?"
        pm_params.extend([start_date, end_date])
    pm_query += " GROUP BY payment_method"

    cursor.execute(pm_query, pm_params)
    payment_methods = [dict(row) for row in cursor.fetchall()]

    return {
        "outlet_id": outlet_id,
        "period": {"start": start_date, "end": end_date},
        "summary": overall,
        "payment_methods": payment_methods
    }

def get_table_report(conn: sqlite3.Connection, outlet_id: int) -> list:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            tbl.id,
            tbl.table_number,
            tg.name AS group_name,
            tbl.capacity,
            tbl.status,
            COALESCE(COUNT(t.id), 0) AS total_orders,
            COALESCE(SUM(t.total_amount), 0) AS total_revenue
        FROM tables tbl
        LEFT JOIN table_groups tg ON tbl.group_id = tg.id
        LEFT JOIN transactions t ON tbl.id = t.table_id AND t.payment_status = 'paid'
        WHERE tbl.outlet_id = ?
        GROUP BY tbl.id, tbl.table_number
        ORDER BY tbl.table_number ASC
    """, (outlet_id,))
    return [dict(row) for row in cursor.fetchall()]
