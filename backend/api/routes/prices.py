"""
GET /prices/correlations              ?window=90
GET /prices/{commodity_id}/regime
GET /prices/{commodity_id}/latest
GET /prices/{commodity_id}            ?days=90&source=&price_type=
"""
from fastapi import APIRouter, HTTPException, Query
from backend.db.init_db import get_conn

router = APIRouter()


# ─── Correlaciones cruzadas ───────────────────────────────────────────────────

def _pearson(x: list[float], y: list[float]) -> float | None:
    n = len(x)
    if n < 2:
        return None
    mx = sum(x) / n
    my = sum(y) / n
    num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    dx = sum((xi - mx) ** 2 for xi in x) ** 0.5
    dy = sum((yi - my) ** 2 for yi in y) ** 0.5
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


@router.get("/correlations")
def price_correlations(window: int = Query(default=90, ge=30, le=365)):
    with get_conn() as conn:
        commodity_ids = [
            r["id"] for r in
            conn.execute("SELECT id FROM commodities ORDER BY id").fetchall()
        ]
        price_data: dict[str, dict[str, float]] = {}
        for cid in commodity_ids:
            rows = conn.execute(
                """
                SELECT date, AVG(price) AS price
                FROM prices
                WHERE commodity_id = ?
                  AND date >= date('now', ? || ' days')
                GROUP BY date
                ORDER BY date ASC
                """,
                (cid, f"-{window}"),
            ).fetchall()
            price_data[cid] = {r["date"]: r["price"] for r in rows}

    active = [c for c in commodity_ids if len(price_data[c]) >= 10]

    matrix = []
    for c1 in active:
        for c2 in active:
            if c1 == c2:
                matrix.append({"c1": c1, "c2": c2, "r": 1.0, "n": len(price_data[c1])})
                continue
            dates = sorted(set(price_data[c1]) & set(price_data[c2]))
            if len(dates) < 10:
                matrix.append({"c1": c1, "c2": c2, "r": None, "n": len(dates)})
                continue
            x = [price_data[c1][d] for d in dates]
            y = [price_data[c2][d] for d in dates]
            r = _pearson(x, y)
            matrix.append({
                "c1": c1,
                "c2": c2,
                "r":  round(r, 3) if r is not None else None,
                "n":  len(dates),
            })

    return {"window": window, "commodities": active, "matrix": matrix}


# ─── Régimen de mercado ───────────────────────────────────────────────────────

@router.get("/{commodity_id}/regime")
def price_regime(commodity_id: str):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT date, AVG(price) AS price
            FROM prices
            WHERE commodity_id = ?
              AND date >= date('now', '-400 days')
            GROUP BY date
            ORDER BY date ASC
            """,
            (commodity_id,),
        ).fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail=f"Sin precios para '{commodity_id}'")

    prices = [r["price"] for r in rows]

    def sma(n: int) -> float | None:
        return sum(prices[-n:]) / n if len(prices) >= n else None

    sma20  = sma(20)
    sma50  = sma(50)
    sma200 = sma(200)
    current = prices[-1]

    boll_upper = boll_lower = cv = None
    if sma20 is not None and len(prices) >= 20:
        last20 = prices[-20:]
        std = (sum((p - sma20) ** 2 for p in last20) / 20) ** 0.5
        boll_upper = sma20 + 2 * std
        boll_lower = sma20 - 2 * std
        cv = std / sma20 if sma20 != 0 else 0

    # Lógica de régimen
    if sma20 and sma50 and sma200:
        if sma20 > sma50 > sma200:
            regime = "ALCISTA"
        elif sma20 < sma50 < sma200:
            regime = "BAJISTA"
        elif cv and cv > 0.04:
            regime = "VOLÁTIL"
        else:
            regime = "LATERAL"
    elif cv and cv > 0.04:
        regime = "VOLÁTIL"
    else:
        regime = "LATERAL"

    return {
        "commodity_id": commodity_id,
        "regime":        regime,
        "current_price": round(current, 4),
        "sma20":         round(sma20,  2) if sma20  else None,
        "sma50":         round(sma50,  2) if sma50  else None,
        "sma200":        round(sma200, 2) if sma200 else None,
        "boll_upper":    round(boll_upper, 2) if boll_upper else None,
        "boll_lower":    round(boll_lower, 2) if boll_lower else None,
        "n_days":        len(prices),
    }


# ─── Histórico y latest ───────────────────────────────────────────────────────

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
