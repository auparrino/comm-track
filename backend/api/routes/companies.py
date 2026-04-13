"""
GET /companies                          ?commodity=
GET /companies/{company_id}
GET /companies/{company_id}/valuations  ?days=90
"""
from fastapi import APIRouter, HTTPException, Query
from backend.db.init_db import get_conn

router = APIRouter()


@router.get("/")
def list_companies(commodity: str | None = Query(default=None)):
    with get_conn() as conn:
        if commodity:
            rows = conn.execute(
                "SELECT * FROM companies WHERE commodity_id = ? ORDER BY name",
                (commodity,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM companies ORDER BY commodity_id, name"
            ).fetchall()
    return [dict(r) for r in rows]


@router.get("/{company_id}")
def get_company(company_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM companies WHERE id = ?", (company_id,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Empresa id={company_id} no encontrada")
    return dict(row)


@router.get("/{company_id}/valuations")
def company_valuations(
    company_id: int,
    days: int = Query(default=90, ge=1, le=1825),
):
    with get_conn() as conn:
        # verify company exists
        exists = conn.execute(
            "SELECT id FROM companies WHERE id = ?", (company_id,)
        ).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail=f"Empresa id={company_id} no encontrada")

        rows = conn.execute(
            """
            SELECT cv.*, c.name, c.ticker, c.commodity_id
            FROM company_valuations cv
            JOIN companies c ON c.id = cv.company_id
            WHERE cv.company_id = ?
              AND cv.date >= date('now', ? || ' days')
            ORDER BY cv.date ASC
            """,
            (company_id, f"-{days}"),
        ).fetchall()
    return [dict(r) for r in rows]
