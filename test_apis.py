"""
Test de acceso a APIs financieras.
Verifica conectividad y respuesta válida de cada API/fuente de datos.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

TIMEOUT = 15


# --- GRATUITAS (sin key) ---

def test_dolarapi():
    """DolarAPI - Cotizaciones dólar."""
    try:
        r = requests.get("https://dolarapi.com/v1/dolares", timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        return ("OK", f"{r.status_code} - {len(data)} cotizaciones recibidas")
    except Exception as e:
        return ("FAIL", str(e)[:80])


def test_bluelytics():
    """Bluelytics - Dólar blue/oficial."""
    try:
        r = requests.get("https://api.bluelytics.com.ar/v2/latest", timeout=TIMEOUT)
        r.raise_for_status()
        r.json()
        return ("OK", f"{r.status_code} - datos recibidos")
    except Exception as e:
        return ("FAIL", str(e)[:80])


def test_bcra():
    """API BCRA - Cotizaciones cambiarias."""
    try:
        url = "https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones"
        r = requests.get(url, timeout=TIMEOUT, verify=True)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", {})
        detalle = results.get("detalle", [])
        return ("OK", f"{r.status_code} - {len(detalle)} divisas recibidas")
    except requests.exceptions.SSLError as e:
        return ("FAIL", f"SSL error: {str(e)[:60]}")
    except Exception as e:
        return ("FAIL", str(e)[:80])


def test_bcra_macro():
    """API BCRA v4.0 - Datos macro (reservas, base monetaria, CER, BADLAR)."""
    try:
        url = "https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias/1?desde=2026-01-01&hasta=2026-12-31&limit=3"
        r = requests.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        detalle = data.get("results", [{}])[0].get("detalle", [])
        if not detalle:
            return ("FAIL", "sin datos de reservas")
        last = detalle[0]
        return ("OK", f"reservas: USD {last['valor']:,.0f}M ({last['fecha']})")
    except Exception as e:
        return ("FAIL", str(e)[:80])


def test_argentinadatos_riesgo():
    """ArgentinaDatos - Riesgo país."""
    try:
        r = requests.get(
            "https://api.argentinadatos.com/v1/finanzas/indices/riesgo-pais",
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        count = len(data) if isinstance(data, list) else "?"
        return ("OK", f"{r.status_code} - {count} registros recibidos")
    except Exception as e:
        return ("FAIL", str(e)[:80])


def test_argentinadatos_inflacion():
    """ArgentinaDatos - Inflación."""
    try:
        r = requests.get(
            "https://api.argentinadatos.com/v1/finanzas/indices/inflacion",
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        count = len(data) if isinstance(data, list) else "?"
        return ("OK", f"{r.status_code} - {count} registros recibidos")
    except Exception as e:
        return ("FAIL", str(e)[:80])


def test_rss_ambito():
    """RSS Ámbito Financiero - Noticias economía."""
    try:
        import feedparser

        d = feedparser.parse("https://www.ambito.com/rss/economia.xml")
        if d.bozo and not d.entries:
            return ("FAIL", f"error de parseo: {str(d.bozo_exception)[:60]}")
        count = len(d.entries)
        if count == 0:
            return ("FAIL", "feed vacío, 0 noticias")
        latest = d.entries[0].get("title", "?")[:50]
        return ("OK", f'{count} noticias - "{latest}..."')
    except Exception as e:
        return ("FAIL", str(e)[:80])


def test_rss_cronista():
    """RSS El Cronista - Noticias finanzas."""
    try:
        import feedparser

        d = feedparser.parse("https://www.cronista.com/files/rss/finanzas.xml")
        if d.bozo and not d.entries:
            return ("FAIL", f"error de parseo: {str(d.bozo_exception)[:60]}")
        count = len(d.entries)
        if count == 0:
            return ("FAIL", "feed vacío, 0 noticias")
        latest = d.entries[0].get("title", "?")[:50]
        return ("OK", f'{count} noticias - "{latest}..."')
    except Exception as e:
        return ("FAIL", str(e)[:80])


def test_pyobd_bonos():
    """PyOBD - Bonos soberanos AR (Open BYMA Data, 20min delay)."""
    try:
        import PyOBD

        obd = PyOBD.openBYMAdata()
        bonds = obd.get_bonds()
        if bonds.empty:
            return ("FAIL", "sin datos de bonos")
        al30 = bonds[bonds["symbol"] == "AL30"]
        if al30.empty:
            return ("OK", f"{len(bonds)} bonos (AL30 sin precio aún)")
        price = al30.iloc[0]["last"]
        return ("OK", f"{len(bonds)} bonos - AL30: ${price:,.0f}")
    except Exception as e:
        return ("FAIL", str(e)[:80])


def test_pyobd_lecaps():
    """PyOBD - Lecaps/Boncaps (Open BYMA Data, 20min delay)."""
    try:
        import PyOBD

        obd = PyOBD.openBYMAdata()
        short = obd.get_short_term_bonds()
        if short.empty:
            return ("FAIL", "sin datos de letras")
        active = short[short["last"] > 0]
        return ("OK", f"{len(short)} letras ({len(active)} con precio)")
    except Exception as e:
        return ("FAIL", str(e)[:80])


def test_rss_bloomberg():
    """RSS Bloomberg Markets - Noticias mercados globales."""
    try:
        import feedparser

        d = feedparser.parse("https://feeds.bloomberg.com/markets/news.rss")
        if d.bozo and not d.entries:
            return ("FAIL", f"error de parseo: {str(d.bozo_exception)[:60]}")
        count = len(d.entries)
        if count == 0:
            return ("FAIL", "feed vacío, 0 noticias")
        latest = d.entries[0].get("title", "?")[:50]
        return ("OK", f'{count} noticias - "{latest}..."')
    except Exception as e:
        return ("FAIL", str(e)[:80])


def test_rss_cnbc():
    """RSS CNBC Finance - Noticias finanzas US."""
    try:
        import feedparser

        d = feedparser.parse(
            "https://search.cnbc.com/rs/search/combinedcms/view.xml"
            "?partnerId=wrss01&id=10000664"
        )
        if d.bozo and not d.entries:
            return ("FAIL", f"error de parseo: {str(d.bozo_exception)[:60]}")
        count = len(d.entries)
        if count == 0:
            return ("FAIL", "feed vacío, 0 noticias")
        latest = d.entries[0].get("title", "?")[:50]
        return ("OK", f'{count} noticias - "{latest}..."')
    except Exception as e:
        return ("FAIL", str(e)[:80])


def test_rss_ft():
    """RSS Financial Times Markets."""
    try:
        import feedparser

        d = feedparser.parse("https://www.ft.com/rss/markets")
        if d.bozo and not d.entries:
            return ("FAIL", f"error de parseo: {str(d.bozo_exception)[:60]}")
        count = len(d.entries)
        if count == 0:
            return ("FAIL", "feed vacío, 0 noticias")
        latest = d.entries[0].get("title", "?")[:50]
        return ("OK", f'{count} noticias - "{latest}..."')
    except Exception as e:
        return ("FAIL", str(e)[:80])


def test_rss_infobae():
    """RSS Infobae Economía."""
    try:
        import feedparser

        d = feedparser.parse(
            "https://www.infobae.com/arc/outboundfeeds/rss/category/economia/"
        )
        if d.bozo and not d.entries:
            return ("FAIL", f"error de parseo: {str(d.bozo_exception)[:60]}")
        count = len(d.entries)
        if count == 0:
            return ("FAIL", "feed vacío, 0 noticias")
        latest = d.entries[0].get("title", "?")[:50]
        return ("OK", f'{count} noticias - "{latest}..."')
    except Exception as e:
        return ("FAIL", str(e)[:80])


def test_yfinance():
    """yfinance - CEDEARs en Yahoo Finance (AAPL.BA)."""
    try:
        import yfinance as yf

        ticker = yf.Ticker("AAPL.BA")
        hist = ticker.history(period="5d")
        if hist.empty:
            return ("FAIL", "sin datos para AAPL.BA")
        last_price = hist["Close"].iloc[-1]
        return ("OK", f"precio: ${last_price:,.0f} ARS")
    except Exception as e:
        return ("FAIL", str(e)[:80])


# --- CON API KEY ---

def test_alpha_vantage():
    """Alpha Vantage - Precio acciones US."""
    key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not key:
        return ("NO_KEY", "ALPHA_VANTAGE_API_KEY no configurada")
    try:
        r = requests.get(
            "https://www.alphavantage.co/query",
            params={"function": "GLOBAL_QUOTE", "symbol": "AAPL", "apikey": key},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        if "Global Quote" in data and data["Global Quote"]:
            price = data["Global Quote"].get("05. price", "?")
            return ("OK", f"{r.status_code} - AAPL: ${price}")
        if "Note" in data or "Information" in data:
            return ("FAIL", f"{r.status_code} - rate limit alcanzado")
        return ("FAIL", f"{r.status_code} - respuesta inesperada")
    except Exception as e:
        return ("FAIL", str(e)[:80])


def test_fmp():
    """Financial Modeling Prep - Precio + fundamentals US."""
    key = os.getenv("FMP_API_KEY")
    if not key:
        return ("NO_KEY", "FMP_API_KEY no configurada")
    try:
        r = requests.get(
            f"https://financialmodelingprep.com/api/v3/quote/AAPL?apikey={key}",
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list) and len(data) > 0:
            price = data[0].get("price", "?")
            return ("OK", f"{r.status_code} - AAPL: ${price}")
        return ("FAIL", f"{r.status_code} - respuesta vacía")
    except Exception as e:
        return ("FAIL", str(e)[:80])


def test_tavily():
    """Tavily - Búsqueda de noticias financieras."""
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        return ("NO_KEY", "TAVILY_API_KEY no configurada")
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": key, "query": "argentina economia", "max_results": 5},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        return ("OK", f"{r.status_code} - {len(results)} resultados")
    except Exception as e:
        return ("FAIL", str(e)[:80])


def test_newsapi():
    """NewsAPI - Noticias generales."""
    key = os.getenv("NEWSAPI_KEY")
    if not key:
        return ("NO_KEY", "NEWSAPI_KEY no configurada")
    try:
        r = requests.get(
            "https://newsapi.org/v2/everything",
            params={"q": "argentina", "pageSize": 5, "apiKey": key},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        total = data.get("totalResults", "?")
        return ("OK", f"{r.status_code} - {total} resultados totales")
    except Exception as e:
        return ("FAIL", str(e)[:80])


# --- MAIN ---

def main():
    gratuitas = [
        ("DolarAPI", test_dolarapi),
        ("Bluelytics", test_bluelytics),
        ("BCRA Cotizaciones", test_bcra),
        ("BCRA Macro v4", test_bcra_macro),
        ("ArgentinaDatos riesgo", test_argentinadatos_riesgo),
        ("ArgentinaDatos inflac", test_argentinadatos_inflacion),
        ("yfinance AAPL.BA", test_yfinance),
        ("BYMA Bonos", test_pyobd_bonos),
        ("BYMA Lecaps", test_pyobd_lecaps),
        ("RSS Ámbito", test_rss_ambito),
        ("RSS Cronista", test_rss_cronista),
        ("RSS Bloomberg", test_rss_bloomberg),
        ("RSS CNBC Finance", test_rss_cnbc),
        ("RSS FT Markets", test_rss_ft),
        ("RSS Infobae Economía", test_rss_infobae),
    ]

    con_key = [
        ("Alpha Vantage", test_alpha_vantage),
        ("Financial Modeling", test_fmp),
        ("Tavily", test_tavily),
        ("NewsAPI", test_newsapi),
    ]

    print("\n=== Test de Acceso a APIs ===\n")

    ok = 0
    no_key = 0
    fail = 0

    print("GRATUITAS (sin key):")
    for name, fn in gratuitas:
        status, detail = fn()
        tag = f"[{status}]"
        print(f"  {tag:<10} {name:<22} {detail}")
        if status == "OK":
            ok += 1
        elif status == "NO_KEY":
            no_key += 1
        else:
            fail += 1

    print("\nCON API KEY:")
    for name, fn in con_key:
        status, detail = fn()
        tag = f"[{status}]"
        print(f"  {tag:<10} {name:<22} {detail}")
        if status == "OK":
            ok += 1
        elif status == "NO_KEY":
            no_key += 1
        else:
            fail += 1

    total = ok + no_key + fail
    print(f"\nResumen: {ok}/{total} OK | {no_key} sin key | {fail} fallido(s)\n")


if __name__ == "__main__":
    main()
