from fastapi import APIRouter, Depends
import sqlite3
import datetime
import json
from app.database import get_db
from app.models.integration import SyncPushRequest, SyncPullResponse

router = APIRouter(prefix="/sync", tags=["Multi-Terminal & Cloud Sync"])

@router.get("/status")
def get_sync_status(outlet_id: int, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) AS total_logs, MAX(synced_at) AS last_sync FROM sync_logs WHERE outlet_id = ?", (outlet_id,))
    row = cursor.fetchone()

    # Get unsynced transaction count
    cursor.execute("SELECT COUNT(*) AS pending_trx FROM transactions WHERE outlet_id = ?", (outlet_id,))
    trx_cnt = cursor.fetchone()["pending_trx"]

    return {
        "outlet_id": outlet_id,
        "is_online": True,
        "last_synced_at": row["last_sync"] or datetime.datetime.now().isoformat(),
        "total_sync_records": row["total_logs"],
        "total_transactions": trx_cnt,
        "sync_health": "healthy"
    }

@router.post("/push")
def push_sync_record(data: SyncPushRequest, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO sync_logs (outlet_id, entity_name, action, entity_id, payload)
        VALUES (?, ?, ?, ?, ?)
    """, (data.outlet_id, data.entity_name, data.action, data.entity_id, json.dumps(data.payload)))
    log_id = cursor.lastrowid
    db.commit()
    return {"success": True, "sync_log_id": log_id, "synced_at": datetime.datetime.now().isoformat()}

@router.get("/pull", response_model=SyncPullResponse)
def pull_sync_records(outlet_id: int, since_timestamp: str = None, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    query = "SELECT id, outlet_id, entity_name, action, entity_id, payload, synced_at FROM sync_logs WHERE outlet_id = ?"
    params = [outlet_id]
    if since_timestamp:
        query += " AND synced_at > ?"
        params.append(since_timestamp)
    query += " ORDER BY id ASC LIMIT 100"

    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]

    return {
        "total_synced": len(rows),
        "latest_sync_timestamp": datetime.datetime.now().isoformat(),
        "items": rows
    }
