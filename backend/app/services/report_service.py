import sqlite3

def get_dashboard_summary(
    conn: sqlite3.Connection,
    outlet_id: int,
    period: str = "today",
    start_date: str = None,
    end_date: str = None
) -> dict:
    cursor = conn.cursor()

    # Determine date filter clause
    date_clause = "AND date(t.created_at) = date('now')"
    date_params = []

    if start_date and end_date:
        date_clause = "AND date(t.created_at) BETWEEN ? AND ?"
        date_params = [start_date, end_date]
    elif start_date:
        date_clause = "AND date(t.created_at) >= ?"
        date_params = [start_date]
    elif period == "today":
        date_clause = "AND date(t.created_at) = date('now')"
    elif period == "yesterday":
        date_clause = "AND date(t.created_at) = date('now', '-1 day')"
    elif period == "last_7_days":
        date_clause = "AND date(t.created_at) >= date('now', '-7 days')"
    elif period == "last_30_days":
        date_clause = "AND date(t.created_at) >= date('now', '-30 days')"
    elif period == "this_month":
        date_clause = "AND strftime('%Y-%m', t.created_at) = strftime('%Y-%m', 'now')"
    elif period == "all":
        date_clause = ""

    # 1. Total Metrics & Financials for the selected period
    query_metrics = f"""
        SELECT 
            COALESCE(SUM(t.subtotal), 0) AS gross_sales,
            COALESCE(SUM(t.discount_amount), 0) AS total_discounts,
            COALESCE(SUM(t.tax_amount), 0) AS total_tax,
            COALESCE(SUM(t.total_amount), 0) AS net_sales,
            COUNT(DISTINCT t.id) AS total_transactions
        FROM transactions t
        WHERE t.outlet_id = ? AND t.payment_status = 'paid' {date_clause}
    """
    cursor.execute(query_metrics, [outlet_id] + date_params)
    row_m = cursor.fetchone()

    gross_sales = float(row_m["gross_sales"]) if row_m and row_m["gross_sales"] else 0.0
    net_sales = float(row_m["net_sales"]) if row_m and row_m["net_sales"] else 0.0
    total_trx = int(row_m["total_transactions"]) if row_m and row_m["total_transactions"] else 0
    avg_sale = round(net_sales / total_trx, 2) if total_trx > 0 else 0.0

    # Calculate COGS (Cost of Goods Sold) to get Gross Profit
    query_cogs = f"""
        SELECT COALESCE(SUM(COALESCE(i.cost_price, 0) * ti.quantity), 0) AS total_cogs
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.id
        JOIN items i ON ti.item_id = i.id
        WHERE t.outlet_id = ? AND t.payment_status = 'paid' {date_clause}
    """
    cursor.execute(query_cogs, [outlet_id] + date_params)
    row_cogs = cursor.fetchone()
    total_cogs = float(row_cogs["total_cogs"]) if row_cogs and row_cogs["total_cogs"] else 0.0
    gross_profit = max(0.0, net_sales - total_cogs)

    # 2. Categories by Volume (Porsi terjual)
    query_cat_vol = f"""
        SELECT 
            COALESCE(c.id, 0) AS category_id,
            COALESCE(c.name, 'Lainnya') AS category_name,
            COALESCE(SUM(ti.quantity), 0) AS total_volume
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.id
        JOIN items i ON ti.item_id = i.id
        LEFT JOIN categories c ON i.category_id = c.id
        WHERE t.outlet_id = ? AND t.payment_status = 'paid' {date_clause}
        GROUP BY c.id, c.name
        ORDER BY total_volume DESC
    """
    cursor.execute(query_cat_vol, [outlet_id] + date_params)
    raw_cat_vol = [dict(r) for r in cursor.fetchall()]
    total_all_volume = sum(c["total_volume"] for c in raw_cat_vol) or 1
    categories_by_volume = []
    for c in raw_cat_vol:
        vol = c["total_volume"]
        categories_by_volume.append({
            "category_id": c["category_id"],
            "category_name": c["category_name"],
            "total_volume": vol,
            "percentage": round((vol / total_all_volume) * 100, 1)
        })

    # 3. Categories by Sales (Omzet Rupiah)
    query_cat_sales = f"""
        SELECT 
            COALESCE(c.id, 0) AS category_id,
            COALESCE(c.name, 'Lainnya') AS category_name,
            COALESCE(SUM(ti.subtotal_price), 0) AS total_sales
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.id
        JOIN items i ON ti.item_id = i.id
        LEFT JOIN categories c ON i.category_id = c.id
        WHERE t.outlet_id = ? AND t.payment_status = 'paid' {date_clause}
        GROUP BY c.id, c.name
        ORDER BY total_sales DESC
    """
    cursor.execute(query_cat_sales, [outlet_id] + date_params)
    raw_cat_sales = [dict(r) for r in cursor.fetchall()]
    total_all_sales = sum(c["total_sales"] for c in raw_cat_sales) or 1.0
    categories_by_sales = []
    for c in raw_cat_sales:
        sls = float(c["total_sales"])
        categories_by_sales.append({
            "category_id": c["category_id"],
            "category_name": c["category_name"],
            "total_sales": sls,
            "percentage": round((sls / total_all_sales) * 100, 1)
        })

    # 4. Top Items by Category
    query_top_items = f"""
        SELECT 
            i.id AS item_id,
            i.name AS item_name,
            COALESCE(c.name, 'Lainnya') AS category_name,
            i.price AS item_price,
            COALESCE(SUM(ti.quantity), 0) AS qty_sold,
            COALESCE(SUM(ti.subtotal_price), 0) AS total_revenue
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.id
        JOIN items i ON ti.item_id = i.id
        LEFT JOIN categories c ON i.category_id = c.id
        WHERE t.outlet_id = ? AND t.payment_status = 'paid' {date_clause}
        GROUP BY i.id, i.name, c.name, i.price
        ORDER BY qty_sold DESC, total_revenue DESC
        LIMIT 15
    """
    cursor.execute(query_top_items, [outlet_id] + date_params)
    top_items_by_category = [dict(r) for r in cursor.fetchall()]

    # 5. Active Shift
    cursor.execute("""
        SELECT s.id, s.start_time, s.initial_cash, s.expected_cash, e.name AS cashier_name
        FROM shifts s
        JOIN employees e ON s.employee_id = e.id
        WHERE s.outlet_id = ? AND s.status = 'open'
        ORDER BY s.id DESC LIMIT 1
    """, (outlet_id,))
    active_shift = cursor.fetchone()

    # 6. Table Occupancy
    cursor.execute("""
        SELECT 
            COUNT(*) AS total_tables,
            SUM(CASE WHEN status = 'occupied' THEN 1 ELSE 0 END) AS occupied_tables,
            SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) AS available_tables
        FROM tables WHERE outlet_id = ?
    """, (outlet_id,))
    tables_summary = cursor.fetchone()

    # 7. Low Stock Alerts
    cursor.execute("""
        SELECT ing.id, ing.name, ing.unit, ois.current_stock, ing.min_stock_alert
        FROM outlet_ingredient_stocks ois
        JOIN ingredients ing ON ois.ingredient_id = ing.id
        WHERE ois.outlet_id = ? AND ois.current_stock <= ing.min_stock_alert
        ORDER BY ois.current_stock ASC LIMIT 5
    """, (outlet_id,))
    low_stocks = [dict(row) for row in cursor.fetchall()]

    return {
        "outlet_id": outlet_id,
        "period": period,
        "gross_sales": gross_sales,
        "net_sales": net_sales,
        "gross_profit": gross_profit,
        "total_transactions": total_trx,
        "avg_sale": avg_sale,
        "today_sales": net_sales,
        "today_transactions": total_trx,
        "total_sales_today": net_sales,
        "transaction_count_today": total_trx,
        "categories_by_volume": categories_by_volume,
        "categories_by_sales": categories_by_sales,
        "top_items_by_category": top_items_by_category,
        "active_shift": dict(active_shift) if active_shift else None,
        "tables": dict(tables_summary) if tables_summary else {
            "total_tables": 0,
            "occupied_tables": 0,
            "available_tables": 0
        },
        "low_stock_alerts": low_stocks
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
