#!/bin/bash
# Comm-Track — startup script para Render
# Inicializa DB y corre pipelines de datos antes de levantar el servidor

set -e

echo "[startup] Inicializando base de datos..."
python -m backend.db.init_db

echo "[startup] Descargando precios (90 días)..."
python -m backend.pipelines.prices --days 90 || echo "[startup] prices: error parcial, continuando"

echo "[startup] Descargando variables macro y ENSO..."
python -m backend.pipelines.variables || echo "[startup] variables: error parcial, continuando"

echo "[startup] Descargando exportaciones INDEC (36 meses)..."
python -m backend.pipelines.comex --months 36 || echo "[startup] comex: error parcial, continuando"

echo "[startup] Descargando comercio bilateral..."
python -m backend.pipelines.comex_bilateral || echo "[startup] comex_bilateral: error parcial, continuando"

echo "[startup] Procesando datos INDEC mensuales (ZIPs bilaterales 2020-2026)..."
python -m backend.pipelines.comex_indec || echo "[startup] comex_indec: error parcial, continuando"

echo "[startup] Descargando noticias y clasificando con LLM..."
python -m backend.pipelines.news || echo "[startup] news: error parcial, continuando"

echo "[startup] Generando resúmenes semanales..."
python -m backend.pipelines.summary || echo "[startup] summary: error parcial, continuando"

echo "[startup] Generando alertas..."
python -m backend.pipelines.alerts || echo "[startup] alerts: error parcial, continuando"

echo "[startup] Listo. Levantando servidor..."
exec uvicorn backend.api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
