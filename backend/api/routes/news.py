"""
GET /news/                  ?commodity=&days=&sentiment=&signal=&limit=
GET /news/{id}
"""
from fastapi import APIRouter, Query
from backend.db.init_db import get_conn

router = APIRouter()


@router.get("/")
def list_news(
    commodity: str | None = Query(default=None),
    days: int             = Query(default=14, ge=1, le=365),
    sentiment: str | None = Query(default=None),
    signal: str | None    = Query(default=None),
    limit: int            = Query(default=50, ge=1, le=200),
):
    filters = ["n.published_at >= datetime('now', ? || ' days')"]
    params: list = [f"-{days}"]

    if commodity:
        filters.append("n.commodity_id = ?")
        params.append(commodity)
    if sentiment:
        filters.append("n.sentiment = ?")
        params.append(sentiment)
    if signal:
        filters.append("n.signal_type = ?")
        params.append(signal)

    where = " AND ".join(filters)
    params.append(limit)

    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT
                n.id, n.commodity_id, n.title, n.snippet, n.url,
                n.source, n.published_at, n.sentiment, n.signal_type,
                n.relevance_score, n.summary_es, n.impact_direction,
                n.llm_provider,
                c.name_es AS commodity_name
            FROM news n
            LEFT JOIN commodities c ON c.id = n.commodity_id
            WHERE {where}
            ORDER BY n.published_at DESC
            LIMIT ?
            """,
            params,
        ).fetchall()
    return [dict(r) for r in rows]


@router.get("/{news_id}")
def get_news(news_id: int):
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT n.*, c.name_es AS commodity_name
            FROM news n
            LEFT JOIN commodities c ON c.id = n.commodity_id
            WHERE n.id = ?
            """,
            (news_id,),
        ).fetchone()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Noticia no encontrada")
    return dict(row)
