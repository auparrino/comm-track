"""
GET /impact-variables               ?commodity=&variable=&days=180
GET /impact-variables/latest        ?commodity=
"""
from fastapi import APIRouter, Query
from backend.db.init_db import get_conn

router = APIRouter()


@router.get("/latest")
def latest_variables(commodity: str | None = Query(default=None)):
    """Último valor de cada variable de impacto (por commodity si se especifica).
    Incluye prev_value (valor anterior) para calcular tendencia en el frontend.
    """
    _PREV = """
        (SELECT iv3.value FROM impact_variables iv3
         WHERE iv3.variable_name = iv.variable_name
           AND (iv3.commodity_id IS iv.commodity_id)
           AND iv3.date < iv.date
         ORDER BY iv3.date DESC LIMIT 1) AS prev_value,
        (SELECT iv3.date FROM impact_variables iv3
         WHERE iv3.variable_name = iv.variable_name
           AND (iv3.commodity_id IS iv.commodity_id)
           AND iv3.date < iv.date
         ORDER BY iv3.date DESC LIMIT 1) AS prev_date
    """
    with get_conn() as conn:
        if commodity:
            rows = conn.execute(
                f"""
                SELECT iv.id, iv.commodity_id, iv.variable_name, iv.date,
                       iv.value, iv.value_text, iv.source, iv.unit,
                       {_PREV}
                FROM impact_variables iv
                WHERE (iv.commodity_id = ? OR iv.commodity_id IS NULL)
                  AND iv.date = (
                      SELECT MAX(iv2.date)
                      FROM impact_variables iv2
                      WHERE iv2.variable_name = iv.variable_name
                        AND (iv2.commodity_id IS iv.commodity_id)
                  )
                GROUP BY iv.variable_name
                ORDER BY iv.variable_name
                """,
                (commodity,),
            ).fetchall()
        else:
            rows = conn.execute(
                f"""
                SELECT iv.id, iv.commodity_id, iv.variable_name, iv.date,
                       iv.value, iv.value_text, iv.source, iv.unit,
                       {_PREV}
                FROM impact_variables iv
                WHERE iv.date = (
                    SELECT MAX(iv2.date)
                    FROM impact_variables iv2
                    WHERE iv2.variable_name = iv.variable_name
                      AND (iv2.commodity_id IS iv.commodity_id)
                )
                GROUP BY iv.commodity_id, iv.variable_name
                ORDER BY iv.commodity_id, iv.variable_name
                """
            ).fetchall()
    return [dict(r) for r in rows]


@router.get("/")
def list_variables(
    commodity: str | None = Query(default=None),
    variable: str | None = Query(default=None),
    days: int = Query(default=180, ge=1, le=1825),
):
    filters = ["iv.date >= date('now', ? || ' days')"]
    params: list = [f"-{days}"]

    if commodity:
        filters.append("iv.commodity_id = ?")
        params.append(commodity)
    if variable:
        filters.append("iv.variable_name = ?")
        params.append(variable)

    where = " AND ".join(filters)
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM impact_variables iv WHERE {where} ORDER BY iv.commodity_id, iv.variable_name, iv.date ASC",
            params,
        ).fetchall()
    return [dict(r) for r in rows]
