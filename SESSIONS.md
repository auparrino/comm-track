# Pisubí — Session Tracker

Este archivo es el punto de entrada para cada sesión de desarrollo.
Al iniciar una sesión, leé este archivo para saber exactamente dónde continuar.

---

## ESTADO ACTUAL: Sesión 9 — COMPLETADA (continuar en Sesión 10)

**Fecha:** 2026-04-12
**Fase activa:** FASE 4
**Próxima sesión:** Sesión 10

---

## RESUMEN DEL PROYECTO

Monitor de commodities (litio, oro, soja) con:
- Backend: Python + FastAPI + SQLite
- Pipelines: precios (yfinance, BCRA, FRED), noticias (RSS + scraping), comercio (INDEC), variables
- IA: Cerebras / Mistral / Groq (rotación, no Anthropic)
- Frontend: React + TypeScript + Recharts
- Extra: valuación de empresas vinculadas a cada commodity (tickers bursátiles)

---

## CHECKLIST POR FASE

### FASE 1 — Fundación (Semanas 1-2)
- [x] Crear estructura de directorios
- [x] Schema SQLite (con tabla `company_valuations`)
- [x] Script init_db.py + seed de commodities/actores
- [x] Pipeline de precios: yfinance (commodities + acciones de empresas)
- [x] Pipeline de precios: BCRA
- [x] Pipeline de precios: FRED
- [x] API FastAPI: endpoints /prices /commodities /companies /impact-variables
- [x] Frontend: Dashboard con 3 CommodityCards
- [x] Frontend: PriceChart (recharts)
- [x] Frontend: CompanyValuationPanel

### FASE 2 — Inteligencia (Semanas 3-4)
- [x] Scraper RSS (Mining.com, Kitco, Ámbito, Bichos de Campo)
- [ ] Scraper sitios sin RSS
- [x] Clasificador de noticias (Groq/Mistral/Cerebras — rotación con fallback)
- [x] Frontend: NewsPanel con filtros
- [x] Pipeline Comex → trade_flows (datos.gob.ar NCM 2 dígitos, mensual)
- [x] Frontend: TradeFlowChart (barras apiladas por capítulo NCM)

### FASE 3 — Análisis (Semanas 5-6)
- [x] Pipeline variables: ENSO (NOAA ONI), retenciones AR (AFIP/decreto)
- [x] Frontend: ImpactRadar (panel de variables con cards)
- [ ] Frontend: SupplyChainGraph
- [ ] Resumen semanal automático (LLM)
- [ ] Alertas de señales de alto impacto
- [x] Mobile responsive (useIsMobile hook, grids adaptativos)
- [x] Resumen semanal automático (LLM, endpoint /summary, componente WeeklySummary)
- [x] Alertas de señales de alto impacto (pipeline alerts.py, endpoint /alerts, AlertBanner)
- [x] NCM bilateral desde comex-IED (pipeline comex_bilateral.py, endpoint /partners, TradePartnersChart)

### FASE 4 — Escalamiento (Semanas 7-8)
- [ ] Agregar: cobre, gas natural, trigo
- [x] Dockerfile + railway.toml + fly.toml (configurado, pendiente ejecutar)
- [ ] Deploy backend ejecutado (Railway/Fly.io)
- [ ] Deploy frontend (GitHub Pages / Vercel)
- [ ] Cron en producción
- [ ] Panel de admin para pipelines

---

### Sesión 3 — 2026-04-12
**Completado:**
- Instalación de deps Python (fastapi, etc.) y npm install del frontend
- .env con GROQ, CEREBRAS, MISTRAL keys (FRED vacío)
- Fix % variación en CommodityCards (filtro por price_type correcto por commodity)
- Fix gráfico vacío en PriceChart (mismo fix de price_type)
- Proxy de litio: LIT ETF (Global X Lithium) en config.py y prices.py
- Pipeline prices corrido con --days 90 (456 registros históricos)
- backend/pipelines/news.py: scraper RSS + clasificador LLM (feedparser + BeautifulSoup)
- backend/api/routes/news.py: GET /news/ con filtros (commodity, days, sentiment, signal)
- frontend/src/components/NewsPanel.tsx: panel con badges LLM, filtros, links a fuentes
- Dashboard: layout 2 columnas (empresas | noticias)
- Backend corriendo en puerto 8001 (proceso viejo en 8000 no se pudo matar)
- 46 noticias clasificadas con Groq

**Notas de Sesión 3:**
- mining.com es feed compartido entre lithium y gold → artículos se guardan bajo `lithium` (primera iteración). En próxima sesión: limpiar duplicados o cambiar lógica para asignar commodity por clasificación LLM
- Kitco RSS devuelve 404, Benchmark devuelve 403, Ámbito devuelve 403. Feeds activos: mining.com + bichosdecampo.com
- Backend corre en puerto 8001 (vite proxy apunta a 8001). Para próximas sesiones: matar proceso viejo en 8000 antes de arrancar
- PYTHONIOENCODING=utf-8 necesario en Windows para los logs del pipeline

**Pendiente para Sesión 4:**
- Arreglar asignación de commodity en noticias (usar clasificación LLM en vez de commodity del feed)
- Buscar feeds RSS alternativos para oro y soja que funcionen
- Pipeline Comex → trade_flows (INDEC)
- Frontend: TradeFlowMap

---

### Sesión 4 — 2026-04-12
**Completado:**
- Rediseño estético completo: light mode editorial (crema #FDF0D5 / navy #003049)
  - Paleta centralizada en frontend/src/utils/theme.ts
  - Dashboard, CommodityCard, PriceChart, CompanyValuationPanel, NewsPanel rediseñados
  - Estética consistente con auparrino.github.io/media-monitor y otros proyectos del usuario
  - Cards con borde izquierdo colored (3px), monospace para precios/tickers, header blanco
  - Range buttons con fondo pill (cream), activo = navy sólido
- Fix asignación de commodity en noticias:
  - news.py _classify_article: si el LLM devuelve un único commodity reconocido, actualiza commodity_id
  - Si hay múltiples → mantiene el original del feed
- RSS feeds actualizados en config.py:
  - Litio: mining.com/web-tag/lithium/feed/ + fallback general
  - Oro: mining.com/web-tag/gold/feed/ + precious-metals tag
  - Soja: bichosdecampo.com (✓) + agrositio.com.ar (por verificar)

**Notas de Sesión 4:**
- Tag feeds de mining.com (WordPress) más específicos que feed general — verificar en sesión 5
- agrositio.com.ar/feed/ no verificado, puede dar 403; si falla, remover
- Reclasificación retroactiva de noticias ya guardadas: pendiente flag --reclassify en news.py

**Pendiente para Sesión 5:**
- Pipeline Comex → trade_flows (INDEC API / archivos CSV)
- Frontend: TradeFlowMap (mapa o treemap de flujos por NCM)
- Flag --reclassify en news.py para re-procesar noticias existentes
- Verificar nuevos feeds RSS

---

### Sesión 5 — 2026-04-12
**Completado:**
- Tema: `surface` bajado a `#FEF9F0` (blanco cálido, menos contraste vs fondo crema)
- Feeds RSS verificados: mining.com/web-tag/gold/feed/ → 404 (reemplazado por gold-price/feed/)
  mining.com/web-tag/precious-metals/feed/ → 404 (removido); agrositio.com.ar → 404 (removido)
- Diarios económicos AR agregados como `AR_ECONOMIC_FEEDS` en config.py:
  Ámbito Financiero ✓, El Cronista ✓, iProfesional ✓
  (Infobae 404, LaNacion 404)
- Feeds soja mejorados: + El Cronista agro-negocios ✓, Agrofy ✓, Infobae agro ✓
- news.py: soporte para AR_ECONOMIC_FEEDS (commodity_id=None, LLM asigna)
- news.py: flag --reclassify [--all] para re-clasificar artículos existentes
- Pipeline comex.py: descarga datos.gob.ar NCM 2 dígitos mensual (1990-2025-02)
  Litio: cap.28 (químicos inorgánicos), Oro: cap.71 (metales preciosos),
  Soja: cap.12 + 15 + 23 (semillas + aceites + harinas)
  180 registros insertados (36 meses × 5 series)
- API: GET /trade-flows/ y GET /trade-flows/summary en main.py
- Frontend: TradeFlowChart.tsx — barras apiladas, range 12/24/36M
  Integrado en Dashboard al lado del PriceChart (layout 2 columnas)
- TypeScript: tsc --noEmit sin errores

**Notas de Sesión 5:**
- Pipeline comex corre en < 1 seg (todo el procesamiento es local tras descarga)
- Datos INDEC tienen ~30 días de lag (último dato disponible: 2025-02)
- cap.28 incluye TODOS los químicos inorgánicos, no solo litio → limitación conocida
- cap.71 incluye oro + plata + piedras preciosas → proxy razonable para oro
- Fuente: https://datos.gob.ar dataset sspm-exportaciones-segun-nomenclador-comun-mercosur-ncm
- AR_ECONOMIC_FEEDS guardadas con commodity_id=NULL → requieren --reclassify para aparecer
  en los paneles de noticias por commodity

---

### Sesión 7 — 2026-04-12
**Completado:**
- Reclasificación noticias AR: feeds Ámbito/iProfesional siguen en 403, Cronista devuelve 0. Sin artículos pendientes en DB.
- backend/pipelines/summary.py: genera resumen semanal LLM por commodity
  Tabla weekly_summaries. 3 resúmenes generados OK con Groq. GET /summary/{commodity_id}
- backend/pipelines/alerts.py: detecta noticias relevance_score >= 0.7 + impact_direction bullish/bearish
  Tabla alerts. 6 alertas generadas (3 litio, 3 soja). GET /alerts/
- backend/pipelines/comex_bilateral.py: lee comex-IED/products.json → 2431 registros bilaterales (80 países)
  GET /trade-flows/partners?commodity=&year=&flow=
- frontend/src/components/WeeklySummary.tsx: resumen LLM + key_signals pills
- frontend/src/components/AlertBanner.tsx: alertas activas amber/blue según severity
- frontend/src/components/TradePartnersChart.tsx: bar chart horizontal top-10 socios, exp/imp toggle, año
- Dashboard: AlertBanner, nueva fila WeeklySummary + TradePartnersChart
- Dockerfile + railway.toml + fly.toml + DEPLOY.md
- TypeScript: tsc --noEmit sin errores. Smoke test API: todos los endpoints OK.

**Notas de Sesión 7:**
- comex-IED products.json: datos anuales 2015-2026, 80 países, caps 2 dígitos, valores USD
- Para deploy en Railway: SQLite sin persistencia → usar Fly.io con volumen o migrar a PostgreSQL

**Pendiente para Sesión 8:**
- Ejecutar deploy real en Fly.io (flyctl launch → fly volumes create → fly deploy)
- Deploy frontend en Vercel/GitHub Pages + actualizar proxy en vite.config.ts
- Cron en producción para pipelines (prices, news, summary, alerts)
- Agregar nuevos commodities: cobre (CU=F), gas natural (NG=F), trigo (ZW=F)
- Panel de admin para ver/forzar ejecución de pipelines

---

### Sesión 9 — 2026-04-12
**Completado:**
- Fix proxy vite.config.ts: ya estaba en 8000 (corregido sesión 8)
- Fix crítico: config.py no llamaba load_dotenv() → API keys LLM/etc nunca se cargaban
  Agregado load_dotenv(ROOT/.env) al inicio de config.py — todos los pipelines LLM ahora funcionan
- YahooMacroPipeline: reemplaza BCRAPipeline (API BCRA v3.0 deprecada 2025)
  Fuentes vía yfinance sin API key:
    USDARS=X  → tc_oficial_usd_ars (TC USD/ARS, 248 registros 90 días)
    DX-Y.NYB  → broad_dollar_idx (ICE Dollar Index proxy DXY)
    ^IRX      → fed_funds_rate (T-bill 13 semanas, proxy tasa Fed)
- FREDPipeline: conservado pero se omite si FRED_API_KEY vacío (log claro)
- ImpactRadar ahora muestra las 5 variables: TC=1370 ARS/USD, DXY=99.1, Fed=3.59%, ENSO=-0.16, Retenciones
- Fix feeds RSS: copper-price/feed → 200 (copper/feed era 404)
- news.py: commodities reconocidos extendido a 6 (incluye copper, natgas, wheat)
  --commodity flag acepta los 6 nuevos valores
- Reclasificación LLM completa (57 artículos): noticias redistribuidas correctamente
  copper: 6, gold: 10, lithium: 23, natgas: 7, soy: 11, wheat: 0 (normal, no en mining.com)
- Alertas re-generadas: lithium 3, gold 3, soy 3, copper 3, natgas 1 (total 13 alertas activas)
- Resúmenes LLM: 6/6 commodities generados con Groq
- admin.py + AdminPanel.tsx: ya estaban implementados (sesión previa), descripciones actualizadas
- TypeScript: tsc --noEmit sin errores

**Estado de datos al cierre de sesión 9:**
- Precios: 6 commodities + 8 empresas trackeadas con 90 días histórico
- Variables globales: TC USD/ARS, DXY, Fed Rate, ENSO ONI → todas activas
- Retenciones: 6 commodities con valores vigentes
- Noticias: 5 de 6 commodities con noticias clasificadas (wheat: 0, esperado)
- Alertas: 5 de 6 commodities con alertas activas
- Resúmenes: 6/6

**Notas de Sesión 9:**
- BCRAPipeline eliminado del run_all — reemplazado por YahooMacroPipeline
- FRED sigue disponible si se configura FRED_API_KEY (datos más precisos que yfinance proxy)
- wheat no tiene noticias en mining.com (es lógico); para trigo usar feeds AR de granos
  (próxima sesión: agregar feeds específicos de trigo como agrofy, bichosdecampo ya filtran)
- mining.com copper-price/feed: devuelve 200 pero 0 artículos (feed existe pero está vacío)
  El feed general de mining.com tiene artículos de cobre que el LLM reclasifica correctamente

### Sesión 8 — 2026-04-12
**Completado:**
- Nuevos commodities: cobre (CU=F), gas natural (NG=F), trigo (ZW=F)
  - config.py: tickers, feeds RSS, company tickers (FCX, SCCO, YPF, TTE, PAM)
  - init_db.py: seed commodities (supply_chain JSON) + 13 empresas nuevas
  - prices.py: SYMBOL_COMMODITY + 90 días histórico descargado (150 precios, 1350 valuaciones)
  - comex.py: NCM map (cap.74 cobre, cap.27 natgas, cap.10 trigo) + 108 registros
  - variables.py: retenciones cobre 3%, gas 0%, trigo 12% + fix duplicados ENSO
  - summary.py + alerts.py: COMMODITIES extendido a 6
  - theme.ts: colores copper/natgas/wheat
  - CommodityCard + PriceChart: PRIMARY_PRICE_TYPE para los 3 nuevos
  - ImpactRadar: COMMODITY_VARS + VARIABLE_META para copper/natgas/wheat
  - TradeFlowChart: NCM_LABELS para los 3 nuevos
- Fix crítico variables API (/impact-variables/latest):
  - Bug: NULL = NULL es NULL en SQL → ENSO nunca aparecía
  - Fix: usar iv.commodity_id IS latest.commodity_id en JOIN
  - Fix: query reestructurada con subquery correlacionada + GROUP BY para deduplicar
  - Fix: ENSO pipeline usa SELECT EXISTS en lugar de INSERT OR IGNORE (evita duplicados NULL)
  - 914 registros duplicados de ENSO eliminados de DB
- TypeScript: tsc --noEmit sin errores

**Notas de Sesión 8:**
- Backend corre en puerto 8000 (no 8001 — el proceso viejo en 8001 fue eliminado)
- Verificar que vite.config.ts proxy apunta a 8000 antes de iniciar frontend
- FRED API key sigue sin configurar → fed_funds_rate, broad_dollar_idx, cpi_us muestran "—"
- BCRA API retorna 400 con fechas 2026 → tc_oficial_usd_ars vacío (endpoint variable 4 puede haber cambiado)
- Para nuevos commodities: noticias, summaries y alerts estarán vacíos hasta correr news/summary/alerts pipelines

**Pendiente para Sesión 10:**
- Deploy backend en Fly.io
- Deploy frontend en Vercel/GitHub Pages
- Cron en producción para pipelines
- Correr news pipeline para feeds de copper/natgas/wheat y luego summary + alerts
- Investigar BCRA API si el retry automático no resuelve el 400 (probar variable IDs alternativos)

---

### Sesión 6 — 2026-04-12
**Completado:**
- backend/pipelines/variables.py: nuevo pipeline con 2 sub-pipelines
  - ENSOPipeline: descarga NOAA ONI (oni.ascii.txt) — 914 registros desde 1950
    Mapeo SEAS→mes central, guardado como variable_name='enso_oni', commodity_id=NULL
  - RetencionesPipeline: datos estáticos AFIP/decreto
    Soja 33% (Decreto 230/2020), Oro 12% (Res. 61/2022), Litio 4.5% (Decreto 206/2023)
- frontend/src/types/index.ts: interfaz ImpactVariable agregada
- frontend/src/utils/api.ts: api.variables.latest() y api.variables.history()
- frontend/src/components/ImpactRadar.tsx: nuevo componente
  Panel de cards (auto-fill grid) con: Fed Rate, DXY, TC Oficial, ENSO/ONI, Retenciones
  ENSO con coloreo por umbral (El Niño amber / La Niña blue / Neutro slate)
  Tooltip con descripción de fuente en cada card
- Dashboard.tsx: integración de ImpactRadar (full width entre TradeFlowChart y empresas)
  Mobile responsive: useIsMobile hook (breakpoint 768px) → grids colapsan a 1 columna
  Padding lateral adaptativo (32px → 16px en mobile)
- TypeScript: tsc --noEmit sin errores

**Notas de Sesión 6:**
- NOAA ONI cambió formato: solo 4 columnas (SEAS YR TOTAL ANOM), ANOM en índice 3
  (no 7 columnas como en versiones anteriores — fix aplicado)
- Fed Rate y DXY ya están en impact_variables vía FREDPipeline (prices.py) → no duplicados
- ENSO almacenado con commodity_id=NULL (global); ImpactRadar lo muestra para todos los commodities
- Retenciones son punto en el tiempo (fecha vigencia), no serie histórica → 1 registro por commodity
- useIsMobile hook: window.innerWidth < 768px, con addEventListener('resize') + cleanup

---

## LOG DE SESIONES

### Sesión 1 — 2026-04-12
**Completado:**
- Estructura de directorios
- schema.sql (incluye `company_valuations`)
- init_db.py con seed de commodities, actores y empresas con tickers
- config.py
- base_pipeline.py
- prices.py (yfinance: commodities + empresas; BCRA; FRED)
- requirements.txt

**Notas de Sesión 1:**
- ALTM (Arcadium Lithium) y PLL (Piedmont) están delistados → removidos de COMPANY_TICKERS
- Arcadium fue adquirida por Rio Tinto en 2025, no hay ticker sucesor cotizando aún
- Precios funcionando: Oro $4.787 USD/oz, empresas OK (ALB $173, SQM $82, Barrick $43)
- 71 registros en DB: 21 precios commodity + 50 valuaciones empresa

**Pendiente para Sesión 2:**
- API FastAPI (main.py + routes): /prices, /commodities, /companies, /impact-variables ✓
- Frontend básico: Dashboard con 3 CommodityCards + PriceChart (recharts) + CompanyValuationPanel ✓

---

### Sesión 2 — 2026-04-12
**Completado:**
- backend/api/main.py: FastAPI app con CORS, monta los 4 routers
- backend/api/routes/commodities.py: GET /commodities/, GET /commodities/{id}
- backend/api/routes/prices.py: GET /prices/{id}/latest, GET /prices/{id}?days=N
- backend/api/routes/companies.py: GET /companies/, GET /companies/{id}, GET /companies/{id}/valuations?days=N
- backend/api/routes/variables.py: GET /impact-variables/, GET /impact-variables/latest
- run.py: entry point uvicorn (python run.py)
- frontend/package.json + vite.config.ts + tsconfig.json
- frontend/src/types/index.ts: tipos Commodity, Price, Company, Valuation
- frontend/src/utils/api.ts: cliente fetch con proxy /api → localhost:8000
- frontend/src/components/CommodityCard.tsx: precio actual + variación
- frontend/src/components/PriceChart.tsx: AreaChart recharts con selector 1M/3M/6M/1A
- frontend/src/components/CompanyValuationPanel.tsx: tabla empresas + precio acción + mkt cap
- frontend/src/components/Dashboard.tsx: layout completo
- frontend/src/App.tsx + main.tsx

**Pendiente para Sesión 3:**
- Instalar dependencias: cd frontend && npm install
- Levantar backend: python run.py (requiere .env con FRED_API_KEY, etc.)
- Levantar frontend: cd frontend && npm run dev
- Verificar datos reales en dashboard
- Fase 2: Scraper RSS + clasificador LLM + NewsPanel

---

## NOTAS TÉCNICAS CLAVE

### AI / LLM
- Proveedor principal: **Groq** (más rápido y barato para clasificación)
- Fallback 1: **Cerebras**
- Fallback 2: **Mistral**
- Lógica de rotación en: `backend/pipelines/llm_client.py`
- Variables de entorno: `GROQ_API_KEY`, `CEREBRAS_API_KEY`, `MISTRAL_API_KEY`

### Empresas con valuación trackeada
Ver tabla `company_valuations` en DB y seed en `init_db.py`.

**Litio:** ALB (Albemarle), SQM, ALTM (Arcadium), LAC, PLL, GNENF (Ganfeng OTC)
**Oro:** GOLD (Barrick), NEM (Newmont), PAAS (Pan American Silver), AEM (Agnico Eagle)
**Soja:** BG (Bunge), ADM, VITOL (privada/skip), AGD (no listada), LDC (privada/skip)

### NCMs monitoreados
- Litio: 2836.91.00, 2825.20.00
- Oro: 7108.12.10, 7108.13.10
- Soja: 1201.90.00, 1507.10.00, 2304.00.00

### Puertos/endpoints externos
- BCRA: https://api.bcra.gob.ar/estadisticas/v3.0/
- FRED: https://fred.stlouisfed.org/ (API key requerida)
- yfinance: sin key
- Groq: https://api.groq.com/

---

## CÓMO RETOMAR UNA SESIÓN

1. Leer este archivo
2. Ver el último ítem completado en el log
3. Retomar desde "Pendiente para Sesión X"
4. Al finalizar: actualizar este archivo con lo completado y lo pendiente
