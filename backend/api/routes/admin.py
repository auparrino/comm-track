"""
Pisubí — Rutas de administración de pipelines
GET  /admin/pipelines              → estado de cada pipeline (último run, registros, errores)
POST /admin/pipelines/{name}/run   → dispara un pipeline en background
"""
import sqlite3
from fastapi import APIRouter, BackgroundTasks, HTTPException

from backend.config import DB_PATH

router = APIRouter()

# Pipelines expuestos con su descripción
PIPELINE_REGISTRY: dict[str, str] = {
    "prices":           "Yahoo Finance (commodities + empresas + macro: TC, DXY, Fed Rate)",
    "news":             "RSS feeds + clasificación LLM",
    "summary":          "Resumen semanal LLM por commodity",
    "alerts":           "Detección de alertas de alto impacto",
    "variables":        "ENSO (NOAA) + retenciones AR",
    "comex":            "Exportaciones INDEC (NCM mensual)",
    "comex_bilateral":  "Comercio bilateral anual (comex-IED)",
}


@router.get("/pipelines")
def list_pipelines():
    """
    Retorna estado del último run de cada pipeline conocido.
    Pipelines que nunca corrieron aparecen con status='never_run'.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT
            pipeline_name,
            MAX(started_at)    AS last_run,
            status,
            records_processed,
            records_skipped,
            error_message,
            finished_at
        FROM pipeline_runs
        GROUP BY pipeline_name
        ORDER BY pipeline_name
    """).fetchall()
    conn.close()

    result = {r["pipeline_name"]: dict(r) for r in rows}

    # Incluir pipelines conocidos que nunca corrieron
    for name in PIPELINE_REGISTRY:
        if name not in result:
            result[name] = {
                "pipeline_name":     name,
                "last_run":          None,
                "status":            "never_run",
                "records_processed": 0,
                "records_skipped":   0,
                "error_message":     None,
                "finished_at":       None,
            }

    # Enriquecer con descripción y ordenar
    output = []
    for name in sorted(PIPELINE_REGISTRY):
        entry = result.get(name, {})
        entry["description"] = PIPELINE_REGISTRY[name]
        output.append(entry)

    return output


@router.post("/pipelines/{name}/run")
def trigger_pipeline(name: str, background_tasks: BackgroundTasks):
    """Dispara un pipeline en background. Retorna inmediatamente."""
    if name not in PIPELINE_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Pipeline '{name}' no encontrado")
    background_tasks.add_task(_run_pipeline, name)
    return {"status": "triggered", "pipeline": name}


# ──────────────────────────────────────────────
# Runner interno (ejecutado en background thread)
# ──────────────────────────────────────────────

def _run_pipeline(name: str) -> None:
    if name == "prices":
        from backend.pipelines.prices import run_all
        run_all()

    elif name == "news":
        from backend.pipelines.news import NewsPipeline
        pl = NewsPipeline()
        with pl.run_context():
            pl.run()

    elif name == "summary":
        from backend.pipelines.summary import SummaryPipeline
        pl = SummaryPipeline()
        with pl.run_context():
            pl.run()

    elif name == "alerts":
        from backend.pipelines.alerts import AlertsPipeline
        pl = AlertsPipeline()
        with pl.run_context():
            pl.run()

    elif name == "variables":
        from backend.pipelines.variables import run_all
        run_all()

    elif name == "comex":
        from backend.pipelines.comex import ComexPipeline
        pl = ComexPipeline()
        with pl.run_context():
            pl.run()

    elif name == "comex_bilateral":
        from backend.pipelines.comex_bilateral import ComexBilateralPipeline
        pl = ComexBilateralPipeline()
        with pl.run_context():
            pl.run()
