"""
Pisubí — Pipeline de Resumen Semanal
Genera un resumen LLM por commodity usando noticias + variables de la última semana.

Uso:
  python -m backend.pipelines.summary              # todos los commodities
  python -m backend.pipelines.summary --commodity gold
  python -m backend.pipelines.summary --days 14    # ampliar ventana de noticias
"""
import sys
import argparse
from datetime import date, timedelta
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


class SummaryPipeline(BasePipeline):

    def __init__(self):
        super().__init__("summary")

    def _get_recent_news(self, conn, commodity_id: str, days: int) -> list[dict]:
        rows = conn.execute(
            """
            SELECT title, snippet, sentiment, signal_type,
                   relevance_score, summary_es, impact_direction
            FROM news
            WHERE commodity_id = ?
              AND classified_at IS NOT NULL
              AND published_at >= date('now', ? || ' days')
            ORDER BY relevance_score DESC NULLS LAST, published_at DESC
            LIMIT 15
            """,
            (commodity_id, f"-{days}"),
        ).fetchall()
        return [dict(r) for r in rows]

    def _get_variables(self, conn, commodity_id: str) -> list[dict]:
        """Variables globales + las del commodity."""
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
            ORDER BY iv.variable_name
            """,
            (commodity_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def _get_trade_summary(self, conn, commodity_id: str) -> dict | None:
        row = conn.execute(
            """
            SELECT commodity_id,
                   SUM(value_usd) AS total_export_usd,
                   MIN(period)    AS from_period,
                   MAX(period)    AS to_period,
                   COUNT(*)       AS data_points
            FROM trade_flows
            WHERE commodity_id = ?
              AND flow_type = 'export'
              AND period >= strftime('%Y-%m', date('now', '-12 months'))
            GROUP BY commodity_id
            """,
            (commodity_id,),
        ).fetchone()
        return dict(row) if row else None

    def run(self, commodity_id: str | None = None, days: int = 7) -> None:
        targets = (
            {commodity_id: COMMODITIES[commodity_id]}
            if commodity_id
            else COMMODITIES
        )

        with self.get_conn() as conn:
            today = date.today()
            period_start = today - timedelta(days=days)

            for cid, name_es in targets.items():
                self.log(f"Generando resumen para {name_es}...")

                news     = self._get_recent_news(conn, cid, days)
                variables = self._get_variables(conn, cid)
                trade    = self._get_trade_summary(conn, cid)

                if not news and not variables:
                    self.log(f"  Sin datos para {cid}, saltando.")
                    continue

                try:
                    result = llm.generate_weekly_summary(
                        commodity_name=name_es,
                        news_items=news,
                        variables=variables,
                        trade_summary=trade,
                    )
                except Exception as exc:
                    self.log(f"  LLM error {cid}: {exc}")
                    continue

                import json
                key_signals_json = json.dumps(
                    result.get("key_signals", []), ensure_ascii=False
                )

                try:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO weekly_summaries
                            (commodity_id, period_start, period_end,
                             summary_text, key_signals, llm_provider)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            cid,
                            str(period_start),
                            str(today),
                            result.get("summary_text", ""),
                            key_signals_json,
                            result.get("llm_provider"),
                        ),
                    )
                    conn.commit()
                    self._records_processed += 1
                    self.log(f"  OK [{result.get('llm_provider')}]")
                except Exception as exc:
                    self.log(f"  DB error {cid}: {exc}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline de resumen semanal Pisubí")
    parser.add_argument(
        "--commodity",
        choices=list(COMMODITIES.keys()),
        default=None,
        help="Commodity a resumir (default: todos)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Ventana de noticias en días (default: 7)",
    )
    args = parser.parse_args()

    pl = SummaryPipeline()
    with pl.run_context():
        pl.run(commodity_id=args.commodity, days=args.days)
