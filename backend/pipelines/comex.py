"""
Pisubí — Pipeline de Comercio Exterior (Comex)
Fuente: datos.gob.ar — Exportaciones por NCM 2 dígitos, datos mensuales
        Dataset: sspm-exportaciones-segun-nomenclador-comun-mercosur-ncm
        Actualización: ~30 días de lag

Uso:
  python -m backend.pipelines.comex              # últimos 24 meses
  python -m backend.pipelines.comex --months 60  # últimos 60 meses
  python -m backend.pipelines.comex --all        # serie completa desde 1990
"""

import sys
import csv
import io
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import requests

from backend.config import DB_PATH
from backend.pipelines.base_pipeline import BasePipeline


# ──────────────────────────────────────────────────────────────────────────────
# Configuración
# ──────────────────────────────────────────────────────────────────────────────

DATOS_GOB_URL = (
    "https://infra.datos.gob.ar/catalog/sspm/dataset/162/distribution/162.3"
    "/download/exportaciones-clasificadas-nomenclador-comun-mercosur-ncm-2-digitos-mensual.csv"
)

# Capítulos NCM 2 dígitos relevantes por commodity.
# Nota: datos a nivel capítulo (agregado), no NCM 8 dígitos.
# Limitación conocida: Cap 28 incluye todos los inorgánicos, no solo litio.
#                      Cap 71 incluye oro + plata + piedras preciosas.
#                      Caps 12/15/23 cubren el complejo sojero AR.
COMMODITY_NCM_MAP: dict[str, list[tuple[str, str]]] = {
    "lithium": [
        ("28", "x_productos_quimicos_inorganicos_compuestos_inorganicos"),
    ],
    "gold": [
        ("71", "x_perlas_naturales_piedras_preciosas_semipreciosasa_monedas"),
    ],
    "soy": [
        ("12", "x_semillas_frutos_oleaginosos_semillas"),
        ("15", "x_grasas_aceites_animales_vegetales"),
        ("23", "x_residuos_desperdicios_industrias_alimentarias"),
    ],
    # Nuevos commodities (sesión 8)
    # Nota: cap.74 incluye cobre + manufacturas; cap.27 incluye combustibles en gral;
    #       cap.10 incluye todos los cereales (trigo + maíz + etc.)
    "copper": [
        ("74", "x_cobre_manufacturas_cobre"),
    ],
    "natgas": [
        ("27", "x_comb_minerales_aceites_minerales_productos_destilacion"),
    ],
    "wheat": [
        ("10", "x_cereales"),
    ],
    # Nota: cap.10 incluye todos los cereales (maíz + trigo + sorgo).
    # Al nivel 2 dígitos no es posible separar maíz de trigo; ambos comparten
    # la misma columna. El gráfico refleja el total del capítulo NCM 10.
    "corn": [
        ("10", "x_cereales"),
    ],
}

# Unidad del CSV: millones de USD corrientes
VALUE_UNIT_MULTIPLIER = 1_000_000


# ──────────────────────────────────────────────────────────────────────────────
# Pipeline
# ──────────────────────────────────────────────────────────────────────────────

class ComexPipeline(BasePipeline):

    def __init__(self):
        super().__init__("comex")

    def _ensure_unique_index(self, conn) -> None:
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_trade_unique
            ON trade_flows(commodity_id, ncm, period, flow_type,
                           COALESCE(country_dest, ''))
            """
        )

    def _download_csv(self) -> list[dict]:
        self.log("Descargando CSV de datos.gob.ar...")
        try:
            r = requests.get(
                DATOS_GOB_URL,
                timeout=30,
                headers={"User-Agent": "Pisubí-Bot/1.0"},
            )
            r.raise_for_status()
        except Exception as exc:
            self.log(f"  ERROR descargando CSV: {exc}")
            return []

        reader = csv.DictReader(io.StringIO(r.text))
        rows = list(reader)
        self.log(f"  {len(rows)} filas descargadas (1990-01 - {rows[-1]['indice_tiempo'][:7]})")
        return rows

    def run(self, months: int | None = 24) -> None:
        rows = self._download_csv()
        if not rows:
            return

        # Filtrar por período si corresponde
        if months is not None:
            rows = rows[-months:]
            self.log(f"  Filtrando últimos {months} meses")

        with self.get_conn() as conn:
            self._ensure_unique_index(conn)

            for commodity_id, ncm_cols in COMMODITY_NCM_MAP.items():
                for ncm_code, col_name in ncm_cols:
                    inserted = 0
                    skipped  = 0

                    for row in rows:
                        raw_val = row.get(col_name, "").strip()
                        if not raw_val:
                            continue

                        try:
                            value_usd = float(raw_val) * VALUE_UNIT_MULTIPLIER
                        except ValueError:
                            continue

                        # period: '2024-01' desde '2024-01-01'
                        period = row["indice_tiempo"][:7]

                        try:
                            cur = conn.execute(
                                """
                                INSERT OR IGNORE INTO trade_flows
                                    (commodity_id, ncm, period, flow_type, value_usd, source)
                                VALUES (?, ?, ?, 'export', ?, 'indec_datos_gob')
                                """,
                                (commodity_id, ncm_code, period, value_usd),
                            )
                            if cur.rowcount > 0:
                                inserted += 1
                                self._records_processed += 1
                            else:
                                skipped += 1
                                self._records_skipped += 1
                        except Exception as exc:
                            self.log(f"  DB error {commodity_id}/cap{ncm_code}/{period}: {exc}")

                    self.log(
                        f"  {commodity_id} cap{ncm_code}: "
                        f"{inserted} insertados, {skipped} duplicados"
                    )

            conn.commit()
            self.log(
                f"Comex completo: {self._records_processed} nuevos, "
                f"{self._records_skipped} duplicados"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline Comex Pisubí")
    parser.add_argument("--months", type=int, default=24,
                        help="Últimos N meses a procesar (default: 24)")
    parser.add_argument("--all", dest="all_data", action="store_true",
                        help="Procesar serie completa desde 1990")
    args = parser.parse_args()

    pl = ComexPipeline()
    with pl.run_context():
        pl.run(months=None if args.all_data else args.months)
