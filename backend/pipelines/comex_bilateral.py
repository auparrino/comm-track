"""
Pisubí — Pipeline de Comercio Exterior Bilateral
Fuente: comex-IED (public/data/trade/products.json)
        Estructura: {país: {año: {exp: {cap_ncm: usd}, imp: ...}}}
        Datos anuales 2015-2026, 80 países, 2 dígitos NCM.

Uso:
  python -m backend.pipelines.comex_bilateral              # 2015–hoy
  python -m backend.pipelines.comex_bilateral --from 2020  # desde 2020
"""
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.config import DB_PATH
from backend.pipelines.base_pipeline import BasePipeline


# Ruta al archivo del repo comex-IED
COMEX_IED_PATH = Path(
    "C:/Users/augus/OneDrive/Documentos/Comex/comex-IED"
    "/public/data/trade/products.json"
)

# Capítulos NCM 2 dígitos por commodity (mismos que comex.py)
COMMODITY_NCM: dict[str, list[str]] = {
    "lithium": ["28"],
    "gold":    ["71"],
    "soy":     ["12", "15", "23"],
}


class ComexBilateralPipeline(BasePipeline):

    def __init__(self):
        super().__init__("comex_bilateral")

    def run(self, from_year: int = 2015) -> None:
        if not COMEX_IED_PATH.exists():
            self.log(f"ERROR: no se encontró {COMEX_IED_PATH}")
            return

        self.log(f"Cargando {COMEX_IED_PATH.name}...")
        with open(COMEX_IED_PATH, encoding="utf-8") as f:
            data: dict = json.load(f)

        countries = list(data.keys())
        self.log(f"  {len(countries)} países, años {from_year}+")

        with self.get_conn() as conn:
            for country, year_data in data.items():
                for year_str, flows in year_data.items():
                    if int(year_str) < from_year:
                        continue

                    period = year_str  # almacenamos año como '2024'

                    for flow_type, col_key, country_col in [
                        ("export", "exp", "country_dest"),
                        ("import", "imp", "country_origin"),
                    ]:
                        chapter_values: dict = flows.get(col_key, {})

                        for commodity_id, chapters in COMMODITY_NCM.items():
                            for cap in chapters:
                                value_usd = chapter_values.get(cap)
                                if value_usd is None:
                                    continue

                                try:
                                    if country_col == "country_dest":
                                        cur = conn.execute(
                                            """
                                            INSERT OR IGNORE INTO trade_flows
                                                (commodity_id, ncm, period, flow_type,
                                                 country_dest, value_usd, source)
                                            VALUES (?, ?, ?, ?, ?, ?, 'comex_ied')
                                            """,
                                            (commodity_id, cap, period,
                                             flow_type, country, value_usd),
                                        )
                                    else:
                                        cur = conn.execute(
                                            """
                                            INSERT OR IGNORE INTO trade_flows
                                                (commodity_id, ncm, period, flow_type,
                                                 country_origin, value_usd, source)
                                            VALUES (?, ?, ?, ?, ?, ?, 'comex_ied')
                                            """,
                                            (commodity_id, cap, period,
                                             flow_type, country, value_usd),
                                        )

                                    if cur.rowcount > 0:
                                        self._records_processed += 1
                                    else:
                                        self._records_skipped += 1

                                except Exception as exc:
                                    self.log(
                                        f"  DB error {commodity_id}/cap{cap}"
                                        f"/{country}/{period}: {exc}"
                                    )

            conn.commit()
            self.log(
                f"Bilateral completo: {self._records_processed} nuevos, "
                f"{self._records_skipped} duplicados"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline Comex Bilateral Pisubí")
    parser.add_argument(
        "--from",
        dest="from_year",
        type=int,
        default=2015,
        help="Año de inicio (default: 2015)",
    )
    args = parser.parse_args()

    pl = ComexBilateralPipeline()
    with pl.run_context():
        pl.run(from_year=args.from_year)
