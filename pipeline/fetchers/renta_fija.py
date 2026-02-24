"""
Fetcher de renta fija.
Fuentes: PyOBD (bonos, lecaps, ONs), ArgentinaDatos (tasas plazo fijo).
"""

import logging
import requests

from pipeline.config import (
    REQUEST_TIMEOUT,
    BONOS_CLAVE,
    ARGDATOS_PLAZO_FIJO,
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


# --- Bonos Soberanos ---

def _fetch_bonos_soberanos():
    """Fetch bonos soberanos de PyOBD (Open BYMA Data)."""
    try:
        import PyOBD
        obd = PyOBD.openBYMAdata()
        bonds_df = obd.get_bonds()
        if bonds_df.empty:
            return [], "sin datos"

        bonos = []
        for _, row in bonds_df.iterrows():
            bonos.append({
                "ticker": row.get("symbol", ""),
                "nombre": row.get("description", ""),
                "ultimo": _safe_float(row.get("last")),
                "variacion_pct": _safe_float(row.get("change")),
                "volumen": _safe_int(row.get("volume")),
                "bid": _safe_float(row.get("bid")),
                "ask": _safe_float(row.get("ask")),
                "vencimiento": str(row.get("maturityDate", "")) if row.get("maturityDate") else None,
                "moneda": "ARS",
                "fuente": "PyOBD",
            })
        return bonos, "ok"
    except Exception as e:
        logger.error(f"PyOBD bonos falló: {e}")
        return [], str(e)[:100]


def _extract_bonos_clave(bonos):
    """Extraer bonos clave del listado completo."""
    clave = {}
    bonos_por_ticker = {b["ticker"]: b for b in bonos if b.get("ticker")}
    for ticker in BONOS_CLAVE:
        bono = bonos_por_ticker.get(ticker, {})
        clave[ticker] = {
            "ultimo": bono.get("ultimo"),
            "variacion_pct": bono.get("variacion_pct"),
        }
    return clave


# --- Lecaps / Boncaps ---

def _fetch_lecaps():
    """Fetch Lecaps/Boncaps de PyOBD."""
    try:
        import PyOBD
        obd = PyOBD.openBYMAdata()
        short_df = obd.get_short_term_bonds()
        if short_df.empty:
            return [], "sin datos"

        lecaps = []
        for _, row in short_df.iterrows():
            lecaps.append({
                "ticker": row.get("symbol", ""),
                "ultimo": _safe_float(row.get("last")),
                "variacion_pct": _safe_float(row.get("change")),
                "volumen": _safe_int(row.get("volume")),
                "vencimiento": str(row.get("maturityDate", "")) if row.get("maturityDate") else None,
                "fuente": "PyOBD",
            })
        return lecaps, "ok"
    except Exception as e:
        logger.error(f"PyOBD lecaps falló: {e}")
        return [], str(e)[:100]


# --- Obligaciones Negociables ---

def _fetch_ons():
    """Fetch ONs de PyOBD (corporateBonds), filtrado top 50 por volumen."""
    try:
        import PyOBD
        obd = PyOBD.openBYMAdata()
        ons_df = obd.get_corporateBonds()
        if ons_df.empty:
            return [], "sin datos"

        # Filtrar solo las que tienen precio activo
        if "last" in ons_df.columns:
            active = ons_df[ons_df["last"] > 0].copy()
        else:
            active = ons_df.copy()

        # Ordenar por volumen y tomar top 50
        if "volume" in active.columns:
            active = active.sort_values("volume", ascending=False).head(50)

        ons = []
        for _, row in active.iterrows():
            ons.append({
                "ticker": row.get("symbol", ""),
                "emisor": row.get("description", ""),
                "ultimo": _safe_float(row.get("last")),
                "variacion_pct": _safe_float(row.get("change")),
                "volumen": _safe_int(row.get("volume")),
                "moneda": "ARS",
                "fuente": "PyOBD",
            })
        return ons, "ok"
    except Exception as e:
        logger.error(f"PyOBD ONs falló: {e}")
        return [], str(e)[:100]


# --- Tasas plazo fijo ---

def _fetch_tasas_plazo_fijo():
    """Fetch tasas de plazo fijo de ArgentinaDatos."""
    try:
        r = requests.get(ARGDATOS_PLAZO_FIJO, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        return [
            {
                "entidad": t.get("entidad", ""),
                "tna_clientes": _safe_float(t.get("tnaClientes")),
                "tna_no_clientes": _safe_float(t.get("tnaNoClientes")),
            }
            for t in data
        ]
    except Exception as e:
        logger.warning(f"Tasas plazo fijo falló: {e}")
        return []


# --- Función pública ---

def fetch_renta_fija():
    """Fetch todos los datos de renta fija. Retorna (data_dict, status_str)."""
    logger.info("Fetching bonos soberanos...")
    bonos, bonos_status = _fetch_bonos_soberanos()
    bonos_clave = _extract_bonos_clave(bonos)

    logger.info("Fetching lecaps/boncaps...")
    lecaps, lecaps_status = _fetch_lecaps()

    logger.info("Fetching obligaciones negociables...")
    ons, ons_status = _fetch_ons()

    logger.info("Fetching tasas plazo fijo...")
    tasas = _fetch_tasas_plazo_fijo()

    # Determinar status general
    if bonos_status == "ok":
        status = "ok"
    elif lecaps_status == "ok":
        status = "parcial"
    else:
        status = "error"

    data = {
        "bonos_soberanos": bonos,
        "bonos_clave": bonos_clave,
        "lecaps_boncaps": lecaps,
        "obligaciones_negociables": ons,
        "tasas_plazo_fijo": tasas,
    }

    return data, status
