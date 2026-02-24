"""
Configuración central del pipeline de datos diarios.
Constantes, URLs, tickers, ratios y parámetros.
"""

from datetime import date
import os

# --- General ---
REQUEST_TIMEOUT = 15  # seconds
TODAY = date.today().isoformat()
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
OUTPUT_FILENAME_TEMPLATE = "datos_diarios_{fecha}.json"

# --- DolarAPI ---
DOLARAPI_BASE = "https://dolarapi.com/v1"
DOLARAPI_ALL = f"{DOLARAPI_BASE}/dolares"

# --- Bluelytics ---
BLUELYTICS_URL = "https://api.bluelytics.com.ar/v2/latest"

# --- BCRA ---
BCRA_COTIZACIONES = "https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones"
BCRA_MACRO_BASE = "https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias"
BCRA_VARIABLES = {
    "reservas": 1,
    "tc_minorista": 4,
    "tc_mayorista": 5,
    "badlar": 7,
    "base_monetaria": 15,
    "cer": 30,
}

# --- ArgentinaDatos ---
ARGDATOS_BASE = "https://api.argentinadatos.com/v1"
ARGDATOS_RIESGO_PAIS_ULTIMO = f"{ARGDATOS_BASE}/finanzas/indices/riesgo-pais/ultimo"
ARGDATOS_INFLACION = f"{ARGDATOS_BASE}/finanzas/indices/inflacion"
ARGDATOS_INFLACION_INTERANUAL = f"{ARGDATOS_BASE}/finanzas/indices/inflacionInteranual"
ARGDATOS_PLAZO_FIJO = f"{ARGDATOS_BASE}/finanzas/tasas/plazoFijo"

# --- Tickers Acciones Argentinas ---
ACCIONES_AR = [
    "GGAL.BA", "YPFD.BA", "PAMP.BA", "BBAR.BA", "CEPU.BA",
    "TXAR.BA", "TGSU2.BA", "LOMA.BA", "CRES.BA", "ALUA.BA",
]

# --- CEDEARs ---
CEDEARS_TICKERS_BA = [
    "MELI.BA", "AAPL.BA", "GOOGL.BA", "MSFT.BA", "AMZN.BA",
    "TSLA.BA", "NVDA.BA", "JPM.BA", "KO.BA", "GLOB.BA", "COIN.BA",
]

US_TICKERS = [
    "MELI", "AAPL", "GOOGL", "MSFT", "AMZN",
    "TSLA", "NVDA", "JPM", "KO", "GLOB", "COIN",
]

RATIOS_CEDEAR = {
    "MELI": 120, "AAPL": 20, "GOOGL": 58, "MSFT": 30, "AMZN": 144,
    "TSLA": 15, "NVDA": 24, "JPM": 15, "KO": 5, "GLOB": 18, "COIN": 27,
}

# --- Índices ---
INDICES = {
    "MERVAL": "^MERV",
    "SP500": "^GSPC",
    "NASDAQ": "^IXIC",
    "DOW_JONES": "^DJI",
}

# --- Commodities ---
COMMODITIES = {
    "soja": {"ticker": "ZS=F", "unidad": "USD/bushel"},
    "maiz": {"ticker": "ZC=F", "unidad": "USD/bushel"},
    "trigo": {"ticker": "ZW=F", "unidad": "USD/bushel"},
    "petroleo_wti": {"ticker": "CL=F", "unidad": "USD/barrel"},
    "oro": {"ticker": "GC=F", "unidad": "USD/oz"},
}

# --- Crypto ---
CRYPTO = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "SOL": "SOL-USD",
    "ADA": "ADA-USD",
}

# --- Bonos clave ---
BONOS_CLAVE = ["AL29", "AL30", "AL35", "AL41", "GD30", "GD35", "GD38", "GD41"]

# --- RSS Feeds ---
RSS_FEEDS_AR = {
    "ambito": "https://www.ambito.com/rss/economia.xml",
    "cronista": "https://www.cronista.com/files/rss/finanzas.xml",
    "infobae": "https://www.infobae.com/arc/outboundfeeds/rss/category/economia/",
}

RSS_FEEDS_INTL = {
    "bloomberg": "https://feeds.bloomberg.com/markets/news.rss",
    "cnbc": (
        "https://search.cnbc.com/rs/search/combinedcms/view.xml"
        "?partnerId=wrss01&id=10000664"
    ),
    "ft": "https://www.ft.com/rss/markets",
}

MAX_NOTICIAS_PER_FEED = 10
