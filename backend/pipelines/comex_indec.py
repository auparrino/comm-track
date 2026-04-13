"""
Comm-Track — Pipeline Comex INDEC Local (datos mensuales bilaterales)
Fuente: archivos zip de INDEC con datos mensuales por NCM 8 dígitos y país.
        exports_YYYY_M.zip  →  exponmYY.csv  (exportaciones mensuales)
        imports_YYYY_M.zip  →  impomYY.csv   (importaciones mensuales)
        Países.csv          →  mapa código → nombre de país

Ventajas sobre comex_bilateral.py (products.json anual):
  - Datos MENSUALES (no anuales) → pueden mostrarse en TradeFlowChart
  - Distinción maíz (1005) vs trigo (1001) al nivel NCM 4 dígitos
  - Datos hasta 2026-02

Uso:
  python -m backend.pipelines.comex_indec
  python -m backend.pipelines.comex_indec --flow exports
  python -m backend.pipelines.comex_indec --years 2024 2025 2026
"""
import sys
import re
import csv
import zipfile
import argparse
import io
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.pipelines.base_pipeline import BasePipeline

# ─── Rutas a los archivos locales ────────────────────────────────────────────

COMEX_DIR = Path("C:/Users/augus/OneDrive/Documentos/Comex")

PAISES_CSV = COMEX_DIR / "Países.csv"

# exports_YYYY_M.zip → exponmYY.csv
# imports_YYYY_M.zip → impomYY.csv
YEAR_FILES = {
    2024: {
        "exports": (COMEX_DIR / "exports_2024_M.zip", "exponm24.csv"),
        "imports": (COMEX_DIR / "imports_2024_M.zip", "impom24.csv"),
    },
    2025: {
        "exports": (COMEX_DIR / "exports_2025_M.zip", "exponm25.csv"),
        "imports": (COMEX_DIR / "imports_2025_M.zip", "impom25.csv"),
    },
    2026: {
        "exports": (COMEX_DIR / "exports_2026_M.zip", "exponm26.csv"),
        "imports": (COMEX_DIR / "imports_2026_M.zip", "impom26.csv"),
    },
}

# ─── Mapeo NCM → commodity ────────────────────────────────────────────────────
# Primero se intenta el prefijo de 4 dígitos, luego el de 2.
# El ncm que se guarda en la DB es el prefijo normalizado.

NCM_4D: dict[str, tuple[str, str]] = {
    "1001": ("wheat",   "1001"),   # Trigo y morcajo (tranquillón)
    "1005": ("corn",    "1005"),   # Maíz
    "1006": ("corn",    "1006"),   # Arroz — bonus
}

NCM_2D: dict[str, tuple[str, str]] = {
    "12": ("soy",     "12"),
    "15": ("soy",     "15"),
    "23": ("soy",     "23"),
    "27": ("natgas",  "27"),
    "28": ("lithium", "28"),
    "71": ("gold",    "71"),
    "74": ("copper",  "74"),
}

SOURCE_NAME = "indec_local"


# ─── Pipeline ────────────────────────────────────────────────────────────────

class ComexIndecPipeline(BasePipeline):

    def __init__(self):
        super().__init__("comex_indec")

    def _load_countries(self) -> dict[str, str]:
        """Lee Países.csv → {código_id: nombre}"""
        if not PAISES_CSV.exists():
            self.log(f"  Países.csv no encontrado en {COMEX_DIR}")
            return {}
        countries: dict[str, str] = {}
        with open(PAISES_CSV, encoding="latin1", newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                _id  = str(row.get("_id", "")).strip()
                name = str(row.get("nombre", row.get("Nombre", ""))).strip()
                if _id and name:
                    countries[_id] = name
        self.log(f"  {len(countries)} países cargados")
        return countries

    @staticmethod
    def _parse_float(s: str) -> float | None:
        """Convierte '1.234.567,89' o '1234567,89' a float. Retorna None si es 's', 's1'..."""
        s = s.strip()
        if not s or re.match(r"^s\d*$", s, re.IGNORECASE):
            return None
        s = s.replace(".", "").replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return None

    @staticmethod
    def _ncm_lookup(ncm: str) -> tuple[str, str] | None:
        """Retorna (commodity_id, ncm_key) o None si no aplica."""
        prefix4 = ncm[:4]
        if prefix4 in NCM_4D:
            return NCM_4D[prefix4]
        prefix2 = ncm[:2]
        if prefix2 in NCM_2D:
            return NCM_2D[prefix2]
        return None

    def _process_zip(
        self,
        zip_path: Path,
        csv_name: str,
        flow_type: str,       # 'export' | 'import'
        countries: dict[str, str],
        conn,
    ) -> None:
        if not zip_path.exists():
            self.log(f"  Archivo no encontrado: {zip_path.name}")
            return

        with zipfile.ZipFile(zip_path) as z:
            try:
                with z.open(csv_name) as f:
                    raw = f.read().decode("latin1")
            except KeyError:
                self.log(f"  {csv_name} no encontrado en {zip_path.name}")
                return

        reader = csv.DictReader(io.StringIO(raw), delimiter=";")
        # Normalizar nombres de columnas (tildes, mayúsculas)
        rows = list(reader)
        if not rows:
            return

        # Detectar nombres de columnas flexiblemente
        sample = rows[0]
        col_year  = next((k for k in sample if "o" in k.lower()), None)
        col_month = next((k for k in sample if "mes" in k.lower()), None)
        col_ncm   = next((k for k in sample if "ncm" in k.lower()), None)
        col_country = next((k for k in sample if "pdes" in k.lower() or "porg" in k.lower()), None)
        col_fob   = next((k for k in sample if "fob" in k.lower()), None)
        col_peso  = next((k for k in sample if "pnet" in k.lower()), None)

        if not all([col_year, col_month, col_ncm, col_fob]):
            self.log(f"  Columnas no detectadas en {csv_name}: {list(sample.keys())}")
            return

        country_key = "country_dest" if flow_type == "export" else "country_origin"

        for row in rows:
            ncm_raw  = str(row.get(col_ncm, "")).strip()
            lookup   = self._ncm_lookup(ncm_raw)
            if lookup is None:
                continue

            commodity_id, ncm_key = lookup
            fob = self._parse_float(str(row.get(col_fob, "")))
            if fob is None or fob <= 0:
                continue

            peso  = self._parse_float(str(row.get(col_peso, "") or ""))
            year  = str(row.get(col_year, "")).strip()
            month = str(row.get(col_month, "")).strip().zfill(2)
            period = f"{year}-{month}"

            country_code   = str(row.get(col_country, "")).strip() if col_country else ""
            country_name   = countries.get(country_code, country_code) if country_code else None

            try:
                if country_key == "country_dest":
                    cur = conn.execute(
                        """
                        INSERT OR IGNORE INTO trade_flows
                            (commodity_id, ncm, period, flow_type,
                             country_dest, value_usd, weight_kg, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (commodity_id, ncm_key, period, flow_type,
                         country_name, fob, peso, SOURCE_NAME),
                    )
                else:
                    cur = conn.execute(
                        """
                        INSERT OR IGNORE INTO trade_flows
                            (commodity_id, ncm, period, flow_type,
                             country_origin, value_usd, weight_kg, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (commodity_id, ncm_key, period, flow_type,
                         country_name, fob, peso, SOURCE_NAME),
                    )
                if cur.rowcount > 0:
                    self._records_processed += 1
                else:
                    self._records_skipped += 1
            except Exception as exc:
                self.log(f"  DB error {commodity_id}/{ncm_key}/{period}: {exc}")

    def _insert_aggregates(self, conn) -> int:
        """
        A partir de los registros bilaterales (indec_local), genera e inserta
        totales agregados (country_dest/origin = NULL) con source='indec_local_agg'.

        Los NCM de 4 dígitos (ej: 1005 maíz, 1001 trigo) se normalizan a 2 dígitos
        (→ '10') para ser compatibles con el gráfico TradeFlowChart.

        Usa INSERT OR IGNORE: si ya existe un agregado para ese periodo desde otra
        fuente (p.ej. indec_datos_gob), se conserva el existente (no se duplica).

        Retorna la cantidad de nuevos agregados insertados.
        """
        # Borrar agregados previos para regenerar (evita NCMs stale de 4 dígitos)
        conn.execute("DELETE FROM trade_flows WHERE source='indec_local_agg'")

        cur = conn.execute("""
            INSERT OR IGNORE INTO trade_flows
                (commodity_id, ncm, period, flow_type,
                 country_dest, country_origin, value_usd, weight_kg, source)
            SELECT
                commodity_id,
                -- Normalizar NCM de 4+ dígitos a 2 dígitos (1005→10, 1001→10)
                CASE WHEN LENGTH(ncm) >= 4 THEN SUBSTR(ncm, 1, 2) ELSE ncm END AS ncm,
                period,
                flow_type,
                NULL  AS country_dest,
                NULL  AS country_origin,
                SUM(value_usd)   AS value_usd,
                SUM(weight_kg)   AS weight_kg,
                'indec_local_agg' AS source
            FROM trade_flows
            WHERE source = 'indec_local'
              AND flow_type = 'export'       -- solo exportaciones (chart "Exportaciones AR")
              AND country_dest IS NOT NULL    -- solo registros bilaterales con destino conocido
            GROUP BY commodity_id,
                     CASE WHEN LENGTH(ncm) >= 4 THEN SUBSTR(ncm, 1, 2) ELSE ncm END,
                     period, flow_type
        """)
        conn.commit()
        return cur.rowcount

    def run(
        self,
        years: list[int] | None = None,
        flows: list[str] | None = None,
    ) -> None:
        years = years or list(YEAR_FILES.keys())
        flows = flows or ["exports", "imports"]

        if not COMEX_DIR.exists():
            self.log(f"Directorio no encontrado: {COMEX_DIR}")
            return

        countries = self._load_countries()
        self.log(f"Procesando años {years}, flujos {flows}")

        with self.get_conn() as conn:
            for year in years:
                year_cfg = YEAR_FILES.get(year)
                if not year_cfg:
                    self.log(f"  Año {year} no configurado")
                    continue

                for flow in flows:
                    if flow not in year_cfg:
                        continue
                    zip_path, csv_name = year_cfg[flow]
                    flow_type = "export" if flow == "exports" else "import"
                    self.log(f"  {year} {flow}: {zip_path.name}/{csv_name}")
                    self._process_zip(zip_path, csv_name, flow_type, countries, conn)
                    conn.commit()
                    self.log(
                        f"    {self._records_processed} nuevos, "
                        f"{self._records_skipped} duplicados (acumulado)"
                    )

            # Generar totales agregados para el gráfico mensual
            self.log("Generando agregados mensuales (indec_local_agg)...")
            n_agg = self._insert_aggregates(conn)
            self.log(f"  {n_agg} nuevos periodos agregados insertados")

        self.log(
            f"Comex INDEC local completo: {self._records_processed} nuevos, "
            f"{self._records_skipped} duplicados"
        )


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline Comex INDEC local")
    parser.add_argument("--years", nargs="+", type=int, default=None,
                        help="Años a procesar (default: todos)")
    parser.add_argument("--flow", choices=["exports", "imports", "all"], default="all",
                        help="Flujo a procesar (default: all)")
    args = parser.parse_args()

    flows = ["exports", "imports"] if args.flow == "all" else [args.flow]

    pl = ComexIndecPipeline()
    with pl.run_context():
        pl.run(years=args.years, flows=flows)
