"""
GET /commodities
GET /commodities/{commodity_id}
"""
import json
from fastapi import APIRouter, HTTPException
from backend.db.init_db import get_conn

router = APIRouter()


@router.get("/")
def list_commodities():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, name_es, name_en, unit, category, description FROM commodities ORDER BY id"
        ).fetchall()
    return [dict(r) for r in rows]


@router.get("/{commodity_id}")
def get_commodity(commodity_id: str):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM commodities WHERE id = ?", (commodity_id,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Commodity '{commodity_id}' no encontrado")
    data = dict(row)
    if data.get("supply_chain_json"):
        data["supply_chain"] = json.loads(data.pop("supply_chain_json"))
    else:
        data.pop("supply_chain_json", None)
    return data
