# Pisubí — Roadmap de Mejoras

**Actualizado:** 2026-04-13 | **Sesión base:** 14

## Orden de ejecución sugerido

```
━━━ ESTABILIZACIÓN ━━━
Sesión 15:  #1 (datos Render) + #10 (precios históricos)
Sesión 16:  A1 (migrar SQLite → PostgreSQL)
Sesión 17:  B1 (NCM 4-6 dígitos) + E1 (cron jobs en Render)

━━━ VALOR ANALÍTICO CORE ━━━
Sesión 18:  C2 (briefing semanal PDF) + D2 (indicadores de frescura)
Sesión 19:  C1 (correlaciones cruzadas) + F2 (regímenes de mercado)
Sesión 20:  F8 (señales técnicas) + F7 (COT — pipeline)
Sesión 21:  F7 (COT — frontend) + D1 (navegación por commodity)
Sesión 22:  F4 (spread AR vs. internacional) + F3 (sentimiento temporal)

━━━ INTELIGENCIA DIFERENCIAL ━━━
Sesión 23:  F1 (índice de riesgo de suministro)
Sesión 24:  G1 (monitor BORA/regulatorio)
Sesión 25:  B3 (NER entidades) + G2 (calendario forward-looking)
Sesión 26:  F6 (comparativa regional)
Sesión 27:  F5 (Sankey cadena de valor)

━━━ POLISH ━━━
Sesión 28:  D3 (mobile refinements) + E2 (monitoring)
```

---

## Pendientes inmediatos (antes de continuar con roadmap)

### #1 — Datos 2024 near-zero en Render (CRÍTICO)
Soja, oro, gas, litio muestran ~0 en 2024 en producción. Localmente OK.
- **Causa:** `comex_indec.py` usa ZIPs locales que no existen en Render.
- **Fix opción A:** `comex_comtrade.py` — UN Comtrade API pública.
  - `https://comtradeapi.un.org/public/v1/preview/C/A/HS?reporterCode=32&period=2023&flowCode=X&cmdCode=12&includeDesc=true`
  - Sin key: 500 req/día. Argentina = reporterCode 32.
- **Fix opción B:** subir DB local a Render via Render Shell (temporal).

### #10 — Precios históricos desde más atrás
- `prices.py`: flag `--full-history` con `start="1990-01-01"` en yfinance.
- Nuevo `worldbank_prices.py`: World Bank Pink Sheet mensual desde ~1960 (soja, trigo, maíz, cobre, gas, oro).
- `PriceChart.tsx`: selector de rango 1A / 5A / 10A / Máx.

---

## Fase A — Estabilización

### A1. Migrar SQLite → PostgreSQL (CRÍTICA)
SQLite en Render se resetea en cada deploy. Sin réplicas, sin backups.
- Crear instancia Postgres gratuita (Supabase free tier o Neon.tech)
- Adaptar `backend/db/init_db.py`: sqlite3 → psycopg2
- Cambios en schema: `SERIAL PRIMARY KEY`, `ON CONFLICT DO NOTHING`, `NOW()`
- Variable de entorno `DATABASE_URL`
- Actualizar todos los pipelines para usar pool de conexiones

### A2. Reestructurar documentación de sesiones
Estado actual: `SESSIONS.md` centralizado. Migrar a:
```
docs/CURRENT.md       ← estado activo (máx 30 líneas)
docs/sessions/        ← sesión-01.md, sesión-02.md...
ARCHITECTURE.md       ← decisiones técnicas
```

---

## Fase B — Calidad de datos

### B1. NCM 2 dígitos → 4-6 dígitos (ALTA)
Cap.28 incluye todos los químicos inorgánicos, no solo litio. Cap.27 incluye petróleo.
Posiciones precisas:
- Litio: 2836.91 (carbonato), 2825.20 (óxido/hidróxido)
- Oro: 7108.12, 7108.13
- Soja: 1201.90 (porotos), 1507.10 (aceite crudo), 2304.00 (harina)
- Cobre: 7403 (refinado), 7401 (matas)
- Gas: 2711.11 (GNL), 2711.21 (gaseoso)
- Trigo: 1001.19 (duro), 1001.99 (demás)

### B2. Diversificar feeds de noticias (ALTA)
Feeds a agregar: Reuters Commodities, BCR Rosario, Fastmarkets cobre, Secretaría Energía AR.

### B3. NER sobre noticias: extraer entidades (MEDIA-ALTA)
Extender prompt LLM de clasificación para devolver `companies`, `countries`, `amounts_usd`, `key_event`.
Nueva tabla `news_entities`. Tags de empresas en NewsPanel.

---

## Fase C — Análisis cruzado

### C1. Panel de correlaciones cruzadas (ALTA)
Endpoint `/analytics/correlations`. Ventanas 30/90/180d. Pearson entre series de precios y variables.
Frontend: `CorrelationHeatmap.tsx` con Recharts.

### C2. Export briefing semanal PDF/XLSX (ALTA)
Endpoint `/export/weekly-briefing?format=pdf`. 1-2 páginas:
tabla resumen precios, top alertas, resumen LLM, variables macro, comercio exterior.
Generación con WeasyPrint o ReportLab.

---

## Fase D — Frontend UX

### D1. Navegación por commodity (tabs) (MEDIA)
Tab bar: `Todos | Litio | Oro | Soja | Cobre | Gas | Trigo`.
React Router con `/dashboard`, `/dashboard/lithium`, etc.

### D2. Indicadores de frescura de datos (MEDIA)
Footer badge: `Precios: hace 2h | Noticias: hace 5h | Comex: 2026-02`.
Endpoint `/status/pipelines` con timestamp del último run.

### D3. Mobile-first refinements (BAJA)
Touch tooltips en Recharts, bottom sheet para filtros, pull-to-refresh.

---

## Fase E — Operaciones en producción

### E1. Cron jobs (ALTA, post-deploy estable)
| Pipeline | Frecuencia |
|----------|------------|
| prices.py | Diario 08:00 UTC |
| news.py | Cada 6h |
| summary.py | Semanal lunes 10:00 UTC |
| alerts.py | Diario 09:00 UTC |
| comex.py | Mensual 1ro del mes |
| variables.py | Semanal lunes 08:00 UTC |

### E2. Monitoring y health checks (MEDIA)
`/health` con check DB + timestamp último pipeline. UptimeRobot free tier.

---

## Fase F — Inteligencia analítica avanzada

### F1. Índice de riesgo de suministro 0-100 (ALTA)
Componentes: HHI producción (25%), estabilidad política (20%), dependencia AR (20%), volatilidad precio (20%), sentimiento noticioso (15%).
Datos HHI iniciales:
- Litio: AU 47%, CL 30%, CN 15% → HHI ≈ 0.33
- Soja: BR 37%, US 28%, AR 17% → HHI ≈ 0.24
- Oro: CN 10%, AU 9%, RU 9% → HHI ≈ 0.04

### F2. Detección de regímenes de mercado (MEDIA-ALTA)
SMA20 vs SMA50 vs SMA200 + Bollinger + ATR → clasifica ALCISTA / BAJISTA / LATERAL / VOLÁTIL.
Badge en CommodityCard. Input al weekly summary LLM.

### F3. Análisis de sentimiento temporal (MEDIA-ALTA)
Serie diaria de sentiment por commodity (promedio ponderado por relevance_score, SMA7).
`SentimentOverlay.tsx` — overlay opcional en PriceChart, eje Y secundario.

### F4. Spread AR vs. precio internacional (ALTA)
`Precio interno efectivo = Precio CBOT × (1 - retención) - flete`
`Captura productor (%) = precio_interno / CBOT × 100`
Datos ya en DB (precios + retenciones). `SpreadChart.tsx` con anotaciones en fechas de decretos.

### F5. Mapa de cadena de valor Sankey (MEDIA)
Datos estáticos en `supply_chain` JSON de cada commodity. D3 Sankey.

### F6. Comparativa regional AR vs. vecinos (MEDIA-ALTA)
AR vs. Chile (litio/cobre), Brasil (soja), Bolivia (litio/gas). Tabla: producción, exportaciones, carga fiscal, IED.

### F7. CFTC Commitments of Traders semanal (ALTA — DATOS VERIFICADOS)
Datos reales al 7/4/2026: oro 4.19:1 (extremadamente bullish), cobre 2.24:1, soja net long 189,630.
Fuente: `https://www.cftc.gov/dea/futures/deacmxsf.htm` (metales) y `deacbtsf.htm` (granos). Sin API key.
Códigos: oro=088691, cobre=085692, soja=005602, trigo=001602, gas=023651.
Cron viernes 20:00 UTC.
`COTPanel.tsx`: gauge long/short ratio + línea net position vs precio.

### F8. Señales técnicas automatizadas (ALTA — CERO DEPENDENCIAS EXTERNAS)
Solo numpy sobre precios ya en DB. Requisito: `prices.py --days 365`.
Señales: Golden/Death Cross (SMA50/SMA200), RSI 30/70, Bollinger breakout, MACD cross, volumen anomalía.
`TechnicalSignals.tsx`: lista con iconos, marcadores en PriceChart.

---

## Fase G — Contexto y calendario

### G1. Monitor BORA + regulatorio (ALTA)
Detectar cambios de retenciones, minería, hidrocarburos antes de la cobertura de prensa.
Endpoint BORA JSON ya descubierto. Clasificación LLM por commodity.

### G2. Calendario forward-looking (MEDIA)
FOMC dates, INDEC calendar, cosechas AR (soja abr-jun, trigo dic-ene, maíz mar-may), LME Week.
`EventTimeline.tsx`. Integrar al briefing PDF.
