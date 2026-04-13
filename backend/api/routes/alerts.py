"""
GET /alerts/                    ?commodity=&active_only=true
GET /alerts/{commodity_id}      (alertas activas del commodity)
"""
from fastapi import APIRouter, Query
from backend.db.init_db import get_conn

router = APIRouter()


@router.get("/")
def list_alerts(
    commodity: str | None = Query(default=None),
    active_only: bool = Query(default=True),
):
    filters = []
    params: list = []

    if commodity:
        filters.append("commodity_id = ?")
        params.append(commodity)
    if active_only:
        filters.append("is_active = 1")

    where = ("WHERE " + " AND ".join(filters)) if filters else ""

    with get_conn() as conn:
        # Ensure table exists (pipeline may not have run yet)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                commodity_id   TEXT REFERENCES commodities(id),
                generated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                title          TEXT NOT NULL,
                description    TEXT,
                severity       TEXT,
                signal_type    TEXT,
                llm_provider   TEXT,
                source_news_ids TEXT,
                is_active      BOOLEAN DEFAULT 1,
                expires_at     DATE
            )
            """
        )
        rows = conn.execute(
            f"""
            SELECT a.*, c.name_es AS commodity_name
            FROM alerts a
            LEFT JOIN commodities c ON a.commodity_id = c.id
            {where}
            ORDER BY
              CASE severity WHEN 'high' THEN 0 ELSE 1 END,
              generated_at DESC
            LIMIT 20
            """,
            params,
        ).fetchall()
    return [dict(r) for r in rows]


@router.get("/{commodity_id}")
def get_commodity_alerts(commodity_id: str, active_only: bool = Query(default=True)):
    filters = ["a.commodity_id = ?"]
    params: list = [commodity_id]
    if active_only:
        filters.append("a.is_active = 1")
    where = "WHERE " + " AND ".join(filters)

    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                commodity_id   TEXT REFERENCES commodities(id),
                generated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                title          TEXT NOT NULL,
                description    TEXT,
                severity       TEXT,
                signal_type    TEXT,
                llm_provider   TEXT,
                source_news_ids TEXT,
                is_active      BOOLEAN DEFAULT 1,
                expires_at     DATE
            )
            """
        )
        rows = conn.execute(
            f"""
            SELECT a.*, c.name_es AS commodity_name
            FROM alerts a
            LEFT JOIN commodities c ON a.commodity_id = c.id
            {where}
            ORDER BY
              CASE severity WHEN 'high' THEN 0 ELSE 1 END,
              generated_at DESC
            """,
            params,
        ).fetchall()
    return [dict(r) for r in rows]
