"""
Pisubí — Pipeline de Variables de Impacto
Fuentes:
  - NOAA ONI (Oceanic Niño Index): ENSO indicator, mensual
  - Retenciones AR: estáticas, actualizadas manualmente por decreto

Nota: Fed Funds Rate, CPI y DXY ya se cargan en prices.py (FREDPipeline)
      y se guardan en impact_variables. Este pipeline complementa con
      variables que FRED no cubre.

Uso:
  python -m backend.pipelines.variables [--days 730]
  python -m backend.pipelines.variables --pipeline enso
  python -m backend.pipelines.variables --pipeline retenciones
"""
import sys
import argparse
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.pipelines.base_pipeline import BasePipeline


# ─────────────────────────────────────────────────────────────────────────────
# 1. ENSO — NOAA Oceanic Niño Index (ONI)
# ─────────────────────────────────────────────────────────────────────────────

class ENSOPipeline(BasePipeline):
    """
    Descarga el índice ONI (Oceanic Niño Index) desde NOAA CPC.

    El ONI mide la anomalía de temperatura superficial del mar en la región
    Niño 3.4 del Pacífico tropical, promediada en ventanas de 3 meses.

    Interpretación:
      > +0.5  →  El Niño (calor)  →  sequía en Cono Sur → bearish soja
      < -0.5  →  La Niña (frío)   →  lluvias/inundaciones AR → bullish soja
      ±0.5    →  Neutro

    Fuente: https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt
    Guardado con commodity_id=NULL (global; el frontend filtra por relevancia).
    """

    ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"

    # Temporada de 3 meses → mes central (para asignar fecha en DB)
    SEAS_TO_MONTH = {
        "DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4,
        "AMJ": 5, "MJJ": 6, "JJA": 7, "JAS": 8,
        "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12,
    }

    def __init__(self):
        super().__init__("enso")

    def run(self, days: int = 730) -> None:
        self.log("Descargando NOAA ONI index...")
        try:
            resp = requests.get(self.ONI_URL, timeout=20)
            resp.raise_for_status()
            text = resp.text
        except requests.RequestException as exc:
            self.log(f"Error descargando ONI: {exc}")
            return

        with self.get_conn() as conn:
            for line in text.splitlines():
                line = line.strip()
                # Saltar cabecera y líneas vacías
                if not line or not line[0].isalpha() or line.startswith("SEAS"):
                    continue
                parts = line.split()
                if len(parts) < 4:
                    continue
                try:
                    seas = parts[0]
                    yr   = int(parts[1])
                    anom = float(parts[3])   # columna ANOM (índice 3: SEAS YR TOTAL ANOM)
                except (ValueError, IndexError):
                    continue

                month = self.SEAS_TO_MONTH.get(seas)
                if month is None:
                    continue

                date_str = f"{yr}-{month:02d}-01"

                try:
                    # Usamos INSERT OR REPLACE manual para NULL commodity_id
                    # (UNIQUE constraint no previene duplicados con NULL en SQLite)
                    existing = conn.execute(
                        "SELECT id FROM impact_variables WHERE commodity_id IS NULL AND variable_name='enso_oni' AND date=?",
                        (date_str,)
                    ).fetchone()
                    if existing is None:
                        conn.execute("""
                            INSERT INTO impact_variables
                                (commodity_id, variable_name, date, value, source, unit)
                            VALUES (NULL, 'enso_oni', ?, ?, 'noaa_cpc', 'anomalía °C')
                        """, (date_str, anom))
                        self._records_processed += 1
                    else:
                        self._records_skipped += 1
                except Exception:
                    self._records_skipped += 1

            conn.commit()

        self.log(f"ENSO ONI: {self._records_processed} nuevos, {self._records_skipped} ya existían")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Retenciones AR — derechos de exportación vigentes
# ─────────────────────────────────────────────────────────────────────────────

class RetencionesPipeline(BasePipeline):
    """
    Inserta los derechos de exportación vigentes en Argentina.
    Los datos son semi-estáticos (cambian por decreto) y se mantienen
    manualmente en esta tabla.

    Fuente: AFIP/ARCA, decretos del Poder Ejecutivo Nacional.
    Para actualizar: modificar la lista RETENCIONES y re-correr el pipeline.
    """

    # (commodity_id, variable_name, fecha_vigencia, valor_pct, nota_decreto)
    # Valores históricos + vigentes a abril 2026 (Decreto 877/2025)
    RETENCIONES: list[tuple] = [
        # ── Soja ──────────────────────────────────────────────────────────────
        ("soy",     "retenciones_soja",    "2020-09-01", 33.0,
         "Decreto 230/2020 – porotos de soja 33% (histórico)"),
        ("soy",     "retenciones_soja",    "2025-01-27", 26.0,
         "Decreto 38/2025 – soja 26% temporal (ene-jun 2025)"),
        ("soy",     "retenciones_soja",    "2025-12-12", 24.0,
         "Decreto 877/2025 – soja 24% permanente (vigente abr 2026)"),

        # ── Oro ───────────────────────────────────────────────────────────────
        ("gold",    "retenciones_oro",     "2022-01-01", 12.0,
         "Res. 61/2022 – oro en bruto/semielaborado 12% (histórico)"),
        ("gold",    "retenciones_oro",     "2025-08-01",  0.0,
         "Decreto 563/2025 – oro 0% permanente. Minería no ferrosa exenta."),

        # ── Litio ─────────────────────────────────────────────────────────────
        ("lithium", "retenciones_litio",   "2023-06-01",  4.5,
         "Decreto 206/2023 / vigente – carbonato/hidróxido litio 4,5% (sin cambios bajo Milei)"),

        # ── Cobre ─────────────────────────────────────────────────────────────
        ("copper",  "retenciones_cobre",   "2021-01-01",  3.0,
         "Res. Gral. ARCA – cobre cap.74, 3% (histórico)"),
        ("copper",  "retenciones_cobre",   "2025-08-01",  0.0,
         "Decreto 563/2025 – cobre y metales no ferrosos 0% permanente."),

        # ── Gas Natural ───────────────────────────────────────────────────────
        ("natgas",  "retenciones_gas",     "2013-07-01",  0.0,
         "Decreto 929/2013 – gas exportado, DEX suspendidos para Vaca Muerta (histórico)"),
        ("natgas",  "retenciones_gas",     "2024-01-01",  8.0,
         "Vigente abr 2026: gas natural 8% fija (hidrocarburos no convencionales, Vaca Muerta)"),

        # ── Trigo ─────────────────────────────────────────────────────────────
        ("wheat",   "retenciones_trigo",   "2020-09-01", 12.0,
         "Decreto 230/2020 – trigo 12% (histórico)"),
        ("wheat",   "retenciones_trigo",   "2025-01-27",  9.5,
         "Decreto 38/2025 – trigo 9,5% temporal (ene-jun 2025)"),
        ("wheat",   "retenciones_trigo",   "2025-12-12",  7.5,
         "Decreto 877/2025 – trigo 7,5% permanente (vigente abr 2026)"),

        # ── Maíz ──────────────────────────────────────────────────────────────
        ("corn",    "retenciones_maiz",    "2020-09-01", 12.0,
         "Decreto 230/2020 – maíz 12% (histórico)"),
        ("corn",    "retenciones_maiz",    "2025-01-27",  9.5,
         "Decreto 38/2025 – maíz 9,5% temporal (ene-jun 2025)"),
        ("corn",    "retenciones_maiz",    "2025-12-12",  8.5,
         "Decreto 877/2025 – maíz 8,5% permanente (vigente abr 2026)"),
    ]

    def __init__(self):
        super().__init__("retenciones")

    def run(self, days: int = 0) -> None:
        self.log("Insertando retenciones de exportación vigentes...")
        with self.get_conn() as conn:
            for commodity_id, var_name, since, pct, note in self.RETENCIONES:
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO impact_variables
                            (commodity_id, variable_name, date, value, value_text, source, unit)
                        VALUES (?, ?, ?, ?, ?, 'afip_decreto', '%')
                    """, (commodity_id, var_name, since, pct, note))
                    self._records_processed += 1
                except Exception:
                    self._records_skipped += 1
            conn.commit()

        self.log(f"Retenciones: {self._records_processed} insertadas, "
                 f"{self._records_skipped} ya existían")


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────

def run_all(days: int = 730) -> None:
    pipelines = [ENSOPipeline(), RetencionesPipeline()]
    for pl in pipelines:
        with pl.run_context():
            pl.run(days=days)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline variables de impacto Pisubí")
    parser.add_argument("--days", type=int, default=730,
                        help="Días de historia para ENSO (default: 730 ≈ 2 años)")
    parser.add_argument("--pipeline",
                        choices=["enso", "retenciones", "all"],
                        default="all",
                        help="Sub-pipeline a ejecutar (default: all)")
    args = parser.parse_args()

    if args.pipeline == "enso":
        pl = ENSOPipeline()
        with pl.run_context(): pl.run(args.days)
    elif args.pipeline == "retenciones":
        pl = RetencionesPipeline()
        with pl.run_context(): pl.run(args.days)
    else:
        run_all(args.days)
