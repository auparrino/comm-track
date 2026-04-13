"""
Pisubí — Clase base para pipelines de datos
Maneja logging en DB, manejo de errores y contexto de ejecución.
"""
import sqlite3
from datetime import datetime
from typing import Optional
from contextlib import contextmanager
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from backend.config import DB_PATH


class BasePipeline:
    def __init__(self, name: str, commodity_id: Optional[str] = None):
        self.name = name
        self.commodity_id = commodity_id
        self._run_id: Optional[int] = None
        self._records_processed = 0
        self._records_skipped = 0

    def get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def log(self, msg: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] [{self.name}] {msg}")

    def _start_run(self) -> int:
        with self.get_conn() as conn:
            cur = conn.execute("""
                INSERT INTO pipeline_runs (pipeline_name, commodity_id, started_at, status)
                VALUES (?, ?, ?, 'running')
            """, (self.name, self.commodity_id, datetime.utcnow()))
            conn.commit()
            return cur.lastrowid

    def _finish_run(self, run_id: int, status: str, error: Optional[str] = None) -> None:
        with self.get_conn() as conn:
            conn.execute("""
                UPDATE pipeline_runs
                SET finished_at = ?, status = ?,
                    records_processed = ?, records_skipped = ?,
                    error_message = ?
                WHERE id = ?
            """, (datetime.utcnow(), status,
                  self._records_processed, self._records_skipped,
                  error, run_id))
            conn.commit()

    @contextmanager
    def run_context(self):
        """Context manager que loguea inicio/fin en pipeline_runs."""
        run_id = self._start_run()
        self.log(f"Iniciando (run_id={run_id})")
        try:
            yield self
            self._finish_run(run_id, "success")
            self.log(f"OK — {self._records_processed} procesados, {self._records_skipped} saltados")
        except Exception as exc:
            self._finish_run(run_id, "error", str(exc))
            self.log(f"ERROR: {exc}")
            raise

    def upsert_price(
        self,
        conn: sqlite3.Connection,
        commodity_id: str,
        date: str,
        price: float,
        source: str,
        price_type: str = "spot",
        currency: str = "USD",
    ) -> bool:
        """
        Inserta precio si no existe. Retorna True si fue insertado (nuevo),
        False si ya existía (saltado).
        """
        try:
            conn.execute("""
                INSERT INTO prices (commodity_id, date, price, source, price_type, currency)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (commodity_id, date, price, source, price_type, currency))
            self._records_processed += 1
            return True
        except sqlite3.IntegrityError:
            self._records_skipped += 1
            return False

    def upsert_company_valuation(
        self,
        conn: sqlite3.Connection,
        company_id: int,
        date: str,
        close_price: Optional[float],
        open_price: Optional[float] = None,
        high_price: Optional[float] = None,
        low_price: Optional[float] = None,
        volume: Optional[int] = None,
        market_cap_usd: Optional[float] = None,
        currency: str = "USD",
        source: str = "yahoo",
    ) -> bool:
        try:
            conn.execute("""
                INSERT INTO company_valuations
                    (company_id, date, close_price, open_price, high_price,
                     low_price, volume, market_cap_usd, currency, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (company_id, date, close_price, open_price, high_price,
                  low_price, volume, market_cap_usd, currency, source))
            self._records_processed += 1
            return True
        except sqlite3.IntegrityError:
            self._records_skipped += 1
            return False
