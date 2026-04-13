"""
GET /summary/                    ?commodity=
GET /summary/{commodity_id}      (último resumen del commodity)
"""
import json
from fastapi import APIRouter, HTTPException, Query
from backend.db.init_db import get_conn

router = APIRouter()


@router.get("/{commodity_id}")
def get_summary(commodity_id: str):
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT id, commodity_id, generated_at, period_start, period_end,
                   summary_text, key_signals, llm_provider
            FROM weekly_summaries
            WHERE commodity_id = ?
            ORDER BY generated_at DESC
            LIMIT 1
            """,
            (commodity_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Sin resumen disponible")
    result = dict(row)
    # Deserializar key_signals JSON
    try:
        result["key_signals"] = json.loads(result["key_signals"] or "[]")
    except Exception:
        result["key_signals"] = []
    return result


@router.get("/")
def list_summaries(commodity: str | None = Query(default=None)):
    with get_conn() as conn:
        if commodity:
            rows = conn.execute(
                """
                SELECT id, commodity_id, generated_at, period_start, period_end,
                       summary_text, key_signals, llm_provider
                FROM weekly_summaries
                WHERE commodity_id = ?
                ORDER BY generated_at DESC
                LIMIT 1
                """,
                (commodity,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT ws.*
                FROM weekly_summaries ws
                INNER JOIN (
                    SELECT commodity_id, MAX(generated_at) AS max_gen
                    FROM weekly_summaries
                    GROUP BY commodity_id
                ) latest ON ws.commodity_id = latest.commodity_id
                         AND ws.generated_at = latest.max_gen
                ORDER BY ws.commodity_id
                """
            ).fetchall()
    results = []
    for row in rows:
        r = dict(row)
        try:
            r["key_signals"] = json.loads(r["key_signals"] or "[]")
        except Exception:
            r["key_signals"] = []
        results.append(r)
    return results
