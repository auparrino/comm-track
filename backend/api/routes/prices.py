"""
GET /prices/{commodity_id}          ?days=30&source=&price_type=
GET /prices/{commodity_id}/latest
"""
from fastapi import APIRouter, HTTPException, Query
from backend.db.init_db import get_conn

router = APIRouter()


@router.get("/{commodity_id}/latest")
def latest_price(commodity_id: str):
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT p.*, c.name_es, c.unit
            FROM prices p
            JOIN commodities c ON c.id = p.commodity_id
            WHERE p.commodity_id = ?
            ORDER BY p.date DESC
            LIMIT 1
            """,
            (commodity_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Sin precios para '{commodity_id}'")
    return dict(row)


@router.get("/{commodity_id}")
def price_history(
    commodity_id: str,
    days: int = Query(default=90, ge=1, le=1825),
    source: str | None = Query(default=None),
    price_type: str | None = Query(default=None),
):
    filters = ["p.commodity_id = ?", "p.date >= date('now', ? || ' days')"]
    params: list = [commodity_id, f"-{days}"]

    if source:
        filters.append("p.source = ?")
        params.append(source)
    if price_type:
        filters.append("p.price_type = ?")
        params.append(price_type)

    where = " AND ".join(filters)
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM prices p WHERE {where} ORDER BY p.date ASC",
            params,
        ).fetchall()
    return [dict(r) for r in rows]
