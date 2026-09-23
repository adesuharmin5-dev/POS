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


# ==========================================================================
# LAPORAN HARIAN
# ==========================================================================
def get_daily_report(conn: sqlite3.Connection, outlet_id: int, date: str = None) -> dict:
    cursor = conn.cursor()
    date_clause = "date(t.created_at) = date('now')"
    params_base = [outlet_id]
    if date:
        date_clause = "date(t.created_at) = ?"
        params_base = [outlet_id, date]

    # Summary metrics
    cursor.execute(f"""
        SELECT
            COALESCE(SUM(t.subtotal), 0)          AS gross_sales,
            COALESCE(SUM(t.discount_amount), 0)   AS total_discounts,
            COALESCE(SUM(t.tax_amount), 0)        AS total_tax,
            COALESCE(SUM(t.total_amount), 0)      AS net_sales,
            COUNT(DISTINCT t.id)                   AS total_transactions,
            COALESCE(AVG(t.total_amount), 0)       AS avg_transaction
        FROM transactions t
        WHERE t.outlet_id = ? AND t.payment_status = 'paid'
          AND {date_clause}
    """, params_base)
    row = cursor.fetchone()
    net_sales   = float(row["net_sales"])   if row and row["net_sales"] else 0.0
    total_trx   = int(row["total_transactions"]) if row and row["total_transactions"] else 0

    # COGS & profit
    cursor.execute(f"""
        SELECT COALESCE(SUM(COALESCE(i.cost_price,0) * ti.quantity), 0) AS total_cogs
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.id
        JOIN items i ON ti.item_id = i.id
        WHERE t.outlet_id = ? AND t.payment_status = 'paid'
          AND {date_clause}
    """, params_base)
    row_c = cursor.fetchone()
    cogs   = float(row_c["total_cogs"]) if row_c and row_c["total_cogs"] else 0.0
    profit = max(0.0, net_sales - cogs)
    margin = round((profit / net_sales) * 100, 1) if net_sales > 0 else 0.0

    # Hourly breakdown
    cursor.execute(f"""
        SELECT strftime('%H', t.created_at) AS hour,
               COUNT(*) AS trx_count,
               COALESCE(SUM(t.total_amount), 0) AS total_sales
        FROM transactions t
        WHERE t.outlet_id = ? AND t.payment_status = 'paid'
          AND {date_clause}
        GROUP BY hour ORDER BY hour
    """, params_base)
    hourly = [{"hour": r["hour"], "trx_count": r["trx_count"], "total_sales": float(r["total_sales"])} for r in cursor.fetchall()]

    # Payment method breakdown
    cursor.execute(f"""
        SELECT payment_method,
               COUNT(*) AS count,
               COALESCE(SUM(total_amount), 0) AS total
        FROM transactions t
        WHERE t.outlet_id = ? AND t.payment_status = 'paid'
          AND {date_clause}
        GROUP BY payment_method
    """, params_base)
    payment_methods = [{"method": r["payment_method"] or "Unknown", "count": r["count"], "total": float(r["total"])} for r in cursor.fetchall()]

    # Top items today
    cursor.execute(f"""
        SELECT i.name AS item_name,
               COALESCE(c.name, 'Lainnya') AS category_name,
               COALESCE(SUM(ti.quantity), 0) AS qty_sold,
               COALESCE(SUM(ti.subtotal_price), 0) AS revenue,
               COALESCE(SUM(COALESCE(i.cost_price, 0) * ti.quantity), 0) AS cogs
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.id
        JOIN items i ON ti.item_id = i.id
        LEFT JOIN categories c ON i.category_id = c.id
        WHERE t.outlet_id = ? AND t.payment_status = 'paid'
          AND {date_clause}
        GROUP BY i.id, i.name, c.name
        ORDER BY qty_sold DESC
        LIMIT 10
    """, params_base)
    top_items = []
    for r in cursor.fetchall():
        rev  = float(r["revenue"])
        cg   = float(r["cogs"])
        prof = max(0.0, rev - cg)
        top_items.append({
            "item_name": r["item_name"],
            "category_name": r["category_name"],
            "qty_sold": r["qty_sold"],
            "revenue": rev,
            "cogs": cg,
            "profit": prof,
            "margin": round((prof / rev) * 100, 1) if rev > 0 else 0.0
        })

    # Transaction list (last 30)
    cursor.execute(f"""
        SELECT t.transaction_number, t.created_at, t.table_number,
               t.subtotal, t.discount_amount, t.total_amount, t.payment_method
        FROM transactions t
        WHERE t.outlet_id = ? AND t.payment_status = 'paid'
          AND {date_clause}
        ORDER BY t.created_at DESC
        LIMIT 30
    """, params_base)
    transactions = [dict(r) for r in cursor.fetchall()]

    return {
        "date": date or "today",
        "summary": {
            "gross_sales":        float(row["gross_sales"]) if row and row["gross_sales"] else 0.0,
            "total_discounts":    float(row["total_discounts"]) if row and row["total_discounts"] else 0.0,
            "total_tax":          float(row["total_tax"]) if row and row["total_tax"] else 0.0,
            "net_sales":          net_sales,
            "total_transactions": total_trx,
            "avg_transaction":    float(row["avg_transaction"]) if row and row["avg_transaction"] else 0.0,
            "cogs":               cogs,
            "gross_profit":       profit,
            "profit_margin":      margin,
        },
        "hourly_breakdown": hourly,
        "payment_methods": payment_methods,
        "top_items": top_items,
        "transactions": transactions,
    }


# ==========================================================================
# LAPORAN BULANAN
# ==========================================================================
def get_monthly_report(conn: sqlite3.Connection, outlet_id: int, year: int = None, month: int = None) -> dict:
    cursor = conn.cursor()
    import datetime
    now = datetime.date.today()
    y = year or now.year
    m = month or now.month
    month_str = f"{y}-{m:02d}"

    params_base = [outlet_id, month_str]

    # Summary for the month
    cursor.execute("""
        SELECT
            COALESCE(SUM(t.subtotal), 0)          AS gross_sales,
            COALESCE(SUM(t.discount_amount), 0)   AS total_discounts,
            COALESCE(SUM(t.tax_amount), 0)        AS total_tax,
            COALESCE(SUM(t.total_amount), 0)      AS net_sales,
            COUNT(DISTINCT t.id)                   AS total_transactions,
            COUNT(DISTINCT date(t.created_at))     AS active_days
        FROM transactions t
        WHERE t.outlet_id = ? AND t.payment_status = 'paid'
          AND strftime('%Y-%m', t.created_at) = ?
    """, params_base)
    row = cursor.fetchone()
    net_sales  = float(row["net_sales"]) if row and row["net_sales"] else 0.0
    total_trx  = int(row["total_transactions"]) if row and row["total_transactions"] else 0
    active_days = int(row["active_days"]) if row and row["active_days"] else 0

    # COGS
    cursor.execute("""
        SELECT COALESCE(SUM(COALESCE(i.cost_price,0) * ti.quantity), 0) AS total_cogs
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.id
        JOIN items i ON ti.item_id = i.id
        WHERE t.outlet_id = ? AND t.payment_status = 'paid'
          AND strftime('%Y-%m', t.created_at) = ?
    """, params_base)
    row_c = cursor.fetchone()
    cogs   = float(row_c["total_cogs"]) if row_c and row_c["total_cogs"] else 0.0
    profit = max(0.0, net_sales - cogs)
    margin = round((profit / net_sales) * 100, 1) if net_sales > 0 else 0.0

    # Daily breakdown within the month
    cursor.execute("""
        SELECT date(t.created_at) AS day,
               COUNT(*) AS trx_count,
               COALESCE(SUM(t.total_amount), 0) AS total_sales
        FROM transactions t
        WHERE t.outlet_id = ? AND t.payment_status = 'paid'
          AND strftime('%Y-%m', t.created_at) = ?
        GROUP BY day ORDER BY day
    """, params_base)
    daily_breakdown = [{"day": r["day"], "trx_count": r["trx_count"], "total_sales": float(r["total_sales"])} for r in cursor.fetchall()]

    # Category breakdown
    cursor.execute("""
        SELECT COALESCE(c.name, 'Lainnya') AS category_name,
               COALESCE(SUM(ti.quantity), 0)       AS qty_sold,
               COALESCE(SUM(ti.subtotal_price), 0) AS revenue
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.id
        JOIN items i ON ti.item_id = i.id
        LEFT JOIN categories c ON i.category_id = c.id
        WHERE t.outlet_id = ? AND t.payment_status = 'paid'
          AND strftime('%Y-%m', t.created_at) = ?
        GROUP BY c.id, c.name ORDER BY revenue DESC
    """, params_base)
    categories = [{"category_name": r["category_name"], "qty_sold": r["qty_sold"], "revenue": float(r["revenue"])} for r in cursor.fetchall()]

    # Top items of the month
    cursor.execute("""
        SELECT i.name AS item_name,
               COALESCE(c.name, 'Lainnya') AS category_name,
               COALESCE(SUM(ti.quantity), 0)       AS qty_sold,
               COALESCE(SUM(ti.subtotal_price), 0) AS revenue,
               COALESCE(SUM(COALESCE(i.cost_price,0) * ti.quantity), 0) AS cogs
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.id
        JOIN items i ON ti.item_id = i.id
        LEFT JOIN categories c ON i.category_id = c.id
        WHERE t.outlet_id = ? AND t.payment_status = 'paid'
          AND strftime('%Y-%m', t.created_at) = ?
        GROUP BY i.id, i.name, c.name
        ORDER BY qty_sold DESC
        LIMIT 15
    """, params_base)
    top_items = []
    for r in cursor.fetchall():
        rev  = float(r["revenue"])
        cg   = float(r["cogs"])
        prof = max(0.0, rev - cg)
        top_items.append({
            "item_name": r["item_name"],
            "category_name": r["category_name"],
            "qty_sold": r["qty_sold"],
            "revenue": rev,
            "cogs": cg,
            "profit": prof,
            "margin": round((prof / rev) * 100, 1) if rev > 0 else 0.0
        })

    # Payment methods
    cursor.execute("""
        SELECT payment_method,
               COUNT(*) AS count,
               COALESCE(SUM(total_amount), 0) AS total
        FROM transactions t
        WHERE t.outlet_id = ? AND t.payment_status = 'paid'
          AND strftime('%Y-%m', t.created_at) = ?
        GROUP BY payment_method
    """, params_base)
    payment_methods = [{"method": r["payment_method"] or "Unknown", "count": r["count"], "total": float(r["total"])} for r in cursor.fetchall()]

    return {
        "year": y,
        "month": m,
        "month_label": month_str,
        "summary": {
            "gross_sales":        float(row["gross_sales"]) if row and row["gross_sales"] else 0.0,
            "total_discounts":    float(row["total_discounts"]) if row and row["total_discounts"] else 0.0,
            "total_tax":          float(row["total_tax"]) if row and row["total_tax"] else 0.0,
            "net_sales":          net_sales,
            "total_transactions": total_trx,
            "active_days":        active_days,
            "avg_per_day":        round(net_sales / active_days, 2) if active_days > 0 else 0.0,
            "avg_transaction":    round(net_sales / total_trx, 2) if total_trx > 0 else 0.0,
            "cogs":               cogs,
            "gross_profit":       profit,
            "profit_margin":      margin,
        },
        "daily_breakdown": daily_breakdown,
        "categories": categories,
        "top_items": top_items,
        "payment_methods": payment_methods,
    }


# ==========================================================================
# LAPORAN KUSTOM (rentang tanggal bebas)
# ==========================================================================
def get_custom_report(conn: sqlite3.Connection, outlet_id: int, start_date: str, end_date: str) -> dict:
    cursor = conn.cursor()
    params = [outlet_id, start_date, end_date]

    cursor.execute("""
        SELECT
            COALESCE(SUM(t.subtotal), 0)          AS gross_sales,
            COALESCE(SUM(t.discount_amount), 0)   AS total_discounts,
            COALESCE(SUM(t.tax_amount), 0)        AS total_tax,
            COALESCE(SUM(t.total_amount), 0)      AS net_sales,
            COUNT(DISTINCT t.id)                   AS total_transactions,
            COUNT(DISTINCT date(t.created_at))     AS active_days
        FROM transactions t
        WHERE t.outlet_id = ? AND t.payment_status = 'paid'
          AND date(t.created_at) BETWEEN ? AND ?
    """, params)
    row = cursor.fetchone()
    net_sales   = float(row["net_sales"]) if row and row["net_sales"] else 0.0
    total_trx   = int(row["total_transactions"]) if row and row["total_transactions"] else 0
    active_days = int(row["active_days"]) if row and row["active_days"] else 0

    cursor.execute("""
        SELECT COALESCE(SUM(COALESCE(i.cost_price,0) * ti.quantity), 0) AS total_cogs
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.id
        JOIN items i ON ti.item_id = i.id
        WHERE t.outlet_id = ? AND t.payment_status = 'paid'
          AND date(t.created_at) BETWEEN ? AND ?
    """, params)
    row_c = cursor.fetchone()
    cogs   = float(row_c["total_cogs"]) if row_c and row_c["total_cogs"] else 0.0
    profit = max(0.0, net_sales - cogs)
    margin = round((profit / net_sales) * 100, 1) if net_sales > 0 else 0.0

    # Daily breakdown
    cursor.execute("""
        SELECT date(t.created_at) AS day,
               COUNT(*) AS trx_count,
               COALESCE(SUM(t.total_amount), 0) AS total_sales
        FROM transactions t
        WHERE t.outlet_id = ? AND t.payment_status = 'paid'
          AND date(t.created_at) BETWEEN ? AND ?
        GROUP BY day ORDER BY day
    """, params)
    daily_breakdown = [{"day": r["day"], "trx_count": r["trx_count"], "total_sales": float(r["total_sales"])} for r in cursor.fetchall()]

    # Top items
    cursor.execute("""
        SELECT i.name AS item_name,
               COALESCE(c.name, 'Lainnya') AS category_name,
               COALESCE(SUM(ti.quantity), 0)       AS qty_sold,
               COALESCE(SUM(ti.subtotal_price), 0) AS revenue,
               COALESCE(SUM(COALESCE(i.cost_price,0) * ti.quantity), 0) AS cogs
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.id
        JOIN items i ON ti.item_id = i.id
        LEFT JOIN categories c ON i.category_id = c.id
        WHERE t.outlet_id = ? AND t.payment_status = 'paid'
          AND date(t.created_at) BETWEEN ? AND ?
        GROUP BY i.id, i.name, c.name
        ORDER BY revenue DESC
        LIMIT 15
    """, params)
    top_items = []
    for r in cursor.fetchall():
        rev  = float(r["revenue"])
        cg   = float(r["cogs"])
        prof = max(0.0, rev - cg)
        top_items.append({
            "item_name": r["item_name"],
            "category_name": r["category_name"],
            "qty_sold": r["qty_sold"],
            "revenue": rev,
            "cogs": cg,
            "profit": prof,
            "margin": round((prof / rev) * 100, 1) if rev > 0 else 0.0
        })

    # Payment methods
    cursor.execute("""
        SELECT payment_method,
               COUNT(*) AS count,
               COALESCE(SUM(total_amount), 0) AS total
        FROM transactions t
        WHERE t.outlet_id = ? AND t.payment_status = 'paid'
          AND date(t.created_at) BETWEEN ? AND ?
        GROUP BY payment_method
    """, params)
    payment_methods = [{"method": r["payment_method"] or "Unknown", "count": r["count"], "total": float(r["total"])} for r in cursor.fetchall()]

    return {
        "start_date": start_date,
        "end_date": end_date,
        "summary": {
            "gross_sales":        float(row["gross_sales"]) if row and row["gross_sales"] else 0.0,
            "total_discounts":    float(row["total_discounts"]) if row and row["total_discounts"] else 0.0,
            "total_tax":          float(row["total_tax"]) if row and row["total_tax"] else 0.0,
            "net_sales":          net_sales,
            "total_transactions": total_trx,
            "active_days":        active_days,
            "avg_per_day":        round(net_sales / active_days, 2) if active_days > 0 else 0.0,
            "avg_transaction":    round(net_sales / total_trx, 2) if total_trx > 0 else 0.0,
            "cogs":               cogs,
            "gross_profit":       profit,
            "profit_margin":      margin,
        },
        "daily_breakdown": daily_breakdown,
        "top_items": top_items,
        "payment_methods": payment_methods,
    }


# ==========================================================================
# LAPORAN KEUNTUNGAN (Profit per Item & Kategori)
# ==========================================================================
def get_profit_report(conn: sqlite3.Connection, outlet_id: int, start_date: str = None, end_date: str = None, period: str = "this_month") -> dict:
    cursor = conn.cursor()

    if start_date and end_date:
        date_clause = "AND date(t.created_at) BETWEEN ? AND ?"
        date_params = [start_date, end_date]
    elif period == "today":
        date_clause = "AND date(t.created_at) = date('now')"
        date_params = []
    elif period == "yesterday":
        date_clause = "AND date(t.created_at) = date('now', '-1 day')"
        date_params = []
    elif period == "last_7_days":
        date_clause = "AND date(t.created_at) >= date('now', '-7 days')"
        date_params = []
    elif period == "last_30_days":
        date_clause = "AND date(t.created_at) >= date('now', '-30 days')"
        date_params = []
    elif period == "this_month":
        date_clause = "AND strftime('%Y-%m', t.created_at) = strftime('%Y-%m', 'now')"
        date_params = []
    elif period == "all":
        date_clause = ""
        date_params = []
    else:
        date_clause = "AND strftime('%Y-%m', t.created_at) = strftime('%Y-%m', 'now')"
        date_params = []

    params_base = [outlet_id] + date_params

    # Overall metrics
    cursor.execute(f"""
        SELECT
            COALESCE(SUM(t.total_amount), 0) AS net_sales,
            COUNT(DISTINCT t.id) AS total_transactions
        FROM transactions t
        WHERE t.outlet_id = ? AND t.payment_status = 'paid' {date_clause}
    """, params_base)
    row_m = cursor.fetchone()
    net_sales = float(row_m["net_sales"]) if row_m and row_m["net_sales"] else 0.0

    cursor.execute(f"""
        SELECT COALESCE(SUM(COALESCE(i.cost_price,0) * ti.quantity), 0) AS total_cogs
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.id
        JOIN items i ON ti.item_id = i.id
        WHERE t.outlet_id = ? AND t.payment_status = 'paid' {date_clause}
    """, params_base)
    row_c = cursor.fetchone()
    cogs   = float(row_c["total_cogs"]) if row_c and row_c["total_cogs"] else 0.0
    profit = max(0.0, net_sales - cogs)
    margin = round((profit / net_sales) * 100, 1) if net_sales > 0 else 0.0

    # Profit per category
    cursor.execute(f"""
        SELECT
            COALESCE(c.name, 'Lainnya') AS category_name,
            COALESCE(SUM(ti.subtotal_price), 0) AS revenue,
            COALESCE(SUM(COALESCE(i.cost_price, 0) * ti.quantity), 0) AS cogs,
            COALESCE(SUM(ti.quantity), 0) AS qty_sold
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.id
        JOIN items i ON ti.item_id = i.id
        LEFT JOIN categories c ON i.category_id = c.id
        WHERE t.outlet_id = ? AND t.payment_status = 'paid' {date_clause}
        GROUP BY c.id, c.name
        ORDER BY revenue DESC
    """, params_base)
    categories = []
    for r in cursor.fetchall():
        rev  = float(r["revenue"])
        cg   = float(r["cogs"])
        prof = max(0.0, rev - cg)
        categories.append({
            "category_name": r["category_name"],
            "qty_sold": r["qty_sold"],
            "revenue": rev,
            "cogs": cg,
            "profit": prof,
            "margin": round((prof / rev) * 100, 1) if rev > 0 else 0.0,
        })

    # Profit per item
    cursor.execute(f"""
        SELECT
            i.name AS item_name,
            i.price AS sell_price,
            COALESCE(i.cost_price, 0) AS cost_price,
            COALESCE(c.name, 'Lainnya') AS category_name,
            COALESCE(SUM(ti.quantity), 0) AS qty_sold,
            COALESCE(SUM(ti.subtotal_price), 0) AS revenue,
            COALESCE(SUM(COALESCE(i.cost_price, 0) * ti.quantity), 0) AS cogs
        FROM transaction_items ti
        JOIN transactions t ON ti.transaction_id = t.id
        JOIN items i ON ti.item_id = i.id
        LEFT JOIN categories c ON i.category_id = c.id
        WHERE t.outlet_id = ? AND t.payment_status = 'paid' {date_clause}
        GROUP BY i.id, i.name, i.price, i.cost_price, c.name
        ORDER BY revenue DESC
        LIMIT 20
    """, params_base)
    items = []
    for r in cursor.fetchall():
        rev  = float(r["revenue"])
        cg   = float(r["cogs"])
        prof = max(0.0, rev - cg)
        items.append({
            "item_name": r["item_name"],
            "category_name": r["category_name"],
            "sell_price": float(r["sell_price"]),
            "cost_price": float(r["cost_price"]),
            "qty_sold": r["qty_sold"],
            "revenue": rev,
            "cogs": cg,
            "profit": prof,
            "margin": round((prof / rev) * 100, 1) if rev > 0 else 0.0,
        })

    return {
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "summary": {
            "net_sales":     net_sales,
            "total_cogs":    cogs,
            "gross_profit":  profit,
            "profit_margin": margin,
        },
        "categories": categories,
        "items": items,
    }


# ==========================================================================
# LAPORAN MODAL BARANG (Nilai Stok & HPP)
# ==========================================================================
def get_stock_value_report(conn: sqlite3.Connection, outlet_id: int) -> dict:
    cursor = conn.cursor()

    # Ingredient stock value
    cursor.execute("""
        SELECT
            ing.id,
            ing.name,
            ing.unit,
            COALESCE(ing.cost_per_unit, 0) AS cost_per_unit,
            COALESCE(ing.min_stock_alert, 0) AS min_stock_alert,
            COALESCE(ois.current_stock, 0) AS current_stock,
            COALESCE(ois.current_stock, 0) * COALESCE(ing.cost_per_unit, 0) AS stock_value
        FROM ingredients ing
        LEFT JOIN outlet_ingredient_stocks ois
          ON ois.ingredient_id = ing.id AND ois.outlet_id = ?
        ORDER BY stock_value DESC
    """, (outlet_id,))
    ingredients = []
    total_ingredient_value = 0.0
    for r in cursor.fetchall():
        sv = float(r["stock_value"])
        total_ingredient_value += sv
        ingredients.append({
            "id": r["id"],
            "name": r["name"],
            "unit": r["unit"],
            "cost_per_unit": float(r["cost_per_unit"]),
            "current_stock": float(r["current_stock"]),
            "min_stock_alert": float(r["min_stock_alert"]),
            "stock_value": sv,
            "is_low": float(r["current_stock"]) <= float(r["min_stock_alert"]),
        })

    # Items (menu) with cost_price — modal per menu
    cursor.execute("""
        SELECT
            i.id, i.name AS item_name,
            COALESCE(c.name, 'Lainnya') AS category_name,
            i.price AS sell_price,
            COALESCE(i.cost_price, 0) AS cost_price,
            (i.price - COALESCE(i.cost_price, 0)) AS profit_per_unit,
            CASE WHEN i.price > 0 THEN ROUND((i.price - COALESCE(i.cost_price, 0)) / i.price * 100, 1) ELSE 0 END AS margin
        FROM items i
        LEFT JOIN categories c ON i.category_id = c.id
        WHERE i.outlet_id = ? AND i.is_active = 1
        ORDER BY cost_price DESC
    """, (outlet_id,))
    menu_items = []
    for r in cursor.fetchall():
        menu_items.append({
            "id": r["id"],
            "item_name": r["item_name"],
            "category_name": r["category_name"],
            "sell_price": float(r["sell_price"]),
            "cost_price": float(r["cost_price"]),
            "profit_per_unit": float(r["profit_per_unit"]),
            "margin": float(r["margin"]),
        })

    return {
        "outlet_id": outlet_id,
        "total_ingredient_stock_value": round(total_ingredient_value, 2),
        "total_ingredients": len(ingredients),
        "low_stock_count": sum(1 for i in ingredients if i["is_low"]),
        "ingredients": ingredients,
        "menu_items": menu_items,
    }
