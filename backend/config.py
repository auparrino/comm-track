"""
Pisubí — Configuración central
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env desde la raíz del proyecto
_ROOT = Path(__file__).parent.parent
load_dotenv(_ROOT / ".env")

# Directorios
ROOT_DIR = _ROOT
BACKEND_DIR = Path(__file__).parent
DB_PATH = BACKEND_DIR / "db" / "commodity_monitor.db"
DATA_DIR = ROOT_DIR / "data"

# API keys (desde variables de entorno)
GROQ_API_KEY      = os.getenv("GROQ_API_KEY", "")
CEREBRAS_API_KEY  = os.getenv("CEREBRAS_API_KEY", "")
MISTRAL_API_KEY   = os.getenv("MISTRAL_API_KEY", "")
FRED_API_KEY      = os.getenv("FRED_API_KEY", "")
BCRA_BASE_URL     = "https://api.bcra.gob.ar/estadisticas/v3.0"

# Modelos LLM por proveedor
LLM_PROVIDERS = {
    "groq": {
        "model": "llama-3.3-70b-versatile",
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
    },
    "cerebras": {
        "model": "llama-3.3-70b",
        "base_url": "https://api.cerebras.ai/v1",
        "api_key_env": "CEREBRAS_API_KEY",
    },
    "mistral": {
        "model": "mistral-small-latest",
        "base_url": "https://api.mistral.ai/v1",
        "api_key_env": "MISTRAL_API_KEY",
    },
}

# Orden de preferencia para LLM (rotación con fallback)
LLM_PROVIDER_ORDER = ["groq", "cerebras", "mistral"]

# Tickers de Yahoo Finance por commodity
COMMODITY_TICKERS = {
    "gold":    {"symbol": "GC=F",  "type": "futures", "name": "Gold Futures"},
    "gold_etf":{"symbol": "GLD",   "type": "etf",     "name": "SPDR Gold ETF"},
    "soy":     {"symbol": "ZS=F",  "type": "futures", "name": "Soybean Futures"},
    "soy_meal":{"symbol": "ZM=F",  "type": "futures", "name": "Soybean Meal Futures"},
    "soy_oil": {"symbol": "ZL=F",  "type": "futures", "name": "Soybean Oil Futures"},
    # Litio no tiene futures directos; usamos ETF proxy
    "lithium_etf": {"symbol": "LIT", "type": "etf", "name": "Global X Lithium ETF (proxy)"},
    # Nuevos commodities Sesión 8
    "copper":  {"symbol": "CU=F",  "type": "futures", "name": "Copper Futures"},
    "natgas":  {"symbol": "NG=F",  "type": "futures", "name": "Natural Gas Futures"},
    "wheat":   {"symbol": "ZW=F",  "type": "futures", "name": "Wheat Futures"},
}

# Empresas con tickers (para valuación)
COMPANY_TICKERS = {
    # Litio
    "ALB":   {"commodity": "lithium", "name": "Albemarle Corp",          "exchange": "NYSE"},
    "SQM":   {"commodity": "lithium", "name": "SQM (Sociedad Química)",  "exchange": "NYSE"},
    # ALTM (Arcadium) — delistado 2025 tras adquisición por Rio Tinto
    # PLL (Piedmont) — delistado/suspendido 2025
    "LAC":   {"commodity": "lithium", "name": "Lithium Americas Corp",   "exchange": "NYSE"},
    "GNENF": {"commodity": "lithium", "name": "Ganfeng Lithium (OTC)",   "exchange": "OTC"},
    # Oro
    "GOLD":  {"commodity": "gold",    "name": "Barrick Gold Corp",       "exchange": "NYSE"},
    "NEM":   {"commodity": "gold",    "name": "Newmont Corp",            "exchange": "NYSE"},
    "PAAS":  {"commodity": "gold",    "name": "Pan American Silver",     "exchange": "NASDAQ"},
    "AEM":   {"commodity": "gold",    "name": "Agnico Eagle Mines",      "exchange": "NYSE"},
    # Soja (traders/procesadoras)
    "BG":    {"commodity": "soy",     "name": "Bunge Global SA",         "exchange": "NYSE"},
    "ADM":   {"commodity": "soy",     "name": "Archer-Daniels-Midland",  "exchange": "NYSE"},
    # Cobre
    "FCX":   {"commodity": "copper",  "name": "Freeport-McMoRan Inc",    "exchange": "NYSE"},
    "SCCO":  {"commodity": "copper",  "name": "Southern Copper Corp",    "exchange": "NYSE"},
    # Gas Natural
    "YPF":   {"commodity": "natgas",  "name": "YPF S.A.",                "exchange": "NYSE"},
    "TTE":   {"commodity": "natgas",  "name": "TotalEnergies SE",        "exchange": "NYSE"},
    "PAM":   {"commodity": "natgas",  "name": "Pampa Energía S.A.",      "exchange": "NYSE"},
}

# FRED series IDs
FRED_SERIES = {
    "fed_funds_rate": "FEDFUNDS",
    "cpi_us":         "CPIAUCSL",
    "dxy_index":      "DTWEXBGS",   # Broad Dollar Index (proxy DXY)
}

# BCRA variable IDs relevantes
# 1 = Reservas internacionales, 4 = Base monetaria, etc.
# El tipo de cambio se obtiene vía endpoint separado
BCRA_VARIABLES = {
    "tc_oficial": None,  # endpoint /divisas
}

# RSS feeds por commodity
# Estado verificado sesión 5 (2026-04-12):
#   mining.com/web-tag/lithium/feed/   → ✓ 200
#   mining.com/web-tag/gold-price/feed/→ ✓ 200  (gold/feed/ → 404)
#   mining.com/web-tag/gold/feed/      → 404 (removed)
#   mining.com/web-tag/precious-metals/feed/ → 404 (removed)
#   mining.com/feed/                   → ✓ 200 (fallback general)
#   bichosdecampo.com/feed/            → ✓ 200
#   agrositio.com.ar/feed/             → 404 (removed)
#   cronista.com/rss/agro-negocios/    → ✓ 200
#   agrofy.com.ar/blog/feed            → ✓ 200
#   infobae.com/tag/agro/feed/         → ✓ 200
RSS_FEEDS = {
    "lithium": [
        "https://www.mining.com/web-tag/lithium/feed/",  # tag específico litio ✓
        "https://www.mining.com/feed/",                  # fallback general ✓
    ],
    "gold": [
        "https://www.mining.com/web-tag/gold-price/feed/",  # tag precio oro ✓
        "https://www.mining.com/feed/",                     # fallback general ✓
    ],
    "soy": [
        "https://bichosdecampo.com/feed/",               # agro AR ✓
        "https://www.cronista.com/rss/agro-negocios/",   # agro-negocios ✓
        "https://www.agrofy.com.ar/blog/feed",           # agro marketplace AR ✓
        "https://www.infobae.com/tag/agro/feed/",        # agro infobae ✓
    ],
    "copper": [
        "https://www.mining.com/web-tag/copper-price/feed/",  # tag precio cobre ✓ 200
        "https://www.mining.com/feed/",                       # fallback general ✓
    ],
    "natgas": [
        "https://www.energiaestrategica.com/feed/",      # energía renovable/gas AR
        "https://www.cronista.com/rss/economia/",        # economía general AR ✓
    ],
    "wheat": [
        "https://bichosdecampo.com/feed/",               # agro AR (cubre trigo) ✓
        "https://www.cronista.com/rss/agro-negocios/",   # agro-negocios ✓
        "https://www.agrofy.com.ar/blog/feed",           # agro marketplace AR ✓
    ],
}

# Feeds de economía argentina (no atados a un commodity específico)
# El LLM asignará commodity_id durante la clasificación.
# Estado verificado sesión 5:
#   ambito.com/rss/economia.xml      → ✓ 200 (antes 403, ahora funciona)
#   cronista.com/rss/economia/       → ✓ 200
#   iprofesional.com/feed/           → ✓ 200
AR_ECONOMIC_FEEDS = [
    "https://www.ambito.com/rss/economia.xml",      # Ámbito Financiero ✓
    "https://www.cronista.com/rss/economia/",        # El Cronista ✓
    "https://www.iprofesional.com/feed/",            # iProfesional ✓
]
