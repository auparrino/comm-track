"""
GET /trade-flows/                  ?commodity=&months=&ncm=
GET /trade-flows/summary           ?commodity=&months=  → últimos N meses agregados por commodity
GET /trade-flows/partners          ?commodity=&year=&flow=export&top=10
"""
from fastapi import APIRouter, Query
from backend.db.init_db import get_conn

router = APIRouter()


@router.get("/")
def list_trade_flows(
    commodity: str | None = Query(default=None),
    months: int           = Query(default=24, ge=1, le=420),
    ncm: str | None       = Query(default=None),
):
    """Serie mensual de exportaciones por commodity y capítulo NCM."""
    filters = ["period >= strftime('%Y-%m', date('now', ? || ' months'))"]
    params: list = [f"-{months}"]

    if commodity:
        filters.append("commodity_id = ?")
        params.append(commodity)
    if ncm:
        filters.append("ncm = ?")
        params.append(ncm)

    where = " AND ".join(filters)
    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT commodity_id, ncm, period, flow_type,
                   value_usd, weight_kg, source
            FROM trade_flows
            WHERE {where}
            ORDER BY commodity_id, ncm, period
            """,
            params,
        ).fetchall()

    return [
        {
            "commodity_id": r[0],
            "ncm":          r[1],
            "period":       r[2],
            "flow_type":    r[3],
            "value_usd":    r[4],
            "weight_kg":    r[5],
            "source":       r[6],
        }
        for r in rows
    ]


@router.get("/summary")
def trade_summary(
    commodity: str | None = Query(default=None),
    months: int           = Query(default=12, ge=1, le=120),
):
    """
    Suma acumulada de exportaciones por commodity en los últimos N meses.
    Para soja agrega caps 12 + 15 + 23.
    """
    filters = ["period >= strftime('%Y-%m', date('now', ? || ' months'))"]
    params: list = [f"-{months}"]

    if commodity:
        filters.append("commodity_id = ?")
        params.append(commodity)

    where = " AND ".join(filters)
    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT commodity_id,
                   SUM(value_usd)  AS total_export_usd,
                   MIN(period)     AS from_period,
                   MAX(period)     AS to_period,
                   COUNT(*)        AS data_points
            FROM trade_flows
            WHERE {where} AND flow_type = 'export'
            GROUP BY commodity_id
            ORDER BY total_export_usd DESC
            """,
            params,
        ).fetchall()

    return [
        {
            "commodity_id":      r[0],
            "total_export_usd":  r[1],
            "from_period":       r[2],
            "to_period":         r[3],
            "data_points":       r[4],
        }
        for r in rows
    ]


@router.get("/partners")
def trade_partners(
    commodity: str | None = Query(default=None),
    year: int             = Query(default=2024),
    flow: str             = Query(default="export"),
    top: int              = Query(default=10, ge=1, le=50),
):
    """
    Top países por valor de exportaciones/importaciones de un commodity,
    para un año dado. Agrega todos los capítulos NCM del commodity.
    Fuente: comex_ied (datos anuales bilaterales).
    """
    flow_type = "export" if flow == "export" else "import"
    country_col = "country_dest" if flow_type == "export" else "country_origin"

    filters = [
        "source = 'comex_ied'",
        "flow_type = ?",
        "period = ?",
        f"{country_col} IS NOT NULL",
    ]
    params: list = [flow_type, str(year)]

    if commodity:
        filters.append("commodity_id = ?")
        params.append(commodity)

    where = " AND ".join(filters)
    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT {country_col} AS country,
                   commodity_id,
                   SUM(value_usd) AS total_usd
            FROM trade_flows
            WHERE {where}
            GROUP BY {country_col}, commodity_id
            ORDER BY total_usd DESC
            LIMIT ?
            """,
            params + [top],
        ).fetchall()

    return [
        {
            "country":      r[0],
            "commodity_id": r[1],
            "total_usd":    r[2],
            "year":         year,
            "flow_type":    flow_type,
        }
        for r in rows
    ]
