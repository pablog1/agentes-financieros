"""
Fetcher de equity: acciones argentinas, CEDEARs, acciones US y fundamentals.
Fuente: yfinance.
"""

import logging
import time

from pipeline.config import (
    ACCIONES_AR,
    CEDEARS_TICKERS_BA,
    US_TICKERS,
    RATIOS_CEDEAR,
)

logger = logging.getLogger(__name__)


def _safe_float(val):
    if val is None:
        return None
    try:
        f = float(val)
        return None if f != f else f
    except (ValueError, TypeError):
        return None


def _safe_int(val):
    if val is None:
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def _empty_price_dict():
    return {
        "ultimo": None, "apertura": None, "maximo": None, "minimo": None,
        "volumen": None, "variacion_pct": None, "cierre_anterior": None,
        "fecha_dato": None, "fuente": "yfinance",
    }


def _parse_yf_download(df, tickers):
    """Parsear resultado de yf.download() en dict por ticker con OHLCV."""
    import pandas as pd
    result = {}

    for ticker in tickers:
        try:
            if len(tickers) == 1:
                ticker_data = df
            elif isinstance(df.columns, pd.MultiIndex):
                # yfinance >= 0.2.36 usa MultiIndex (Ticker, Price) o (Price, Ticker)
                try:
                    ticker_data = df.xs(ticker, level="Ticker", axis=1)
                except KeyError:
                    try:
                        ticker_data = df[ticker]
                    except KeyError:
                        result[ticker] = _empty_price_dict()
                        continue
            else:
                result[ticker] = _empty_price_dict()
                continue

            if ticker_data.empty:
                result[ticker] = _empty_price_dict()
                continue

            last_row = ticker_data.iloc[-1]
            prev_row = ticker_data.iloc[-2] if len(ticker_data) > 1 else None

            # Extraer fecha real del dato desde el índice del DataFrame
            fecha_dato = None
            try:
                last_index = ticker_data.index[-1]
                if hasattr(last_index, 'strftime'):
                    fecha_dato = last_index.strftime("%Y-%m-%d")
                else:
                    fecha_dato = str(last_index)[:10]
            except Exception:
                pass

            ultimo = _safe_float(last_row.get("Close"))
            cierre_anterior = _safe_float(prev_row.get("Close")) if prev_row is not None else None
            variacion_pct = None
            if ultimo and cierre_anterior and cierre_anterior > 0:
                variacion_pct = round((ultimo / cierre_anterior - 1) * 100, 2)

            result[ticker] = {
                "ultimo": ultimo,
                "apertura": _safe_float(last_row.get("Open")),
                "maximo": _safe_float(last_row.get("High")),
                "minimo": _safe_float(last_row.get("Low")),
                "volumen": _safe_int(last_row.get("Volume")),
                "variacion_pct": variacion_pct,
                "cierre_anterior": cierre_anterior,
                "fecha_dato": fecha_dato,
                "fuente": "yfinance",
            }
        except Exception as e:
            logger.warning(f"Error parseando {ticker}: {e}")
            result[ticker] = _empty_price_dict()

    return result


# --- Acciones Argentinas ---

def _fetch_acciones_ar():
    """Fetch acciones argentinas con OHLCV."""
    try:
        import yfinance as yf
        logger.info(f"Descargando {len(ACCIONES_AR)} acciones AR...")
        df = yf.download(ACCIONES_AR, period="5d", progress=False, threads=True)
        return _parse_yf_download(df, ACCIONES_AR), "ok"
    except Exception as e:
        logger.error(f"yfinance acciones AR falló: {e}")
        return {t: _empty_price_dict() for t in ACCIONES_AR}, str(e)[:100]


# --- CEDEARs en BYMA ---

def _fetch_cedears_ba():
    """Fetch CEDEARs en pesos (tickers .BA)."""
    try:
        import yfinance as yf
        logger.info(f"Descargando {len(CEDEARS_TICKERS_BA)} CEDEARs...")
        df = yf.download(CEDEARS_TICKERS_BA, period="5d", progress=False, threads=True)
        return _parse_yf_download(df, CEDEARS_TICKERS_BA), "ok"
    except Exception as e:
        logger.error(f"yfinance CEDEARs falló: {e}")
        return {t: _empty_price_dict() for t in CEDEARS_TICKERS_BA}, str(e)[:100]


# --- Acciones US ---

def _fetch_us_prices():
    """Fetch precios de acciones US (subyacentes de CEDEARs)."""
    try:
        import yfinance as yf
        logger.info(f"Descargando {len(US_TICKERS)} acciones US...")
        df = yf.download(US_TICKERS, period="5d", progress=False, threads=True)
        return _parse_yf_download(df, US_TICKERS), "ok"
    except Exception as e:
        logger.error(f"yfinance US falló: {e}")
        return {t: _empty_price_dict() for t in US_TICKERS}, str(e)[:100]


# --- Fundamentals ---

def _fetch_fundamentals(ticker):
    """Fetch fundamentals de un ticker US vía yfinance."""
    try:
        import yfinance as yf
        info = yf.Ticker(ticker).info
        return {
            "pe_ratio": _safe_float(info.get("trailingPE")),
            "forward_pe": _safe_float(info.get("forwardPE")),
            "pb_ratio": _safe_float(info.get("priceToBook")),
            "eps": _safe_float(info.get("trailingEps")),
            "dividend_yield": _safe_float(info.get("dividendYield")),
            "market_cap": _safe_int(info.get("marketCap")),
            "market_cap_fmt": _format_market_cap(info.get("marketCap")),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
        }
    except Exception as e:
        logger.warning(f"Fundamentals de {ticker} falló: {e}")
        return {
            "pe_ratio": None, "forward_pe": None, "pb_ratio": None,
            "eps": None, "dividend_yield": None, "market_cap": None,
            "market_cap_fmt": None, "sector": None, "industry": None,
        }


def _format_market_cap(value):
    """Formatear market cap: 3500000000000 → '3.5T'."""
    if not value:
        return None
    v = float(value)
    if v >= 1e12:
        return f"{v/1e12:.1f}T"
    if v >= 1e9:
        return f"{v/1e9:.1f}B"
    if v >= 1e6:
        return f"{v/1e6:.1f}M"
    return str(int(v))


# --- Composición CEDEAR ---

def _compose_cedear(ticker_us, cedear_data, us_data, fundamentals, ccl_venta):
    """Componer un CEDEAR uniendo datos AR, US y fundamentals."""
    ratio = RATIOS_CEDEAR.get(ticker_us, 1)
    precio_us = us_data.get("ultimo")
    precio_cedear = cedear_data.get("ultimo")

    precio_teorico = None
    prima_descuento = None
    if precio_us and ccl_venta and ratio:
        precio_teorico = round((precio_us / ratio) * ccl_venta, 2)
        if precio_cedear and precio_teorico > 0:
            prima_descuento = round((precio_cedear / precio_teorico - 1) * 100, 2)

    return {
        "cedear_ticker": f"{ticker_us}.BA",
        "precio_cedear_ars": precio_cedear,
        "volumen_cedear": cedear_data.get("volumen"),
        "variacion_pct_cedear": cedear_data.get("variacion_pct"),
        "precio_us": precio_us,
        "variacion_pct_us": us_data.get("variacion_pct"),
        "ratio": ratio,
        "precio_teorico_ars": precio_teorico,
        "prima_descuento_pct": prima_descuento,
        "fundamentals": fundamentals,
        "fuente": "yfinance",
    }


# --- Función pública ---

def fetch_equity(dolar_ccl_venta):
    """
    Fetch todos los datos de equity.
    Requiere dolar_ccl_venta para calcular precio teórico de CEDEARs.
    Retorna (equity_ar_dict, cedears_dict, status_str).
    """
    # Descargas batch
    acciones_ar, ar_status = _fetch_acciones_ar()
    cedears_ba, ced_status = _fetch_cedears_ba()
    us_prices, us_status = _fetch_us_prices()

    # Fundamentals (individual por ticker, con pausa)
    logger.info(f"Fetching fundamentals de {len(US_TICKERS)} tickers US...")
    fundamentals = {}
    for ticker in US_TICKERS:
        fundamentals[ticker] = _fetch_fundamentals(ticker)
        time.sleep(0.5)

    # Componer CEDEARs
    cedears = {}
    for ticker_us in US_TICKERS:
        ticker_ba = f"{ticker_us}.BA"
        cedear_data = cedears_ba.get(ticker_ba, _empty_price_dict())
        us_data = us_prices.get(ticker_us, _empty_price_dict())
        fund = fundamentals.get(ticker_us, {})
        cedears[ticker_us] = _compose_cedear(
            ticker_us, cedear_data, us_data, fund, dolar_ccl_venta
        )

    # Equity AR con nombres
    equity_ar = {"acciones": {}}
    nombres_ar = {
        "GGAL.BA": "Grupo Financiero Galicia",
        "YPFD.BA": "YPF S.A.",
        "PAMP.BA": "Pampa Energía",
        "BBAR.BA": "Banco BBVA Argentina",
        "CEPU.BA": "Central Puerto",
        "TXAR.BA": "Ternium Argentina",
        "TGSU2.BA": "Transportadora de Gas del Sur",
        "LOMA.BA": "Loma Negra",
        "CRES.BA": "Cresud",
        "ALUA.BA": "Aluar",
    }
    for ticker in ACCIONES_AR:
        data = acciones_ar.get(ticker, _empty_price_dict())
        data["nombre"] = nombres_ar.get(ticker, ticker)
        equity_ar["acciones"][ticker] = data

    # Status general
    statuses = [ar_status, ced_status, us_status]
    if all(s == "ok" for s in statuses):
        status = "ok"
    elif any(s == "ok" for s in statuses):
        status = "parcial"
    else:
        status = "error"

    return equity_ar, cedears, status
