-- ============================================================
-- Pisubí — Monitor de Commodities
-- Schema SQLite
-- ============================================================

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ------------------------------------------------------------
-- Tabla maestra de commodities
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS commodities (
    id          TEXT PRIMARY KEY,       -- 'lithium', 'gold', 'soy'
    name_es     TEXT NOT NULL,
    name_en     TEXT NOT NULL,
    unit        TEXT,                   -- 'USD/ton', 'USD/oz', 'USD/bu'
    category    TEXT,                   -- 'mineral', 'metal_precioso', 'agro'
    description TEXT,
    supply_chain_json TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- Precios de commodities
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS prices (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    commodity_id TEXT REFERENCES commodities(id),
    date         DATE NOT NULL,
    price        REAL NOT NULL,
    source       TEXT NOT NULL,         -- 'yahoo', 'lbma', 'worldbank', 'bcra'
    price_type   TEXT DEFAULT 'spot',   -- 'spot', 'futures', 'etf', 'index'
    currency     TEXT DEFAULT 'USD',
    UNIQUE(commodity_id, date, source, price_type)
);

CREATE INDEX IF NOT EXISTS idx_prices_commodity_date ON prices(commodity_id, date DESC);

-- ------------------------------------------------------------
-- Empresas vinculadas a commodities (para valuación)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS companies (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    commodity_id TEXT REFERENCES commodities(id),
    name         TEXT NOT NULL,
    ticker       TEXT,                  -- símbolo bursátil (NULL si no cotiza)
    exchange     TEXT,                  -- 'NYSE', 'NASDAQ', 'TSX', 'OTC'
    country      TEXT,
    province_ar  TEXT,                  -- si es empresa con operaciones en AR
    project_name TEXT,                  -- proyecto minero/agro principal en AR
    role         TEXT,                  -- 'producer', 'trader', 'processor', 'miner'
    is_ar_actor  BOOLEAN DEFAULT 0,     -- tiene operaciones en Argentina
    notes        TEXT,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(commodity_id, name)
);

-- Índice único para prevenir duplicados en re-runs de init_db
-- Nota: en DB existentes con duplicados, este índice fallará hasta que se limpien.
CREATE UNIQUE INDEX IF NOT EXISTS idx_companies_unique ON companies(commodity_id, name);
CREATE INDEX IF NOT EXISTS idx_companies_commodity ON companies(commodity_id);

-- ------------------------------------------------------------
-- Valuación de empresas (precio de acción + métricas)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS company_valuations (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id           INTEGER REFERENCES companies(id),
    date                 DATE NOT NULL,
    close_price          REAL,          -- precio de cierre en moneda de la bolsa
    open_price           REAL,
    high_price           REAL,
    low_price            REAL,
    volume               INTEGER,
    market_cap_usd       REAL,          -- capitalización bursátil en USD
    pe_ratio             REAL,          -- P/E ratio (puede ser NULL)
    ev_ebitda            REAL,          -- EV/EBITDA si disponible
    currency             TEXT DEFAULT 'USD',
    source               TEXT DEFAULT 'yahoo',
    UNIQUE(company_id, date, source)
);

CREATE INDEX IF NOT EXISTS idx_cval_company_date ON company_valuations(company_id, date DESC);

-- ------------------------------------------------------------
-- Noticias scrapeadas y clasificadas
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS news (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    commodity_id     TEXT REFERENCES commodities(id),
    title            TEXT NOT NULL,
    snippet          TEXT,
    url              TEXT UNIQUE,
    source           TEXT NOT NULL,
    published_at     TIMESTAMP,
    scraped_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Clasificación LLM
    sentiment        TEXT,              -- 'positive', 'negative', 'neutral'
    signal_type      TEXT,             -- 'regulatory', 'geopolitical', 'supply',
                                       -- 'demand', 'climate', 'technology', 'price'
    relevance_score  REAL,             -- 0.0 a 1.0
    summary_es       TEXT,             -- resumen en español
    impact_direction TEXT,             -- 'bullish', 'bearish', 'neutral'
    llm_provider     TEXT,             -- 'groq', 'cerebras', 'mistral'
    classified_at    TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_news_commodity_date ON news(commodity_id, published_at DESC);

-- ------------------------------------------------------------
-- Flujos comerciales (desde pipeline Comex/INDEC)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trade_flows (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    commodity_id   TEXT REFERENCES commodities(id),
    ncm            TEXT NOT NULL,
    period         TEXT NOT NULL,       -- '2024-01'
    flow_type      TEXT NOT NULL,       -- 'export', 'import'
    country_dest   TEXT,
    country_origin TEXT,
    value_usd      REAL,
    weight_kg      REAL,
    unit_price_usd REAL,               -- calculado: value_usd / weight_kg
    source         TEXT DEFAULT 'indec'
);

CREATE INDEX IF NOT EXISTS idx_trade_commodity_period ON trade_flows(commodity_id, period DESC);

-- Unicidad: (commodity, ncm, periodo, flujo, destino, origen)
-- COALESCE en ambas columnas nullable para que NULL no colisione entre países distintos.
CREATE UNIQUE INDEX IF NOT EXISTS idx_trade_unique ON trade_flows(
    commodity_id, ncm, period, flow_type,
    COALESCE(country_dest,   ''),
    COALESCE(country_origin, '')
);

-- ------------------------------------------------------------
-- Variables de impacto
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS impact_variables (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    commodity_id TEXT REFERENCES commodities(id),
    variable_name TEXT NOT NULL,        -- 'fed_rate', 'enso_index', 'dxy', 'retenciones_porotos'
    date         DATE NOT NULL,
    value        REAL,
    value_text   TEXT,                  -- para variables cualitativas
    source       TEXT,
    unit         TEXT,
    UNIQUE(commodity_id, variable_name, date)
);

CREATE INDEX IF NOT EXISTS idx_ivar_commodity_var_date ON impact_variables(commodity_id, variable_name, date DESC);

-- ------------------------------------------------------------
-- Resúmenes semanales (generados por LLM)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS weekly_summaries (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    commodity_id  TEXT REFERENCES commodities(id),
    generated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    period_start  DATE NOT NULL,
    period_end    DATE NOT NULL,
    summary_text  TEXT NOT NULL,
    key_signals   TEXT,                    -- JSON array de strings
    llm_provider  TEXT,
    UNIQUE(commodity_id, period_start)
);

CREATE INDEX IF NOT EXISTS idx_wsum_commodity ON weekly_summaries(commodity_id, generated_at DESC);

-- ------------------------------------------------------------
-- Alertas de señales de alto impacto
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS alerts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    commodity_id    TEXT REFERENCES commodities(id),
    generated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    title           TEXT NOT NULL,
    description     TEXT,
    severity        TEXT,                  -- 'high', 'medium'
    signal_type     TEXT,
    llm_provider    TEXT,
    source_news_ids TEXT,                  -- JSON array de news.id
    is_active       BOOLEAN DEFAULT 1,
    expires_at      DATE
);

CREATE INDEX IF NOT EXISTS idx_alerts_commodity ON alerts(commodity_id, generated_at DESC);

-- ------------------------------------------------------------
-- Log de ejecución de pipelines
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_name      TEXT NOT NULL,
    commodity_id       TEXT,
    started_at         TIMESTAMP,
    finished_at        TIMESTAMP,
    status             TEXT,            -- 'success', 'error', 'partial'
    records_processed  INTEGER DEFAULT 0,
    records_skipped    INTEGER DEFAULT 0,
    error_message      TEXT
);
