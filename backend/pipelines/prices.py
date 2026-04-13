"""
Pisubí — Pipeline de Precios
Fuentes: Yahoo Finance (commodities futuros + acciones de empresas), BCRA, FRED

Cron: diario 08:00 UTC (05:00 AR)
Uso manual: python -m backend.pipelines.prices [--days 30]
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import Optional
import time

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import yfinance as yf
import requests

from backend.config import (
    COMMODITY_TICKERS,
    COMPANY_TICKERS,
    FRED_API_KEY,
    FRED_SERIES,
    BCRA_BASE_URL,
    DB_PATH,
)
from backend.pipelines.base_pipeline import BasePipeline


# ──────────────────────────────────────────────
# Subpipeline 1: Yahoo Finance — commodities
# ──────────────────────────────────────────────

class YahooCommoditiesPipeline(BasePipeline):
    """Descarga precios de futuros y ETFs desde Yahoo Finance."""

    # Mapeo símbolo → commodity_id
    SYMBOL_COMMODITY = {
        "GC=F":  ("gold",    "futures"),
        "GLD":   ("gold",    "etf"),
        "ZS=F":  ("soy",     "futures"),
        "ZM=F":  ("soy",     "futures"),   # harina — lo guardamos igual con price_type distinto
        "ZL=F":  ("soy",     "futures"),   # aceite
        "LIT":   ("lithium", "etf"),       # proxy ETF litio (no hay futures directos)
        "HG=F":  ("copper",  "futures"),   # COMEX High-Grade Copper (CU=F es ticker inactivo)
        "NG=F":  ("natgas",  "futures"),
        "ZW=F":  ("wheat",   "futures"),
        "ZC=F":  ("corn",    "futures"),
    }
    # Para aceite y harina usamos sufijos específicos
    SYMBOL_OVERRIDES = {
        "ZM=F": {"commodity_id": "soy", "price_type": "futures_meal"},
        "ZL=F": {"commodity_id": "soy", "price_type": "futures_oil"},
    }

    def __init__(self):
        super().__init__("yahoo_commodities")

    def run(self, days: int = 30) -> None:
        symbols = list(self.SYMBOL_COMMODITY.keys())
        period = f"{days}d"
        self.log(f"Descargando {symbols} | período {days}d")

        data = yf.download(symbols, period=period, auto_adjust=True, progress=False)

        if data.empty:
            self.log("Sin datos de Yahoo Finance.")
            return

        with self.get_conn() as conn:
            close = data["Close"] if "Close" in data.columns else data
            for symbol in symbols:
                if symbol not in close.columns:
                    continue

                overrides = self.SYMBOL_OVERRIDES.get(symbol, {})
                commodity_id = overrides.get("commodity_id") or self.SYMBOL_COMMODITY[symbol][0]
                price_type   = overrides.get("price_type")   or self.SYMBOL_COMMODITY[symbol][1]

                series = close[symbol].dropna()
                for idx_date, price in series.items():
                    date_str = idx_date.strftime("%Y-%m-%d") if hasattr(idx_date, "strftime") else str(idx_date)[:10]
                    self.upsert_price(conn, commodity_id, date_str, float(price),
                                      source="yahoo", price_type=price_type)

            conn.commit()
        self.log(f"Yahoo commodities: {self._records_processed} nuevos, {self._records_skipped} ya existían")


# ──────────────────────────────────────────────
# Subpipeline 2: Yahoo Finance — empresas
# ──────────────────────────────────────────────

class YahooCompaniesPipeline(BasePipeline):
    """Descarga precios de acciones de empresas vinculadas a commodities."""

    def __init__(self):
        super().__init__("yahoo_companies")

    def _get_company_ids(self, conn) -> dict[str, int]:
        """Retorna {ticker: company_id} para todos los tickers con datos en DB."""
        rows = conn.execute(
            "SELECT id, ticker FROM companies WHERE ticker IS NOT NULL"
        ).fetchall()
        return {row["ticker"]: row["id"] for row in rows}

    def run(self, days: int = 30) -> None:
        tickers = list(COMPANY_TICKERS.keys())
        period = f"{days}d"
        self.log(f"Descargando acciones: {tickers} | período {days}d")

        # Descargar todo de una vez (más eficiente)
        data = yf.download(tickers, period=period, auto_adjust=True, progress=False)

        if data.empty:
            self.log("Sin datos de Yahoo Finance para empresas.")
            return

        with self.get_conn() as conn:
            company_ids = self._get_company_ids(conn)

            # Intentar obtener market cap por ticker individualmente
            market_caps: dict[str, dict] = {}
            for ticker in tickers:
                try:
                    info = yf.Ticker(ticker).fast_info
                    market_caps[ticker] = {
                        "market_cap": getattr(info, "market_cap", None),
                        "currency":   getattr(info, "currency", "USD"),
                    }
                    time.sleep(0.1)  # cortesía hacia la API
                except Exception:
                    market_caps[ticker] = {"market_cap": None, "currency": "USD"}

            close_df  = data.get("Close",  data)
            open_df   = data.get("Open",   None)
            high_df   = data.get("High",   None)
            low_df    = data.get("Low",    None)
            volume_df = data.get("Volume", None)

            for ticker in tickers:
                company_id = company_ids.get(ticker)
                if company_id is None:
                    self.log(f"  {ticker}: no encontrado en DB, saltando")
                    continue

                if ticker not in close_df.columns:
                    continue

                mc_info  = market_caps.get(ticker, {})
                currency = mc_info.get("currency", "USD")
                mktcap   = mc_info.get("market_cap")

                series = close_df[ticker].dropna()
                for idx_date, close_price in series.items():
                    date_str = idx_date.strftime("%Y-%m-%d") if hasattr(idx_date, "strftime") else str(idx_date)[:10]

                    def safe_get(df, col_ticker, idx):
                        if df is not None and col_ticker in df.columns:
                            val = df[col_ticker].get(idx)
                            return float(val) if val is not None and val == val else None
                        return None

                    self.upsert_company_valuation(
                        conn,
                        company_id=company_id,
                        date=date_str,
                        close_price=float(close_price),
                        open_price=safe_get(open_df, ticker, idx_date),
                        high_price=safe_get(high_df, ticker, idx_date),
                        low_price=safe_get(low_df, ticker, idx_date),
                        volume=int(volume_df[ticker].get(idx_date)) if volume_df is not None and ticker in volume_df.columns and volume_df[ticker].get(idx_date) == volume_df[ticker].get(idx_date) else None,
                        market_cap_usd=mktcap,
                        currency=currency,
                    )

            conn.commit()
        self.log(f"Empresas: {self._records_processed} nuevos, {self._records_skipped} ya existían")


# ──────────────────────────────────────────────
# Subpipeline 3: Variables macro vía Yahoo Finance
# TC USD/ARS, DXY y Fed Rate proxy — sin API key
# ──────────────────────────────────────────────

class YahooMacroPipeline(BasePipeline):
    """
    Descarga variables macroeconómicas globales usando Yahoo Finance.
    No requiere API keys.

    USDARS=X   → tc_oficial_usd_ars  (tipo de cambio USD/ARS, referencia Yahoo)
    DX-Y.NYB   → broad_dollar_idx    (ICE Dollar Index, proxy DXY)
    ^IRX       → fed_funds_rate      (T-bill 13 semanas, proxy tasa Fed)
    """

    # symbol → (variable_name, commodity_id, unit, description)
    MACRO_SYMBOLS: dict[str, tuple] = {
        "USDARS=X": ("tc_oficial_usd_ars", None,   "ARS/USD", "Tipo de cambio USD/ARS (Yahoo Forex)"),
        "DX-Y.NYB": ("broad_dollar_idx",   None,   "index",   "ICE Dollar Index (proxy DXY)"),
        "^IRX":     ("fed_funds_rate",      None,   "%",       "T-bill 13 semanas (proxy Fed Rate)"),
    }

    def __init__(self):
        super().__init__("yahoo_macro")

    def run(self, days: int = 90) -> None:
        symbols = list(self.MACRO_SYMBOLS.keys())
        self.log(f"Descargando macro: {symbols} | {days}d")

        data = yf.download(symbols, period=f"{days}d", auto_adjust=True, progress=False)
        if data.empty:
            self.log("Sin datos de Yahoo Finance para macro.")
            return

        with self.get_conn() as conn:
            close = data["Close"] if "Close" in data.columns else data

            for symbol, (var_name, commodity_id, unit, _desc) in self.MACRO_SYMBOLS.items():
                if symbol not in close.columns:
                    self.log(f"  {symbol}: no encontrado en respuesta")
                    continue

                series = close[symbol].dropna()
                for idx_date, value in series.items():
                    date_str = idx_date.strftime("%Y-%m-%d") if hasattr(idx_date, "strftime") else str(idx_date)[:10]
                    try:
                        conn.execute("""
                            INSERT OR IGNORE INTO impact_variables
                                (commodity_id, variable_name, date, value, source, unit)
                            VALUES (?, ?, ?, ?, 'yahoo', ?)
                        """, (commodity_id, var_name, date_str, float(value), unit))
                        self._records_processed += 1
                    except Exception:
                        self._records_skipped += 1

            conn.commit()
        self.log(f"Yahoo macro: {self._records_processed} nuevos, {self._records_skipped} ya existian")


# ──────────────────────────────────────────────
# Subpipeline 4 (legacy): FRED
# Se ejecuta solo si FRED_API_KEY está configurada.
# Si no hay key, los datos llegan de YahooMacroPipeline.
# ──────────────────────────────────────────────

class FREDPipeline(BasePipeline):
    """
    Descarga series de la Fed usando la API pública de FRED.
    Requiere FRED_API_KEY en .env. Si no está configurada, se omite
    (los proxies de yfinance en YahooMacroPipeline cubren Fed Rate y DXY).
    """

    BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

    def __init__(self):
        super().__init__("fred")

    def _fetch_series(self, series_id: str, days: int) -> list[dict]:
        end   = date.today()
        start = end - timedelta(days=days)
        params = {
            "series_id":         series_id,
            "observation_start": start.strftime("%Y-%m-%d"),
            "observation_end":   end.strftime("%Y-%m-%d"),
            "api_key":           FRED_API_KEY,
            "file_type":         "json",
        }
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=15)
            resp.raise_for_status()
            return resp.json().get("observations", [])
        except requests.RequestException as exc:
            self.log(f"FRED {series_id} error: {exc}")
            return []

    SERIES_META = {
        "FEDFUNDS": ("fed_funds_rate",   None,   "%"),
        "CPIAUCSL": ("cpi_us",           None,   "index"),
        "DTWEXBGS": ("broad_dollar_idx", None,   "index"),
    }

    def run(self, days: int = 90) -> None:
        if not FRED_API_KEY:
            self.log("FRED_API_KEY no configurada — omitiendo (datos cubiertos por YahooMacroPipeline)")
            return
        self.log(f"FRED: descargando {list(FRED_SERIES.values())} | {days}d")
        with self.get_conn() as conn:
            for name, series_id in FRED_SERIES.items():
                observations = self._fetch_series(series_id, days)
                meta = self.SERIES_META.get(series_id, (name, None, None))
                var_name, commodity_id, unit = meta
                for obs in observations:
                    d   = obs.get("date", "")[:10]
                    val = obs.get("value", ".")
                    if val == ".":
                        continue
                    try:
                        conn.execute("""
                            INSERT OR IGNORE INTO impact_variables
                                (commodity_id, variable_name, date, value, source, unit)
                            VALUES (?, ?, ?, ?, 'fred', ?)
                        """, (commodity_id, var_name, d, float(val), unit))
                        self._records_processed += 1
                    except Exception:
                        self._records_skipped += 1
            conn.commit()
        self.log(f"FRED: {self._records_processed} registros guardados")


# ──────────────────────────────────────────────
# Runner principal
# ──────────────────────────────────────────────

def run_all(days: int = 30) -> None:
    pipelines = [
        YahooCommoditiesPipeline(),
        YahooCompaniesPipeline(),
        YahooMacroPipeline(),
        FREDPipeline(),     # solo corre si FRED_API_KEY configurada
    ]
    for pl in pipelines:
        with pl.run_context():
            pl.run(days=days)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline de precios Pisubí")
    parser.add_argument("--days", type=int, default=30,
                        help="Días hacia atrás para descargar (default: 30)")
    parser.add_argument("--pipeline", choices=["yahoo_c", "yahoo_e", "macro", "fred", "all"],
                        default="all", help="Pipeline a ejecutar")
    args = parser.parse_args()

    if args.pipeline == "yahoo_c":
        pl = YahooCommoditiesPipeline()
        with pl.run_context(): pl.run(args.days)
    elif args.pipeline == "yahoo_e":
        pl = YahooCompaniesPipeline()
        with pl.run_context(): pl.run(args.days)
    elif args.pipeline == "macro":
        pl = YahooMacroPipeline()
        with pl.run_context(): pl.run(args.days)
    elif args.pipeline == "fred":
        pl = FREDPipeline()
        with pl.run_context(): pl.run(args.days)
    else:
        run_all(args.days)
