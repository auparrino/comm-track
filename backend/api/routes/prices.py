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


# ─── Señales técnicas ────────────────────────────────────────────────────────

def _ema_series(prices: list[float], period: int) -> list[float]:
    if len(prices) < period:
        return []
    k = 2 / (period + 1)
    result = [sum(prices[:period]) / period]
    for p in prices[period:]:
        result.append(p * k + result[-1] * (1 - k))
    return result


def _sma_series(prices: list[float], period: int) -> list[float]:
    return [
        sum(prices[i - period:i]) / period
        for i in range(period, len(prices) + 1)
    ]


def _rsi(prices: list[float], period: int = 14) -> float | None:
    if len(prices) < period + 1:
        return None
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains  = [d if d > 0 else 0.0 for d in deltas]
    losses = [-d if d < 0 else 0.0 for d in deltas]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)


@router.get("/{commodity_id}/signals")
def price_signals(commodity_id: str):
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
    signals = []

    # ── RSI(14) ────────────────────────────────────────────────────────────────
    rsi = _rsi(prices)
    if rsi is not None:
        if rsi < 30:
            signals.append({
                "signal":    "RSI_OVERSOLD",
                "direction": "bullish",
                "label":     "RSI Sobrevendido",
                "detail":    f"RSI(14) = {rsi:.1f}",
                "strength":  "high" if rsi < 20 else "medium",
            })
        elif rsi > 70:
            signals.append({
                "signal":    "RSI_OVERBOUGHT",
                "direction": "bearish",
                "label":     "RSI Sobrecomprado",
                "detail":    f"RSI(14) = {rsi:.1f}",
                "strength":  "high" if rsi > 80 else "medium",
            })

    # ── MACD (12/26/9) ────────────────────────────────────────────────────────
    ema12 = _ema_series(prices, 12)
    ema26 = _ema_series(prices, 26)
    # Alinear al tramo común
    offset = 26 - 12  # ema26 es más corta en (period-1) elementos
    if len(ema12) > offset and len(ema26) > 0:
        macd_line = [ema12[offset + i] - ema26[i] for i in range(len(ema26))]
        signal_line = _ema_series(macd_line, 9)
        if len(macd_line) > 9 and len(signal_line) >= 2:
            # Cruce reciente (último vs penúltimo)
            macd_tail    = macd_line[-(len(signal_line)):]
            prev_diff = macd_tail[-2] - signal_line[-2]
            curr_diff = macd_tail[-1] - signal_line[-1]
            if prev_diff < 0 < curr_diff:
                signals.append({
                    "signal":    "MACD_BULLISH_CROSS",
                    "direction": "bullish",
                    "label":     "MACD Cruce Alcista",
                    "detail":    f"MACD cruzó señal hacia arriba",
                    "strength":  "medium",
                })
            elif prev_diff > 0 > curr_diff:
                signals.append({
                    "signal":    "MACD_BEARISH_CROSS",
                    "direction": "bearish",
                    "label":     "MACD Cruce Bajista",
                    "detail":    f"MACD cruzó señal hacia abajo",
                    "strength":  "medium",
                })

    # ── Golden / Death Cross (SMA50 × SMA200) ────────────────────────────────
    sma50  = _sma_series(prices, 50)
    sma200 = _sma_series(prices, 200)
    if len(sma50) >= 2 and len(sma200) >= 2:
        # Alinear: sma200 empieza 150 pasos después de sma50
        diff_len = len(sma50) - len(sma200)
        if diff_len >= 0:
            s50_aligned = sma50[diff_len:]
            prev50, curr50   = s50_aligned[-2], s50_aligned[-1]
            prev200, curr200 = sma200[-2], sma200[-1]
            if prev50 <= prev200 and curr50 > curr200:
                signals.append({
                    "signal":    "GOLDEN_CROSS",
                    "direction": "bullish",
                    "label":     "Golden Cross",
                    "detail":    "SMA50 cruzó sobre SMA200",
                    "strength":  "high",
                })
            elif prev50 >= prev200 and curr50 < curr200:
                signals.append({
                    "signal":    "DEATH_CROSS",
                    "direction": "bearish",
                    "label":     "Death Cross",
                    "detail":    "SMA50 cruzó bajo SMA200",
                    "strength":  "high",
                })

    # ── Bollinger Breakout (SMA20 ± 2σ) ──────────────────────────────────────
    if len(prices) >= 20:
        sma20 = sum(prices[-20:]) / 20
        std   = (sum((p - sma20) ** 2 for p in prices[-20:]) / 20) ** 0.5
        upper = sma20 + 2 * std
        lower = sma20 - 2 * std
        current = prices[-1]
        if current > upper:
            signals.append({
                "signal":    "BOLL_BREAKOUT_UP",
                "direction": "bullish",
                "label":     "Bollinger Breakout+",
                "detail":    f"Precio {current:.2f} > banda sup {upper:.2f}",
                "strength":  "medium",
            })
        elif current < lower:
            signals.append({
                "signal":    "BOLL_BREAKOUT_DOWN",
                "direction": "bearish",
                "label":     "Bollinger Breakout-",
                "detail":    f"Precio {current:.2f} < banda inf {lower:.2f}",
                "strength":  "medium",
            })

    return {
        "commodity_id": commodity_id,
        "signals":      signals,
        "rsi":          round(rsi, 1) if rsi is not None else None,
        "n_days":       len(prices),
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
