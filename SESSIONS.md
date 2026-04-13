# Pisubí / Comm-Track — Session Tracker

Al iniciar una nueva sesión, leé este archivo. El header dice en qué sesión estás y qué hacer primero.

---

## ESTADO ACTUAL: Sesión 14 — COMPLETADA (continuar en Sesión 15)

**Fecha:** 2026-04-13
**Deploy:** Backend en Render (`render.yaml` + `startup.sh`), Frontend en GitHub Pages
**Repo:** https://github.com/auparrino/comm-track

---

## PENDIENTE PARA SESIÓN 15

### Prioridad alta

**#1 — Datos 2024 near-zero en TradeFlowChart (Render)**
- Soja, oro, gas, litio muestran valores ~0 para 2024 en producción. Trigo muestra bien.
- Datos existen en DB local y la API local los devuelve bien (verificado).
- Causa probable: la DB de Render no tiene los datos de `comex_indec.py` (ZIPs locales no van a Render).
- Solución: implementar `comex_comtrade.py` que use UN Comtrade API para datos bilaterales anuales.
  - Endpoint público sin key: `https://comtradeapi.un.org/public/v1/preview/C/A/HS?reporterCode=32&period=2023&flowCode=X&cmdCode=12&includeDesc=true`
  - Argentina = reporterCode 32, hasta 500 req/día sin key.
  - Alternativa: subir la DB local a Render manualmente via Render Shell.

**#10 — Precios históricos desde más atrás**
- `prices.py`: agregar flag `--full-history` que use `start="1990-01-01"` en yfinance.
- Nuevo pipeline `worldbank_prices.py` (World Bank Pink Sheet mensual desde ~1960).
- `PriceChart.tsx`: agregar selector de rango 1A / 5A / 10A / Máx.

### Ya resuelto localmente, pendiente de deploy
- Bug #2 (imports solo Brasil): UNIQUE index corregido, datos locales OK con 73 países.
- `comex_indec.py`: ZIPs 2020-2026 procesados, 23,882 registros bilaterales.
- Estos cambios están en `master`. Render re-deploya en el próximo push.

### Roadmap completo de sesiones 15–24
Ver archivo `MEJORAS.md` (fases A–G con detalle de cada feature).

---

## RESUMEN DEL PROYECTO

Monitor de commodities de Argentina (litio, oro, soja, trigo, maíz, cobre, gas natural).

- **Backend:** Python + FastAPI + SQLite (`backend/db/commodity_monitor.db`)
- **Pipelines:** precios (yfinance), noticias (RSS + LLM Groq/Cerebras/Mistral), comex (INDEC ZIPs + datos.gob.ar), variables macro (ENSO, TC, DXY, retenciones)
- **Frontend:** React + TypeScript + Recharts
- **Deploy:** Render (backend), GitHub Pages (frontend, CI automático en push)
- **LLM:** Groq → Cerebras → Mistral (rotación con fallback, NO Anthropic API)

---

## LOG DE SESIONES

### Sesión 14 — 2026-04-13
**Completado:**
- Commit baseline de sesión 13
- ZIPs INDEC movidos de root a `data/comex_indec/` (ignorado por .gitignore — local only)
- `comex_indec.py`: COMEX_DIR ahora relativo (`data/comex_indec/`), YEAR_FILES extendido a 2020–2026 con `_year_entry()` genérico
- Fix bug #2 importaciones: `idx_trade_unique` corregido con `COALESCE(country_origin,'')` en schema.sql y DB local (DROP + recrear + borrar 88 registros malos)
- `_insert_aggregates` extendido para cubrir imports además de exports
- Pipeline corrido completo: 23,882 nuevos registros, 342 periodos export + 631 periodos import (2020-01 → 2026-02)
- Verificación: soja 2024 importaciones muestra 73 países (Paraguay $2710M, Uruguay $200M, Brasil $65M...)

**Notas:**
- Los ZIPs locales están en `data/comex_indec/` — no van al repo (`.gitignore`). Para replicar en otra máquina, descargar ZIPs de INDEC manualmente.
- El fix del UNIQUE index solo está aplicado en la DB local. La DB de Render se recrea con `startup.sh` en cada deploy (usa `init_db.py` + pipelines) — automáticamente tendrá el index correcto.
- La DB de Render no tendrá datos de `comex_indec.py` (ZIPs locales). Ver #1 en pendientes.

---

### Sesión 13 — 2026-04-12
**Completado:**
- `backend/pipelines/comex_indec.py`: nuevo pipeline que lee ZIPs locales INDEC (mensuales, NCM 8 dígitos) y genera registros bilaterales + agregados `indec_local_agg`
- `backend/api/routes/trade.py`: filtro `flow_type='export'` + `country IS NULL` en endpoint `/trade-flows/`
- `backend/db/schema.sql`: UNIQUE index en `companies(commodity_id, name)` para evitar duplicados en re-runs de init_db
- `backend/pipelines/variables.py`: retenciones actualizadas Decreto 877/2025
- `frontend/src/components/PriceChart.tsx`, `TradePartnersChart.tsx`: ajustes visuales

**Notas:**
- `comex_indec.py` inicialmente solo cubría 2024-2026 y solo exports. Sesión 14 lo extendió.

---

### Sesión 12 — 2026-04-12
**Completado:**
- Nuevos commodities: maíz (ZC=F)
- Fix ticker cobre: HG=F (antes CU=F — no existe en yfinance)
- `comex_bilateral.py`: socios comerciales bilaterales desde comex-IED/products.json
- `TradePartnersChart.tsx`: rediseño con toggle export/import y selector de año
- `ImpactRadar`: tendencias (flechas ↑↓) para variables con histórico
- Fix varios bugs UI en gráficos de exportaciones

---

### Sesión 11 — 2026-04-12
**Completado:**
- Deploy backend en **Render** (free tier): `render.yaml` + `startup.sh`
- `startup.sh`: init DB + todos los pipelines al arrancar el servicio
- Rename proyecto: "Pisubí" → "Comm-Track" en header, API title, frontend
- Dockerfile actualizado para usar `startup.sh` como CMD

**Notas:**
- Backend URL en Render: configurar `VITE_API_URL` en GitHub repo vars → CI re-deploya frontend
- La DB de Render se recrea en cada deploy (SQLite sin persistencia). Pipelines corren en startup.

---

### Sesión 10 — 2026-04-12
**Completado:**
- Repo GitHub creado: https://github.com/auparrino/comm-track
- `.gitignore`: excluye `.env`, `*.db`, `node_modules`, `dist`, `data/`
- `frontend/package.json`: homepage, scripts `build:ghpages` + deploy, devDeps gh-pages
- `vite.config.ts`: `base=/comm-track/` cuando `DEPLOY_TARGET=ghpages`
- `api.ts`: `VITE_API_URL` env var para backend prod
- `.github/workflows/deploy-frontend.yml`: CI auto-deploy en push a master
- Build + deploy a GitHub Pages: https://auparrino.github.io/comm-track/

---

### Sesión 9 — 2026-04-12
**Completado:**
- Fix crítico: `config.py` no llamaba `load_dotenv()` → API keys nunca se cargaban
- `YahooMacroPipeline`: reemplaza `BCRAPipeline` (API BCRA v3.0 deprecada 2025). Fuentes: `USDARS=X` (TC), `DX-Y.NYB` (DXY), `^IRX` (Fed proxy)
- `FREDPipeline`: conservado, se omite si `FRED_API_KEY` vacío
- Fix feeds RSS copper: `copper-price/feed` → 200
- `news.py`: commodities reconocidos extendido a 6 (copper, natgas, wheat)
- Reclasificación LLM completa (57 artículos), alertas y resúmenes re-generados para los 6 commodities

---

### Sesión 8 — 2026-04-12
**Completado:**
- Nuevos commodities: cobre (`HG=F`), gas natural (`NG=F`), trigo (`ZW=F`)
- `init_db.py`: seed 13 empresas nuevas (FCX, SCCO, YPF, TTE, PAM...)
- `comex.py`: NCM map cap.74 / cap.27 / cap.10
- `variables.py`: retenciones cobre 3%, gas 0%, trigo 12%
- Fix crítico variables API: `NULL = NULL` en SQL → ENSO nunca aparecía. Fix con subquery correlacionada.
- `theme.ts`: colores copper/natgas/wheat

---

### Sesiones 1–7 — 2026-04-12
Ver historial git (`git log --oneline`) para detalle. Resumen:
- S1: estructura, schema, init_db, prices pipeline
- S2: API FastAPI (5 endpoints), frontend básico (CommodityCard, PriceChart, CompanyValuationPanel)
- S3: news scraper RSS + LLM classifier, NewsPanel
- S4: rediseño estético editorial (crema/navy), fix asignación commodity LLM
- S5: pipeline comex.py (datos.gob.ar NCM 2 dígitos), TradeFlowChart, feeds RSS actualizados
- S6: variables pipeline (ENSO NOAA, retenciones), ImpactRadar, mobile responsive
- S7: summary.py (LLM semanal), alerts.py, comex_bilateral.py, TradePartnersChart, Dockerfile

---

## ARCHIVOS CLAVE

```
backend/
  api/routes/trade.py          ← endpoints /trade-flows/, /partners
  db/schema.sql                ← schema completo (UNIQUE index trade_flows corregido en s14)
  db/init_db.py                ← seed de commodities, empresas, init schema
  pipelines/
    comex_indec.py             ← ZIPs INDEC locales (data/comex_indec/, 2020-2026)
    comex.py                   ← datos.gob.ar NCM mensual (funciona en Render)
    comex_bilateral.py         ← comex-IED anual (funciona en Render)
    prices.py                  ← yfinance commodities + empresas
    news.py                    ← RSS + LLM classifier (Groq/Cerebras/Mistral)
    variables.py               ← ENSO, retenciones, macro
    summary.py                 ← resumen semanal LLM
    alerts.py                  ← alertas de señales

frontend/src/components/
  TradeFlowChart.tsx           ← barras apiladas exportaciones mensuales
  TradePartnersChart.tsx       ← socios bilaterales top-10
  PriceChart.tsx               ← precio histórico con rangos
  NewsPanel.tsx                ← noticias + resumen IA integrado
  CompanyValuationPanel.tsx    ← empresas con Δ1S y badge de rol
  ImpactRadar.tsx              ← variables macro (ENSO, TC, DXY, retenciones)

render.yaml                    ← config deploy Render
startup.sh                     ← init DB + pipelines al iniciar en Render
data/comex_indec/              ← ZIPs INDEC locales (ignorados por .gitignore)
MEJORAS.md                     ← roadmap completo fases A–G (sesiones 15–24)
```

---

## NOTAS TÉCNICAS

- **LLM:** Groq → Cerebras → Mistral. Lógica en `backend/pipelines/llm_client.py`. NO usar Anthropic API.
- **SQLite en Render:** la DB se recrea en cada deploy. `startup.sh` corre `init_db.py` + todos los pipelines. Datos persisten solo mientras el servicio está vivo.
- **ZIPs INDEC:** locales en `data/comex_indec/`, no van al repo. `comex.py` (datos.gob.ar) sí funciona en Render para datos históricos hasta ~Feb 2025.
- **Backend puerto:** 8000. `vite.config.ts` proxy apunta a 8000.
- **UNIQUE index trade_flows:** corregido en s14 — incluye `COALESCE(country_origin,'')` y `COALESCE(country_dest,'')`.
- **Tickers problemáticos:** ALTM (Arcadium, delistado 2025), PLL (Piedmont, delistado) → ticker=NULL en DB.
