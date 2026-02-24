"""
Fetcher de índices, commodities y crypto.
Fuente: yfinance.
"""

import logging

from pipeline.config import INDICES, COMMODITIES, CRYPTO

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


def _parse_single_ticker(df, ticker):
    """Parsear datos OHLCV de un solo ticker del DataFrame."""
    import pandas as pd
    try:
        if isinstance(df.columns, pd.MultiIndex):
            try:
                ticker_data = df.xs(ticker, level="Ticker", axis=1)
            except KeyError:
                try:
                    ticker_data = df[ticker]
                except KeyError:
                    return None
        else:
            ticker_data = df

        if ticker_data.empty:
            return None

        last_row = ticker_data.iloc[-1]
        prev_row = ticker_data.iloc[-2] if len(ticker_data) > 1 else None

        # Extraer la fecha real del dato desde el índice del DataFrame
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

        return {
            "ultimo": ultimo,
            "apertura": _safe_float(last_row.get("Open")),
            "maximo": _safe_float(last_row.get("High")),
            "minimo": _safe_float(last_row.get("Low")),
            "volumen": _safe_int(last_row.get("Volume")),
            "variacion_pct": variacion_pct,
            "fecha_dato": fecha_dato,
        }
    except Exception as e:
        logger.warning(f"Error parseando {ticker}: {e}")
        return None


# --- Índices ---

def _fetch_indices():
    """Fetch índices de mercado (MERVAL, S&P 500, Nasdaq, Dow Jones)."""
    try:
        import yfinance as yf
        tickers = list(INDICES.values())
        logger.info(f"Descargando {len(tickers)} índices...")
        df = yf.download(tickers, period="5d", progress=False, threads=True)

        result = {}
        for name, ticker in INDICES.items():
            parsed = _parse_single_ticker(df, ticker)
            result[name] = {
                "ticker": ticker,
                "ultimo": parsed["ultimo"] if parsed else None,
                "apertura": parsed["apertura"] if parsed else None,
                "maximo": parsed["maximo"] if parsed else None,
                "minimo": parsed["minimo"] if parsed else None,
                "variacion_pct": parsed["variacion_pct"] if parsed else None,
                "volumen": parsed["volumen"] if parsed else None,
                "fecha_dato": parsed["fecha_dato"] if parsed else None,
                "fuente": "yfinance",
            }
        return result, "ok"
    except Exception as e:
        logger.error(f"yfinance índices falló: {e}")
        result = {}
        for name, ticker in INDICES.items():
            result[name] = {
                "ticker": ticker, "ultimo": None, "apertura": None,
                "maximo": None, "minimo": None, "variacion_pct": None,
                "volumen": None, "fuente": "yfinance",
            }
        return result, str(e)[:100]


# --- Commodities ---

def _fetch_commodities():
    """Fetch commodities (soja, maíz, trigo, petróleo, oro)."""
    try:
        import yfinance as yf
        tickers = [c["ticker"] for c in COMMODITIES.values()]
        logger.info(f"Descargando {len(tickers)} commodities...")
        df = yf.download(tickers, period="5d", progress=False, threads=True)

        result = {}
        for name, config in COMMODITIES.items():
            ticker = config["ticker"]
            parsed = _parse_single_ticker(df, ticker)
            result[name] = {
                "ticker": ticker,
                "ultimo": parsed["ultimo"] if parsed else None,
                "variacion_pct": parsed["variacion_pct"] if parsed else None,
                "fecha_dato": parsed["fecha_dato"] if parsed else None,
                "unidad": config["unidad"],
                "fuente": "yfinance",
            }
        return result, "ok"
    except Exception as e:
        logger.error(f"yfinance commodities falló: {e}")
        result = {}
        for name, config in COMMODITIES.items():
            result[name] = {
                "ticker": config["ticker"], "ultimo": None,
                "variacion_pct": None, "unidad": config["unidad"],
                "fuente": "yfinance",
            }
        return result, str(e)[:100]


# --- Crypto ---

def _fetch_crypto():
    """Fetch crypto con variación 24h y 7d."""
    try:
        import yfinance as yf
        tickers = list(CRYPTO.values())
        logger.info(f"Descargando {len(tickers)} cryptos (7d)...")
        df = yf.download(tickers, period="7d", progress=False, threads=True)

        result = {}
        for name, ticker in CRYPTO.items():
            try:
                import pandas as pd
                if isinstance(df.columns, pd.MultiIndex):
                    try:
                        ticker_data = df.xs(ticker, level="Ticker", axis=1)
                    except KeyError:
                        try:
                            ticker_data = df[ticker]
                        except KeyError:
                            result[name] = _empty_crypto(ticker)
                            continue
                else:
                    ticker_data = df

                if ticker_data.empty:
                    result[name] = _empty_crypto(ticker)
                    continue

                last_row = ticker_data.iloc[-1]
                prev_row = ticker_data.iloc[-2] if len(ticker_data) > 1 else None
                first_row = ticker_data.iloc[0]

                # Extraer fecha real del dato
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
                precio_7d = _safe_float(first_row.get("Close"))

                variacion_pct = None
                if ultimo and cierre_anterior and cierre_anterior > 0:
                    variacion_pct = round((ultimo / cierre_anterior - 1) * 100, 2)

                variacion_7d = None
                if ultimo and precio_7d and precio_7d > 0:
                    variacion_7d = round((ultimo / precio_7d - 1) * 100, 2)

                result[name] = {
                    "ticker": ticker,
                    "ultimo": ultimo,
                    "variacion_pct": variacion_pct,
                    "variacion_7d_pct": variacion_7d,
                    "maximo_24h": _safe_float(last_row.get("High")),
                    "minimo_24h": _safe_float(last_row.get("Low")),
                    "volumen_24h": _safe_int(last_row.get("Volume")),
                    "fecha_dato": fecha_dato,
                    "fuente": "yfinance",
                }
            except Exception as e:
                logger.warning(f"Error parseando crypto {name}: {e}")
                result[name] = _empty_crypto(ticker)

        return result, "ok"
    except Exception as e:
        logger.error(f"yfinance crypto falló: {e}")
        result = {name: _empty_crypto(ticker) for name, ticker in CRYPTO.items()}
        return result, str(e)[:100]


def _empty_crypto(ticker):
    return {
        "ticker": ticker, "ultimo": None, "variacion_pct": None,
        "variacion_7d_pct": None, "maximo_24h": None, "minimo_24h": None,
        "volumen_24h": None, "fecha_dato": None, "fuente": "yfinance",
    }


# --- Función pública ---

def fetch_indices_commodities_crypto():
    """
    Fetch índices, commodities y crypto.
    Retorna (indices_dict, commodities_dict, crypto_dict, status_str).
    """
    indices, idx_status = _fetch_indices()
    commodities, cmd_status = _fetch_commodities()
    crypto, cry_status = _fetch_crypto()

    statuses = [idx_status, cmd_status, cry_status]
    if all(s == "ok" for s in statuses):
        status = "ok"
    elif any(s == "ok" for s in statuses):
        status = "parcial"
    else:
        status = "error"

    return indices, commodities, crypto, status
