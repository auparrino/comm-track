"""
Pisubí — Pipeline de Alertas de Alto Impacto
Detecta señales de alta relevancia en noticias recientes y genera alertas LLM.

Uso:
  python -m backend.pipelines.alerts              # todos los commodities
  python -m backend.pipelines.alerts --commodity gold
  python -m backend.pipelines.alerts --threshold 0.6
"""
import sys
import json
import argparse
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.config import DB_PATH
from backend.pipelines.base_pipeline import BasePipeline
from backend.pipelines.llm_client import llm


COMMODITIES = {
    "lithium": "Litio",
    "gold":    "Oro",
    "soy":     "Soja",
    "copper":  "Cobre",
    "natgas":  "Gas Natural",
    "wheat":   "Trigo",
}

# Por defecto: relevance_score >= 0.7 y direction no neutral
DEFAULT_THRESHOLD = 0.7


class AlertsPipeline(BasePipeline):

    def __init__(self):
        super().__init__("alerts")
        self._ensure_table()

    def _ensure_table(self) -> None:
        with self.get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    commodity_id   TEXT REFERENCES commodities(id),
                    generated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    title          TEXT NOT NULL,
                    description    TEXT,
                    severity       TEXT,       -- 'high', 'medium'
                    signal_type    TEXT,
                    llm_provider   TEXT,
                    source_news_ids TEXT,       -- JSON array de news.id
                    is_active      BOOLEAN DEFAULT 1,
                    expires_at     DATE
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_alerts_commodity ON alerts(commodity_id, generated_at DESC)"
            )
            conn.commit()

    def _get_high_impact_news(
        self, conn, commodity_id: str, threshold: float, days: int = 7
    ) -> list[dict]:
        rows = conn.execute(
            """
            SELECT id, title, snippet, sentiment, signal_type,
                   relevance_score, summary_es, impact_direction
            FROM news
            WHERE commodity_id = ?
              AND relevance_score >= ?
              AND impact_direction IN ('bullish', 'bearish')
              AND published_at >= date('now', ? || ' days')
            ORDER BY relevance_score DESC
            LIMIT 10
            """,
            (commodity_id, threshold, f"-{days}"),
        ).fetchall()
        return [dict(r) for r in rows]

    def _get_variables(self, conn, commodity_id: str) -> list[dict]:
        rows = conn.execute(
            """
            SELECT iv.*
            FROM impact_variables iv
            INNER JOIN (
                SELECT COALESCE(commodity_id, 'NULL') AS cid,
                       variable_name,
                       MAX(date) AS max_date
                FROM impact_variables
                WHERE commodity_id = ? OR commodity_id IS NULL
                GROUP BY cid, variable_name
            ) latest ON COALESCE(iv.commodity_id, 'NULL') = latest.cid
                     AND iv.variable_name = latest.variable_name
                     AND iv.date = latest.max_date
            """,
            (commodity_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def run(
        self,
        commodity_id: str | None = None,
        threshold: float = DEFAULT_THRESHOLD,
        days: int = 7,
    ) -> None:
        targets = (
            {commodity_id: COMMODITIES[commodity_id]}
            if commodity_id
            else COMMODITIES
        )

        today = date.today()
        expires = date(today.year, today.month, today.day)

        with self.get_conn() as conn:
            for cid, name_es in targets.items():
                self.log(f"Analizando señales para {name_es}...")

                news      = self._get_high_impact_news(conn, cid, threshold, days)
                variables = self._get_variables(conn, cid)

                if not news:
                    self.log(f"  Sin señales de alto impacto para {cid}")
                    continue

                self.log(f"  {len(news)} noticias de alto impacto")
                news_ids = [n["id"] for n in news]

                try:
                    alerts = llm.generate_alerts(
                        commodity_name=name_es,
                        high_impact_news=news,
                        variables=variables,
                    )
                except Exception as exc:
                    self.log(f"  LLM error {cid}: {exc}")
                    continue

                for alert in alerts:
                    # Desactivar alertas previas del mismo commodity
                    conn.execute(
                        "UPDATE alerts SET is_active=0 WHERE commodity_id=? AND is_active=1",
                        (cid,),
                    )
                    conn.execute(
                        """
                        INSERT INTO alerts
                            (commodity_id, title, description, severity,
                             signal_type, llm_provider, source_news_ids, expires_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            cid,
                            alert.get("title", ""),
                            alert.get("description", ""),
                            alert.get("severity", "medium"),
                            alert.get("signal_type", "other"),
                            alert.get("llm_provider"),
                            json.dumps(news_ids),
                            str(today + __import__("datetime").timedelta(days=7)),
                        ),
                    )
                    self._records_processed += 1
                    self.log(f"  Alerta [{alert.get('severity')}]: {alert.get('title')}")

                conn.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline de alertas Pisubí")
    parser.add_argument("--commodity", choices=list(COMMODITIES.keys()), default=None)
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help=f"Mínimo relevance_score (default: {DEFAULT_THRESHOLD})",
    )
    parser.add_argument("--days", type=int, default=7)
    args = parser.parse_args()

    pl = AlertsPipeline()
    with pl.run_context():
        pl.run(
            commodity_id=args.commodity,
            threshold=args.threshold,
            days=args.days,
        )
