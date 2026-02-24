"""
Fetcher de datos macroeconómicos.
Fuentes: DolarAPI, Bluelytics, BCRA v4, ArgentinaDatos.
"""

import logging
import requests
from datetime import date

from pipeline.config import (
    REQUEST_TIMEOUT,
    DOLARAPI_ALL,
    BLUELYTICS_URL,
    BCRA_COTIZACIONES,
    BCRA_MACRO_BASE,
    BCRA_VARIABLES,
    ARGDATOS_RIESGO_PAIS_ULTIMO,
    ARGDATOS_INFLACION,
    ARGDATOS_INFLACION_INTERANUAL,
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


# --- Dólar ---

def _fetch_dolar_all():
    """Fetch 7 tipos de dólar de DolarAPI, fallback a Bluelytics."""
    try:
        r = requests.get(DOLARAPI_ALL, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        result = {}
        for cotiz in data:
            casa = cotiz.get("casa", "").lower()
            # Normalizar nombres
            key_map = {
                "oficial": "oficial",
                "blue": "blue",
                "bolsa": "mep",
                "contadoconliqui": "ccl",
                "mayorista": "mayorista",
                "cripto": "cripto",
                "tarjeta": "tarjeta",
            }
            key = key_map.get(casa, casa)
            result[key] = {
                "compra": _safe_float(cotiz.get("compra")),
                "venta": _safe_float(cotiz.get("venta")),
                "fecha_actualizacion": cotiz.get("fechaActualizacion"),
            }
        return result, "ok"
    except Exception as e:
        logger.warning(f"DolarAPI falló: {e}. Intentando Bluelytics...")

    try:
        r = requests.get(BLUELYTICS_URL, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        result = {
            "oficial": {
                "compra": _safe_float(data["oficial"]["value_buy"]),
                "venta": _safe_float(data["oficial"]["value_sell"]),
                "fecha_actualizacion": data.get("last_update"),
            },
            "blue": {
                "compra": _safe_float(data["blue"]["value_buy"]),
                "venta": _safe_float(data["blue"]["value_sell"]),
                "fecha_actualizacion": data.get("last_update"),
            },
        }
        return result, "ok (bluelytics fallback, solo oficial+blue)"
    except Exception as e:
        logger.error(f"Bluelytics también falló: {e}")
        return {}, "error"


def _fetch_euro():
    """Fetch EUR oficial/blue de Bluelytics."""
    try:
        r = requests.get(BLUELYTICS_URL, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        return {
            "oficial": {
                "compra": _safe_float(data.get("oficial_euro", {}).get("value_buy")),
                "venta": _safe_float(data.get("oficial_euro", {}).get("value_sell")),
            },
            "blue": {
                "compra": _safe_float(data.get("blue_euro", {}).get("value_buy")),
                "venta": _safe_float(data.get("blue_euro", {}).get("value_sell")),
            },
        }
    except Exception as e:
        logger.warning(f"Bluelytics euro falló: {e}")
        return {"oficial": {"compra": None, "venta": None}, "blue": {"compra": None, "venta": None}}


# --- Riesgo País ---

def _fetch_riesgo_pais():
    """Fetch riesgo país de ArgentinaDatos."""
    try:
        r = requests.get(ARGDATOS_RIESGO_PAIS_ULTIMO, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        return {
            "valor": data.get("valor"),
            "fecha": data.get("fecha"),
            "fuente": "ArgentinaDatos",
        }
    except Exception as e:
        logger.warning(f"Riesgo país falló: {e}")
        return {"valor": None, "fecha": None, "fuente": "error"}


# --- Inflación ---

def _fetch_inflacion():
    """Fetch inflación mensual + interanual de ArgentinaDatos."""
    result = {
        "mensual_ultimo": {"valor": None, "fecha": None},
        "interanual_ultimo": {"valor": None, "fecha": None},
        "serie_12m": [],
    }

    # Mensual
    try:
        r = requests.get(ARGDATOS_INFLACION, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        if data:
            ultimo = data[-1]
            result["mensual_ultimo"] = {
                "valor": _safe_float(ultimo.get("valor")),
                "fecha": ultimo.get("fecha"),
            }
            result["serie_12m"] = [
                {"fecha": d.get("fecha"), "valor": _safe_float(d.get("valor"))}
                for d in data[-12:]
            ]
    except Exception as e:
        logger.warning(f"Inflación mensual falló: {e}")

    # Interanual
    try:
        r = requests.get(ARGDATOS_INFLACION_INTERANUAL, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        if data:
            ultimo = data[-1]
            result["interanual_ultimo"] = {
                "valor": _safe_float(ultimo.get("valor")),
                "fecha": ultimo.get("fecha"),
            }
    except Exception as e:
        logger.warning(f"Inflación interanual falló: {e}")

    return result


# --- Tasas plazo fijo ---

def _fetch_tasas_plazo_fijo():
    """Fetch tasas de plazo fijo por entidad de ArgentinaDatos."""
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


# --- BCRA Variables ---

def _fetch_bcra_variable(var_id, var_name):
    """Fetch una variable BCRA macro por ID."""
    try:
        year = date.today().year
        url = f"{BCRA_MACRO_BASE}/{var_id}"
        params = {"desde": f"{year}-01-01", "hasta": f"{year}-12-31", "limit": 3}
        r = requests.get(url, timeout=REQUEST_TIMEOUT, params=params)
        r.raise_for_status()
        data = r.json()
        detalle = data.get("results", [{}])[0].get("detalle", [])
        if detalle:
            last = detalle[0]
            return {"valor": _safe_float(last["valor"]), "fecha": last["fecha"]}
        return {"valor": None, "fecha": None, "nota": f"sin datos para {var_name}"}
    except Exception as e:
        logger.warning(f"BCRA {var_name} (ID {var_id}) falló: {e}")
        return {"valor": None, "fecha": None, "nota": str(e)[:100]}


def _fetch_bcra_macro():
    """Fetch todas las variables BCRA macro."""
    result = {}
    for var_name, var_id in BCRA_VARIABLES.items():
        result[var_name] = _fetch_bcra_variable(var_id, var_name)
    return result


# --- Divisas BCRA ---

def _fetch_divisas_bcra():
    """Fetch cotizaciones de divisas del BCRA (39 monedas)."""
    try:
        r = requests.get(BCRA_COTIZACIONES, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        detalle = data.get("results", {}).get("detalle", [])
        return [
            {
                "codigo": d.get("codigoMoneda"),
                "descripcion": d.get("descripcion"),
                "tipo_cotizacion": _safe_float(d.get("tipoCotizacion")),
            }
            for d in detalle
        ]
    except Exception as e:
        logger.warning(f"BCRA divisas falló: {e}")
        return []


# --- Brechas calculadas ---

def _calcular_brechas(dolar):
    """Calcular brechas cambiarias."""
    oficial_venta = (dolar.get("oficial") or {}).get("venta")
    blue_venta = (dolar.get("blue") or {}).get("venta")
    mep_venta = (dolar.get("mep") or {}).get("venta")
    ccl_venta = (dolar.get("ccl") or {}).get("venta")

    def _brecha(a, b):
        if a and b and b > 0:
            return round((a / b - 1) * 100, 2)
        return None

    return {
        "blue_oficial_pct": _brecha(blue_venta, oficial_venta),
        "mep_oficial_pct": _brecha(mep_venta, oficial_venta),
        "ccl_oficial_pct": _brecha(ccl_venta, oficial_venta),
        "ccl_mep_pct": _brecha(ccl_venta, mep_venta),
    }


# --- Función pública ---

def fetch_macro():
    """Fetch todos los datos macroeconómicos. Retorna (data_dict, status_dict)."""
    status = {}
    errores = []

    logger.info("Fetching dólar...")
    dolar, dolar_status = _fetch_dolar_all()
    status["dolarapi"] = {"status": dolar_status}

    logger.info("Fetching euro...")
    euro = _fetch_euro()
    status["bluelytics"] = {"status": "ok" if euro["oficial"]["venta"] else "error"}

    logger.info("Fetching riesgo país...")
    riesgo_pais = _fetch_riesgo_pais()
    if riesgo_pais["valor"] is None:
        errores.append("riesgo_pais: sin datos")

    logger.info("Fetching inflación...")
    inflacion = _fetch_inflacion()

    logger.info("Fetching tasas plazo fijo...")
    tasas_pf = _fetch_tasas_plazo_fijo()

    logger.info("Fetching BCRA macro variables...")
    bcra = _fetch_bcra_macro()
    status["bcra_macro"] = {"status": "ok" if bcra.get("reservas", {}).get("valor") else "parcial"}

    logger.info("Fetching divisas BCRA...")
    divisas = _fetch_divisas_bcra()
    status["bcra_cotizaciones"] = {"status": "ok" if divisas else "error"}

    logger.info("Fetching tasas BCRA (BADLAR)...")
    badlar = bcra.pop("badlar", {"valor": None, "fecha": None})

    # Armar resultado
    brechas = _calcular_brechas(dolar)

    # Agregar unidades a BCRA
    bcra_formateado = {}
    if "reservas" in bcra:
        bcra_formateado["reservas"] = {**bcra["reservas"], "unidad": "millones_usd"}
    if "base_monetaria" in bcra:
        bcra_formateado["base_monetaria"] = {**bcra["base_monetaria"], "unidad": "millones_ars"}
    for key in ["cer", "tc_minorista", "tc_mayorista"]:
        if key in bcra:
            bcra_formateado[key] = bcra[key]

    status["argentinadatos"] = {"status": "ok" if riesgo_pais["valor"] else "error"}

    macro_data = {
        "dolar": dolar,
        "brechas": brechas,
        "euro": euro,
        "riesgo_pais": riesgo_pais,
        "inflacion": inflacion,
        "tasas": {
            "plazo_fijo": tasas_pf,
            "badlar": badlar,
        },
        "bcra": bcra_formateado,
        "divisas_bcra": divisas,
    }

    return macro_data, status
