"""
Generador de reportes de agentes financieros vía OpenRouter.
Uso: python3 agentes/generar_reporte.py [--agente manu] [--datos output/datos_diarios_2026-02-24.json]
"""

import argparse
import glob
import json
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")
REPORTES_DIR = os.path.join(os.path.dirname(__file__), "reportes")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def _fmt(val, decimals=0, prefix="", suffix=""):
    """Formatear número al estilo argentino (punto miles, coma decimales)."""
    if val is None:
        return None
    try:
        v = float(val)
        if decimals == 0:
            formatted = f"{v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            formatted = f"{v:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{prefix}{formatted}{suffix}"
    except (ValueError, TypeError):
        return None


def _pct(val):
    """Formatear porcentaje."""
    if val is None:
        return None
    return f"{float(val):+.1f}%".replace(".", ",")


def _detectar_fechas(data, fecha_pipeline):
    """Detectar las fechas reales de cada categoría de datos y alertar si difieren."""
    fechas = {}
    indices = data.get("indices", {})
    commodities = data.get("commodities", {})

    # Buscar fecha_dato en índices (tomar la primera disponible como representativa)
    for name, idx_data in indices.items():
        fd = idx_data.get("fecha_dato")
        if fd and fd != fecha_pipeline:
            fechas["Índices bursátiles"] = fd
            break

    # Buscar en commodities
    for name, cmd_data in commodities.items():
        fd = cmd_data.get("fecha_dato")
        if fd and fd != fecha_pipeline:
            fechas["Commodities"] = fd
            break

    # Riesgo país
    rp_fecha = data.get("macro", {}).get("riesgo_pais", {}).get("fecha")
    if rp_fecha and rp_fecha != fecha_pipeline:
        fechas["Riesgo país"] = rp_fecha

    # Dólar (fecha de actualización)
    dolar = data.get("macro", {}).get("dolar", {})
    for tipo, d in dolar.items():
        fa = d.get("fecha_actualizacion", "")
        if fa and fa[:10] != fecha_pipeline:
            fechas[f"Dólar {tipo}"] = fa[:10]

    return fechas


def _build_manu_user_message(data):
    """Construir el user message para Manu con datos relevantes del JSON."""
    fecha = data.get("metadata", {}).get("fecha", "?")
    macro = data.get("macro", {})
    dolar = macro.get("dolar", {})
    brechas = macro.get("brechas", {})
    inflacion = macro.get("inflacion", {})
    bcra = macro.get("bcra", {})
    indices = data.get("indices", {})
    commodities = data.get("commodities", {})
    crypto = data.get("crypto", {})
    calculados = data.get("calculados", {})
    noticias = data.get("noticias", {})

    lines = [f"# Datos del día — {fecha}"]

    # Detectar fechas de los datos para advertir sobre desfasajes
    fechas_datos = _detectar_fechas(data, fecha)
    if fechas_datos:
        lines.append("")
        lines.append("## ⚠ NOTA SOBRE FECHAS DE LOS DATOS")
        lines.append(f"El pipeline corrió el {fecha}, pero los datos pueden corresponder a distintas fechas de rueda:")
        for categoria, fecha_d in fechas_datos.items():
            lines.append(f"- {categoria}: datos del {fecha_d}")
        lines.append("- Asegurate de referirte correctamente a las fechas de los datos. Si un índice cerró el viernes, decí 'el viernes' no 'hoy'.")
        lines.append("- Si hay diferencia entre la fecha del pipeline y la fecha del dato, mencionalo.")

    lines.append("")

    # Dólar
    lines.append("## Dólar")
    dolar_tipos = [
        ("Oficial", "oficial"),
        ("Blue", "blue"),
        ("MEP (Bolsa)", "mep"),
        ("CCL (Contado con Liqui)", "ccl"),
        ("Mayorista", "mayorista"),
        ("Cripto", "cripto"),
        ("Tarjeta", "tarjeta"),
    ]
    for nombre, key in dolar_tipos:
        d = dolar.get(key, {})
        compra = _fmt(d.get("compra"), prefix="$")
        venta = _fmt(d.get("venta"), prefix="$")
        if compra and venta:
            lines.append(f"- {nombre}: {compra} compra / {venta} venta")

    lines.append("")
    lines.append("## Brechas cambiarias")
    brecha_items = [
        ("Blue vs Oficial", "blue_oficial_pct"),
        ("MEP vs Oficial", "mep_oficial_pct"),
        ("CCL vs Oficial", "ccl_oficial_pct"),
        ("CCL vs MEP", "ccl_mep_pct"),
    ]
    for nombre, key in brecha_items:
        val = brechas.get(key)
        if val is not None:
            lines.append(f"- {nombre}: {_fmt(val, 1)}%")

    # Euro
    euro = macro.get("euro", {})
    if euro.get("oficial", {}).get("venta") or euro.get("blue", {}).get("venta"):
        lines.append("")
        lines.append("## Euro")
        for tipo, datos in euro.items():
            venta = _fmt(datos.get("venta"), prefix="$")
            if venta:
                lines.append(f"- Euro {tipo}: {venta} venta")

    # Macro
    lines.append("")
    lines.append("## Indicadores Macro Argentina")

    rp = macro.get("riesgo_pais", {})
    if rp.get("valor"):
        lines.append(f"- Riesgo país: {rp['valor']} puntos (fecha dato: {rp.get('fecha', '?')})")

    infl_m = inflacion.get("mensual_ultimo", {})
    if infl_m.get("valor") is not None:
        lines.append(f"- Inflación mensual: {_fmt(infl_m['valor'], 1)}% ({infl_m.get('fecha', '?')})")

    infl_ia = inflacion.get("interanual_ultimo", {})
    if infl_ia.get("valor") is not None:
        lines.append(f"- Inflación interanual: {_fmt(infl_ia['valor'], 1)}%")

    infl_anual = calculados.get("inflacion_anualizada_pct")
    if infl_anual is not None:
        lines.append(f"- Inflación anualizada (compuesta desde último mes): {_fmt(infl_anual, 1)}%")

    # Serie 12m de inflación
    serie = inflacion.get("serie_12m", [])
    if serie:
        vals = [_fmt(s["valor"], 1) + "%" for s in serie if s.get("valor") is not None]
        lines.append(f"- Serie inflación últimos 12 meses: {', '.join(vals)}")

    if bcra.get("reservas", {}).get("valor") is not None:
        lines.append(f"- Reservas internacionales BCRA: USD {_fmt(bcra['reservas']['valor'])} millones ({bcra['reservas'].get('fecha', '?')})")

    if bcra.get("base_monetaria", {}).get("valor") is not None:
        lines.append(f"- Base monetaria: ${_fmt(bcra['base_monetaria']['valor'])} millones ARS ({bcra['base_monetaria'].get('fecha', '?')})")

    tasas = macro.get("tasas", {})
    badlar = tasas.get("badlar", {})
    if badlar.get("valor") is not None:
        lines.append(f"- Tasa BADLAR: {_fmt(badlar['valor'], 2)}% TNA ({badlar.get('fecha', '?')})")

    if bcra.get("cer", {}).get("valor") is not None:
        lines.append(f"- CER: {_fmt(bcra['cer']['valor'], 2)} ({bcra['cer'].get('fecha', '?')})")

    tasa_real = calculados.get("tasa_real_plazo_fijo_pct")
    if tasa_real is not None:
        lines.append(f"- Tasa real plazo fijo (promedio TNA - inflación anualizada): {_fmt(tasa_real, 1)}%")

    # Índices
    lines.append("")
    lines.append("## Índices Globales")
    for name, idx_data in indices.items():
        ultimo = idx_data.get("ultimo")
        var = idx_data.get("variacion_pct")
        fd = idx_data.get("fecha_dato")
        if ultimo:
            fecha_str = f" [dato del {fd}]" if fd else ""
            lines.append(f"- {name}: {_fmt(ultimo)} ({_pct(var) or 'sin var'}){fecha_str}")

    merval_usd = calculados.get("merval_usd_ccl")
    if merval_usd:
        lines.append(f"- MERVAL en USD (vía CCL): {_fmt(merval_usd, 0)}")

    # Commodities
    lines.append("")
    lines.append("## Commodities")
    for name, cmd_data in commodities.items():
        ultimo = cmd_data.get("ultimo")
        var = cmd_data.get("variacion_pct")
        unidad = cmd_data.get("unidad", "")
        fd = cmd_data.get("fecha_dato")
        if ultimo:
            fecha_str = f" [dato del {fd}]" if fd else ""
            lines.append(f"- {name.replace('_', ' ').title()}: ${_fmt(ultimo, 2)}/{unidad.split('/')[-1]} ({_pct(var) or 'sin var'}){fecha_str}")

    # Crypto
    lines.append("")
    lines.append("## Crypto (referencia)")
    for name, cry_data in crypto.items():
        ultimo = cry_data.get("ultimo")
        var = cry_data.get("variacion_pct")
        var7 = cry_data.get("variacion_7d_pct")
        fd = cry_data.get("fecha_dato")
        if ultimo:
            fecha_str = f" [dato del {fd}]" if fd else ""
            lines.append(f"- {name}: USD {_fmt(ultimo)} (24h: {_pct(var) or '?'}, 7d: {_pct(var7) or '?'}){fecha_str}")

    # Noticias
    lines.append("")
    lines.append("## Noticias Argentina (últimas)")
    for i, n in enumerate(noticias.get("argentina", [])[:10], 1):
        titulo = n.get("titulo", "?")
        fuente = n.get("fuente", "?")
        lines.append(f"{i}. {titulo} — {fuente}")

    lines.append("")
    lines.append("## Noticias Internacionales (relevantes para Argentina)")
    for i, n in enumerate(noticias.get("internacionales", [])[:10], 1):
        titulo = n.get("titulo", "?")
        fuente = n.get("fuente", "?")
        lines.append(f"{i}. {titulo} — {fuente}")

    lines.append("")
    lines.append("---")
    lines.append("Escribí tu reporte **El Tablero** para hoy basándote exclusivamente en estos datos.")

    return "\n".join(lines)


def _build_tomi_user_message(data):
    """Construir el user message para Tomi con datos de crypto, tech y CEDEARs."""
    fecha = data.get("metadata", {}).get("fecha", "?")
    macro = data.get("macro", {})
    crypto = data.get("crypto", {})
    indices = data.get("indices", {})
    cedears = data.get("cedears", {})
    calculados = data.get("calculados", {})
    noticias = data.get("noticias", {})

    lines = [f"# Datos del día — {fecha}"]

    # Detectar fechas
    fechas_datos = _detectar_fechas(data, fecha)
    if fechas_datos:
        lines.append("")
        lines.append("## NOTA SOBRE FECHAS DE LOS DATOS")
        lines.append(f"El pipeline corrió el {fecha}, pero los datos pueden corresponder a distintas fechas:")
        for categoria, fecha_d in fechas_datos.items():
            lines.append(f"- {categoria}: datos del {fecha_d}")
        lines.append("- Crypto opera 24/7 pero acciones solo en días hábiles. Tené en cuenta la diferencia.")

    # Dólar cripto
    dolar_cripto = macro.get("dolar", {}).get("cripto", {})
    if dolar_cripto.get("venta"):
        lines.append("")
        lines.append("## Dólar Cripto")
        lines.append(f"- Dólar cripto: ${_fmt(dolar_cripto['compra'])} compra / ${_fmt(dolar_cripto['venta'])} venta")

    # Crypto
    lines.append("")
    lines.append("## Crypto")
    for name, cry_data in crypto.items():
        ultimo = cry_data.get("ultimo")
        var = cry_data.get("variacion_pct")
        var7 = cry_data.get("variacion_7d_pct")
        fd = cry_data.get("fecha_dato")
        if ultimo:
            fecha_str = f" [dato del {fd}]" if fd else ""
            lines.append(f"- {name}: USD {_fmt(ultimo, 2)} (24h: {_pct(var) or '?'}, 7d: {_pct(var7) or '?'}){fecha_str}")

    ratio_eth_btc = calculados.get("ratio_eth_btc")
    if ratio_eth_btc:
        lines.append(f"- Ratio ETH/BTC: {ratio_eth_btc}")

    # NASDAQ
    nasdaq = indices.get("NASDAQ", {})
    if nasdaq.get("ultimo"):
        fd = nasdaq.get("fecha_dato")
        fecha_str = f" [dato del {fd}]" if fd else ""
        lines.append("")
        lines.append("## NASDAQ")
        lines.append(f"- NASDAQ: {_fmt(nasdaq['ultimo'])} ({_pct(nasdaq.get('variacion_pct')) or 'sin var'}){fecha_str}")

    # Acciones tech relevantes para Tomi (con datos CEDEAR como referencia)
    tech_tickers = ["MELI", "TSLA", "NVDA", "COIN", "GLOB", "AAPL", "GOOGL", "MSFT", "AMZN"]
    lines.append("")
    lines.append("## Acciones Tech (precio USD = acción real, CEDEAR = instrumento local)")
    for ticker in tech_tickers:
        ced = cedears.get(ticker, {})
        precio_us = ced.get("precio_us")
        var_us = ced.get("variacion_pct_us")
        if precio_us:
            lines.append(f"- {ticker}: USD {_fmt(precio_us, 2)} ({_pct(var_us) or 'sin var'})")

    # Noticias internacionales (filtrar tech/crypto si es posible)
    lines.append("")
    lines.append("## Noticias Internacionales (tech/crypto relevantes)")
    intl_news = noticias.get("internacionales", [])
    for i, n in enumerate(intl_news[:10], 1):
        titulo = n.get("titulo", "?")
        fuente = n.get("fuente", "?")
        lines.append(f"{i}. {titulo} — {fuente}")

    # Noticias Argentina (solo las que impactan tech/crypto)
    lines.append("")
    lines.append("## Noticias Argentina")
    ar_news = noticias.get("argentina", [])
    for i, n in enumerate(ar_news[:5], 1):
        titulo = n.get("titulo", "?")
        fuente = n.get("fuente", "?")
        lines.append(f"{i}. {titulo} — {fuente}")

    lines.append("")
    lines.append("---")
    lines.append("Escribí tu reporte **Señales** para hoy basándote exclusivamente en estos datos.")
    lines.append("IMPORTANTE: Este es tu primer reporte. En la sección Track record, establecé las reglas de seguimiento.")

    return "\n".join(lines)


def _build_vale_user_message(data):
    """Construir el user message para Vale (Renta Fija)."""
    fecha = data.get("metadata", {}).get("fecha", "?")
    macro = data.get("macro", {})
    dolar = macro.get("dolar", {})
    brechas = macro.get("brechas", {})
    inflacion = macro.get("inflacion", {})
    bcra = macro.get("bcra", {})
    tasas = macro.get("tasas", {})
    renta_fija = data.get("renta_fija", {})
    calculados = data.get("calculados", {})
    noticias = data.get("noticias", {})

    lines = [f"# Datos del día — {fecha}"]

    # Detectar fechas
    fechas_datos = _detectar_fechas(data, fecha)
    if fechas_datos:
        lines.append("")
        lines.append("## NOTA SOBRE FECHAS DE LOS DATOS")
        lines.append(f"El pipeline corrió el {fecha}, pero los datos pueden corresponder a distintas fechas:")
        for categoria, fecha_d in fechas_datos.items():
            lines.append(f"- {categoria}: datos del {fecha_d}")
        lines.append("- Tené en cuenta la diferencia al redactar.")

    # Dólar (oficial, blue, mep, ccl)
    lines.append("")
    lines.append("## Dólar")
    for nombre, key in [("Oficial", "oficial"), ("Blue", "blue"), ("MEP (Bolsa)", "mep"), ("CCL (Contado con Liqui)", "ccl")]:
        d = dolar.get(key, {})
        compra = _fmt(d.get("compra"), prefix="$")
        venta = _fmt(d.get("venta"), prefix="$")
        if compra and venta:
            lines.append(f"- {nombre}: {compra} compra / {venta} venta")

    # Brechas
    lines.append("")
    lines.append("## Brechas cambiarias")
    for nombre, key in [("Blue vs Oficial", "blue_oficial_pct"), ("MEP vs Oficial", "mep_oficial_pct"), ("CCL vs Oficial", "ccl_oficial_pct"), ("CCL vs MEP", "ccl_mep_pct")]:
        val = brechas.get(key)
        if val is not None:
            lines.append(f"- {nombre}: {_fmt(val, 1)}%")

    # Riesgo país
    lines.append("")
    lines.append("## Riesgo País")
    rp = macro.get("riesgo_pais", {})
    if rp.get("valor"):
        lines.append(f"- Riesgo país: {rp['valor']} puntos (fecha dato: {rp.get('fecha', '?')})")

    # Inflación y tasas
    lines.append("")
    lines.append("## Inflación y Tasas")
    infl_m = inflacion.get("mensual_ultimo", {})
    if infl_m.get("valor") is not None:
        lines.append(f"- Inflación mensual: {_fmt(infl_m['valor'], 1)}% ({infl_m.get('fecha', '?')})")
    infl_ia = inflacion.get("interanual_ultimo", {})
    if infl_ia.get("valor") is not None:
        lines.append(f"- Inflación interanual: {_fmt(infl_ia['valor'], 1)}%")
    infl_anual = calculados.get("inflacion_anualizada_pct")
    if infl_anual is not None:
        lines.append(f"- Inflación anualizada (compuesta desde último mes): {_fmt(infl_anual, 1)}%")
    badlar = tasas.get("badlar", {})
    if badlar.get("valor") is not None:
        lines.append(f"- Tasa BADLAR: {_fmt(badlar['valor'], 2)}% TNA ({badlar.get('fecha', '?')})")
    tasa_real = calculados.get("tasa_real_plazo_fijo_pct")
    if tasa_real is not None:
        lines.append(f"- Tasa real plazo fijo (promedio TNA - inflación anualizada): {_fmt(tasa_real, 1)}%")

    # BCRA
    lines.append("")
    lines.append("## BCRA")
    if bcra.get("reservas", {}).get("valor") is not None:
        lines.append(f"- Reservas internacionales: USD {_fmt(bcra['reservas']['valor'])} millones ({bcra['reservas'].get('fecha', '?')})")
    if bcra.get("base_monetaria", {}).get("valor") is not None:
        lines.append(f"- Base monetaria: ${_fmt(bcra['base_monetaria']['valor'])} millones ARS ({bcra['base_monetaria'].get('fecha', '?')})")
    if bcra.get("cer", {}).get("valor") is not None:
        lines.append(f"- CER: {_fmt(bcra['cer']['valor'], 2)} ({bcra['cer'].get('fecha', '?')})")

    # Bonos clave
    lines.append("")
    lines.append("## Bonos Soberanos Clave")
    bonos_clave = renta_fija.get("bonos_clave", {})
    for ticker, bd in bonos_clave.items():
        ultimo = bd.get("ultimo")
        var = bd.get("variacion_pct")
        if ultimo is not None:
            lines.append(f"- {ticker}: ${_fmt(ultimo, 2)} ({_pct(var) or 'sin var'})")

    # Tasas plazo fijo
    lines.append("")
    lines.append("## Tasas Plazo Fijo (principales entidades)")
    for pf in renta_fija.get("tasas_plazo_fijo", [])[:10]:
        entidad = pf.get("entidad", "?")
        tna_c = pf.get("tna_clientes")
        tna_nc = pf.get("tna_no_clientes")
        if tna_c is not None:
            lines.append(f"- {entidad}: {_fmt(tna_c, 2)}% TNA clientes / {_fmt(tna_nc, 2)}% TNA no-clientes")

    # ONs top por volumen
    lines.append("")
    lines.append("## Obligaciones Negociables (top por volumen)")
    ons = renta_fija.get("obligaciones_negociables", [])
    ons_sorted = sorted(ons, key=lambda x: x.get("volumen") or 0, reverse=True)
    for on in ons_sorted[:10]:
        ticker = on.get("ticker", "?")
        emisor = on.get("emisor", "?")
        ultimo = on.get("ultimo")
        var = on.get("variacion_pct")
        vol = on.get("volumen")
        moneda = on.get("moneda", "")
        if ultimo is not None:
            lines.append(f"- {ticker} ({emisor}): ${_fmt(ultimo, 2)} {moneda} ({_pct(var) or 'sin var'}) vol: {_fmt(vol)}")

    # Noticias Argentina
    lines.append("")
    lines.append("## Noticias Argentina")
    for i, n in enumerate(noticias.get("argentina", [])[:10], 1):
        titulo = n.get("titulo", "?")
        fuente = n.get("fuente", "?")
        lines.append(f"{i}. {titulo} — {fuente}")

    lines.append("")
    lines.append("---")
    lines.append("Escribí tu reporte **La Curva** para hoy basándote exclusivamente en estos datos.")
    lines.append("IMPORTANTE: Este es tu primer reporte. En la sección Scorecard, establecé las reglas de seguimiento.")

    return "\n".join(lines)


def _build_santi_user_message(data):
    """Construir el user message para Santi (Equity)."""
    fecha = data.get("metadata", {}).get("fecha", "?")
    macro = data.get("macro", {})
    dolar = macro.get("dolar", {})
    indices = data.get("indices", {})
    equity_ar = data.get("equity_ar", {})
    cedears = data.get("cedears", {})
    calculados = data.get("calculados", {})
    noticias = data.get("noticias", {})

    lines = [f"# Datos del día — {fecha}"]

    # Detectar fechas
    fechas_datos = _detectar_fechas(data, fecha)
    if fechas_datos:
        lines.append("")
        lines.append("## NOTA SOBRE FECHAS DE LOS DATOS")
        lines.append(f"El pipeline corrió el {fecha}, pero los datos pueden corresponder a distintas fechas:")
        for categoria, fecha_d in fechas_datos.items():
            lines.append(f"- {categoria}: datos del {fecha_d}")
        lines.append("- Tené en cuenta la diferencia al redactar.")

    # Índices
    lines.append("")
    lines.append("## Índices")
    for name in ["MERVAL", "SP500"]:
        idx_data = indices.get(name, {})
        ultimo = idx_data.get("ultimo")
        var = idx_data.get("variacion_pct")
        fd = idx_data.get("fecha_dato")
        if ultimo:
            fecha_str = f" [dato del {fd}]" if fd else ""
            lines.append(f"- {name}: {_fmt(ultimo)} ({_pct(var) or 'sin var'}){fecha_str}")

    merval_usd = calculados.get("merval_usd_ccl")
    if merval_usd:
        lines.append(f"- MERVAL en USD (vía CCL): {_fmt(merval_usd, 0)}")

    # Dólar CCL referencia
    ccl = dolar.get("ccl", {})
    if ccl.get("venta"):
        lines.append("")
        lines.append("## Dólar CCL (referencia)")
        lines.append(f"- CCL: ${_fmt(ccl['compra'])} compra / ${_fmt(ccl['venta'])} venta")

    # Acciones argentinas
    lines.append("")
    lines.append("## Acciones Argentinas")
    acciones = equity_ar.get("acciones", {})
    for ticker, ac_data in acciones.items():
        ultimo = ac_data.get("ultimo")
        var = ac_data.get("variacion_pct")
        vol = ac_data.get("volumen")
        nombre = ac_data.get("nombre", ticker)
        fd = ac_data.get("fecha_dato")
        if ultimo is not None:
            fecha_str = f" [dato del {fd}]" if fd else ""
            lines.append(f"- {ticker} ({nombre}): ${_fmt(ultimo, 2)} ({_pct(var) or 'sin var'}) vol: {_fmt(vol)}{fecha_str}")

    # CEDEARs
    lines.append("")
    lines.append("## CEDEARs (precio USD real + CEDEAR ARS)")
    for ticker, ced in cedears.items():
        precio_us = ced.get("precio_us")
        var_us = ced.get("variacion_pct_us")
        precio_ars = ced.get("precio_cedear_ars")
        var_ars = ced.get("variacion_pct_cedear")
        ratio = ced.get("ratio")
        fund = ced.get("fundamentals", {})
        if precio_us is not None:
            pe = fund.get("pe_ratio")
            sector = fund.get("sector", "")
            mcap = fund.get("market_cap_fmt", "")
            pe_str = f" P/E: {_fmt(pe, 1)}" if pe else ""
            sector_str = f" [{sector}]" if sector else ""
            mcap_str = f" MCap: {mcap}" if mcap else ""
            lines.append(f"- {ticker}: USD {_fmt(precio_us, 2)} ({_pct(var_us) or 'sin var'}) | CEDEAR ${_fmt(precio_ars, 2)} ({_pct(var_ars) or 'sin var'}) ratio {ratio}{pe_str}{sector_str}{mcap_str}")

    # Noticias
    lines.append("")
    lines.append("## Noticias Argentina")
    for i, n in enumerate(noticias.get("argentina", [])[:10], 1):
        titulo = n.get("titulo", "?")
        fuente = n.get("fuente", "?")
        lines.append(f"{i}. {titulo} — {fuente}")

    lines.append("")
    lines.append("## Noticias Internacionales")
    for i, n in enumerate(noticias.get("internacionales", [])[:10], 1):
        titulo = n.get("titulo", "?")
        fuente = n.get("fuente", "?")
        lines.append(f"{i}. {titulo} — {fuente}")

    lines.append("")
    lines.append("---")
    lines.append("Escribí tu reporte **El Parqué** para hoy basándote exclusivamente en estos datos.")
    lines.append("IMPORTANTE: Este es tu primer reporte. En la sección Scorecard, establecé las reglas de seguimiento.")

    return "\n".join(lines)


def _build_sol_user_message(data):
    """Construir el user message para Sol (Portfolio / Visión integral)."""
    fecha = data.get("metadata", {}).get("fecha", "?")
    macro = data.get("macro", {})
    dolar = macro.get("dolar", {})
    brechas = macro.get("brechas", {})
    inflacion = macro.get("inflacion", {})
    bcra = macro.get("bcra", {})
    tasas = macro.get("tasas", {})
    indices = data.get("indices", {})
    commodities = data.get("commodities", {})
    crypto = data.get("crypto", {})
    renta_fija = data.get("renta_fija", {})
    equity_ar = data.get("equity_ar", {})
    cedears = data.get("cedears", {})
    calculados = data.get("calculados", {})
    noticias = data.get("noticias", {})

    lines = [f"# Datos del día — {fecha}"]

    # Detectar fechas
    fechas_datos = _detectar_fechas(data, fecha)
    if fechas_datos:
        lines.append("")
        lines.append("## NOTA SOBRE FECHAS DE LOS DATOS")
        lines.append(f"El pipeline corrió el {fecha}, pero los datos pueden corresponder a distintas fechas:")
        for categoria, fecha_d in fechas_datos.items():
            lines.append(f"- {categoria}: datos del {fecha_d}")
        lines.append("- Tené en cuenta la diferencia al redactar.")

    # Dólar completo
    lines.append("")
    lines.append("## Dólar")
    dolar_tipos = [
        ("Oficial", "oficial"), ("Blue", "blue"), ("MEP (Bolsa)", "mep"),
        ("CCL (Contado con Liqui)", "ccl"), ("Mayorista", "mayorista"),
        ("Cripto", "cripto"), ("Tarjeta", "tarjeta"),
    ]
    for nombre, key in dolar_tipos:
        d = dolar.get(key, {})
        compra = _fmt(d.get("compra"), prefix="$")
        venta = _fmt(d.get("venta"), prefix="$")
        if compra and venta:
            lines.append(f"- {nombre}: {compra} compra / {venta} venta")

    # Brechas
    lines.append("")
    lines.append("## Brechas cambiarias")
    for nombre, key in [("Blue vs Oficial", "blue_oficial_pct"), ("MEP vs Oficial", "mep_oficial_pct"), ("CCL vs Oficial", "ccl_oficial_pct"), ("CCL vs MEP", "ccl_mep_pct")]:
        val = brechas.get(key)
        if val is not None:
            lines.append(f"- {nombre}: {_fmt(val, 1)}%")

    # Riesgo país
    rp = macro.get("riesgo_pais", {})
    if rp.get("valor"):
        lines.append("")
        lines.append("## Riesgo País")
        lines.append(f"- Riesgo país: {rp['valor']} puntos (fecha dato: {rp.get('fecha', '?')})")

    # Inflación y BCRA
    lines.append("")
    lines.append("## Inflación y BCRA")
    infl_m = inflacion.get("mensual_ultimo", {})
    if infl_m.get("valor") is not None:
        lines.append(f"- Inflación mensual: {_fmt(infl_m['valor'], 1)}% ({infl_m.get('fecha', '?')})")
    infl_ia = inflacion.get("interanual_ultimo", {})
    if infl_ia.get("valor") is not None:
        lines.append(f"- Inflación interanual: {_fmt(infl_ia['valor'], 1)}%")
    infl_anual = calculados.get("inflacion_anualizada_pct")
    if infl_anual is not None:
        lines.append(f"- Inflación anualizada (compuesta): {_fmt(infl_anual, 1)}%")
    if bcra.get("reservas", {}).get("valor") is not None:
        lines.append(f"- Reservas internacionales BCRA: USD {_fmt(bcra['reservas']['valor'])} millones ({bcra['reservas'].get('fecha', '?')})")
    if bcra.get("base_monetaria", {}).get("valor") is not None:
        lines.append(f"- Base monetaria: ${_fmt(bcra['base_monetaria']['valor'])} millones ARS ({bcra['base_monetaria'].get('fecha', '?')})")
    badlar = tasas.get("badlar", {})
    if badlar.get("valor") is not None:
        lines.append(f"- Tasa BADLAR: {_fmt(badlar['valor'], 2)}% TNA ({badlar.get('fecha', '?')})")
    if bcra.get("cer", {}).get("valor") is not None:
        lines.append(f"- CER: {_fmt(bcra['cer']['valor'], 2)} ({bcra['cer'].get('fecha', '?')})")

    # Índices
    lines.append("")
    lines.append("## Índices")
    for name, idx_data in indices.items():
        ultimo = idx_data.get("ultimo")
        var = idx_data.get("variacion_pct")
        fd = idx_data.get("fecha_dato")
        if ultimo:
            fecha_str = f" [dato del {fd}]" if fd else ""
            lines.append(f"- {name}: {_fmt(ultimo)} ({_pct(var) or 'sin var'}){fecha_str}")
    merval_usd = calculados.get("merval_usd_ccl")
    if merval_usd:
        lines.append(f"- MERVAL en USD (vía CCL): {_fmt(merval_usd, 0)}")

    # Commodities
    lines.append("")
    lines.append("## Commodities")
    for name, cmd_data in commodities.items():
        ultimo = cmd_data.get("ultimo")
        var = cmd_data.get("variacion_pct")
        unidad = cmd_data.get("unidad", "")
        fd = cmd_data.get("fecha_dato")
        if ultimo:
            fecha_str = f" [dato del {fd}]" if fd else ""
            lines.append(f"- {name.replace('_', ' ').title()}: ${_fmt(ultimo, 2)}/{unidad.split('/')[-1]} ({_pct(var) or 'sin var'}){fecha_str}")

    # Crypto
    lines.append("")
    lines.append("## Crypto")
    for name, cry_data in crypto.items():
        ultimo = cry_data.get("ultimo")
        var = cry_data.get("variacion_pct")
        var7 = cry_data.get("variacion_7d_pct")
        if ultimo:
            lines.append(f"- {name}: USD {_fmt(ultimo)} (24h: {_pct(var) or '?'}, 7d: {_pct(var7) or '?'})")

    # Bonos clave
    lines.append("")
    lines.append("## Bonos Soberanos Clave")
    bonos_clave = renta_fija.get("bonos_clave", {})
    for ticker, bd in bonos_clave.items():
        ultimo = bd.get("ultimo")
        var = bd.get("variacion_pct")
        if ultimo is not None:
            lines.append(f"- {ticker}: ${_fmt(ultimo, 2)} ({_pct(var) or 'sin var'})")

    # Equity AR — top movers (by absolute variacion_pct)
    lines.append("")
    lines.append("## Acciones Argentinas (top movers)")
    acciones = equity_ar.get("acciones", {})
    sorted_acciones = sorted(acciones.items(), key=lambda x: abs(x[1].get("variacion_pct") or 0), reverse=True)
    for ticker, ac_data in sorted_acciones[:10]:
        ultimo = ac_data.get("ultimo")
        var = ac_data.get("variacion_pct")
        nombre = ac_data.get("nombre", ticker)
        if ultimo is not None:
            lines.append(f"- {ticker} ({nombre}): ${_fmt(ultimo, 2)} ({_pct(var) or 'sin var'})")

    # CEDEARs — top by variacion
    lines.append("")
    lines.append("## CEDEARs (top movers)")
    sorted_cedears = sorted(cedears.items(), key=lambda x: abs(x[1].get("variacion_pct_us") or 0), reverse=True)
    for ticker, ced in sorted_cedears[:10]:
        precio_us = ced.get("precio_us")
        var_us = ced.get("variacion_pct_us")
        if precio_us is not None:
            lines.append(f"- {ticker}: USD {_fmt(precio_us, 2)} ({_pct(var_us) or 'sin var'})")

    # Calculados
    lines.append("")
    lines.append("## Indicadores Calculados")
    tasa_real = calculados.get("tasa_real_plazo_fijo_pct")
    if tasa_real is not None:
        lines.append(f"- Tasa real plazo fijo: {_fmt(tasa_real, 1)}%")
    prima_cedear = calculados.get("cedears_prima_promedio_pct")
    if prima_cedear is not None:
        lines.append(f"- Prima promedio CEDEARs: {_fmt(prima_cedear, 1)}%")
    ratio_eth = calculados.get("ratio_eth_btc")
    if ratio_eth is not None:
        lines.append(f"- Ratio ETH/BTC: {ratio_eth}")

    # Noticias
    lines.append("")
    lines.append("## Noticias Argentina")
    for i, n in enumerate(noticias.get("argentina", [])[:10], 1):
        titulo = n.get("titulo", "?")
        fuente = n.get("fuente", "?")
        lines.append(f"{i}. {titulo} — {fuente}")

    lines.append("")
    lines.append("## Noticias Internacionales")
    for i, n in enumerate(noticias.get("internacionales", [])[:10], 1):
        titulo = n.get("titulo", "?")
        fuente = n.get("fuente", "?")
        lines.append(f"{i}. {titulo} — {fuente}")

    lines.append("")
    lines.append("---")
    lines.append("Escribí tu reporte **La Brújula** para hoy basándote exclusivamente en estos datos.")
    lines.append("IMPORTANTE: Este es tu primer reporte. En la sección Bitácora, establecé las reglas de seguimiento.")

    return "\n".join(lines)


def _build_diego_user_message(data):
    """Construir el user message para Diego (Análisis Técnico)."""
    fecha = data.get("metadata", {}).get("fecha", "?")
    macro = data.get("macro", {})
    dolar = macro.get("dolar", {})
    indices = data.get("indices", {})
    equity_ar = data.get("equity_ar", {})
    cedears = data.get("cedears", {})
    commodities = data.get("commodities", {})
    crypto = data.get("crypto", {})

    lines = [f"# Datos del día — {fecha}"]

    # Detectar fechas
    fechas_datos = _detectar_fechas(data, fecha)
    if fechas_datos:
        lines.append("")
        lines.append("## NOTA SOBRE FECHAS DE LOS DATOS")
        lines.append(f"El pipeline corrió el {fecha}, pero los datos pueden corresponder a distintas fechas:")
        for categoria, fecha_d in fechas_datos.items():
            lines.append(f"- {categoria}: datos del {fecha_d}")
        lines.append("- Los datos OHLCV son de la última rueda disponible. Tené en cuenta la diferencia.")

    # Dólar MEP y CCL (referencia)
    lines.append("")
    lines.append("## Dólar (referencia)")
    for nombre, key in [("MEP (Bolsa)", "mep"), ("CCL (Contado con Liqui)", "ccl")]:
        d = dolar.get(key, {})
        compra = _fmt(d.get("compra"), prefix="$")
        venta = _fmt(d.get("venta"), prefix="$")
        if compra and venta:
            lines.append(f"- {nombre}: {compra} compra / {venta} venta")

    # Índices
    lines.append("")
    lines.append("## Índices")
    for name in ["MERVAL", "SP500", "NASDAQ"]:
        idx_data = indices.get(name, {})
        ultimo = idx_data.get("ultimo")
        var = idx_data.get("variacion_pct")
        fd = idx_data.get("fecha_dato")
        if ultimo:
            fecha_str = f" [dato del {fd}]" if fd else ""
            lines.append(f"- {name}: {_fmt(ultimo)} ({_pct(var) or 'sin var'}){fecha_str}")

    # Acciones argentinas (all with OHLCV)
    lines.append("")
    lines.append("## Acciones Argentinas (OHLCV)")
    acciones = equity_ar.get("acciones", {})
    for ticker, ac_data in acciones.items():
        ultimo = ac_data.get("ultimo")
        apertura = ac_data.get("apertura")
        maximo = ac_data.get("maximo")
        minimo = ac_data.get("minimo")
        vol = ac_data.get("volumen")
        var = ac_data.get("variacion_pct")
        cierre_ant = ac_data.get("cierre_anterior")
        fd = ac_data.get("fecha_dato")
        if ultimo is not None:
            fecha_str = f" [dato del {fd}]" if fd else ""
            lines.append(f"- {ticker}: C ${_fmt(ultimo, 2)} | O ${_fmt(apertura, 2)} | H ${_fmt(maximo, 2)} | L ${_fmt(minimo, 2)} | Vol {_fmt(vol)} | Var {_pct(var) or '?'} | Cierre ant ${_fmt(cierre_ant, 2)}{fecha_str}")

    # CEDEARs tech (top tech tickers)
    lines.append("")
    lines.append("## CEDEARs Tech (precio USD y variación)")
    tech_tickers = ["MELI", "TSLA", "NVDA", "AAPL", "GOOGL", "MSFT", "AMZN", "META", "COIN", "GLOB"]
    for ticker in tech_tickers:
        ced = cedears.get(ticker, {})
        precio_us = ced.get("precio_us")
        var_us = ced.get("variacion_pct_us")
        precio_ars = ced.get("precio_cedear_ars")
        var_ars = ced.get("variacion_pct_cedear")
        if precio_us is not None:
            lines.append(f"- {ticker}: USD {_fmt(precio_us, 2)} ({_pct(var_us) or 'sin var'}) | CEDEAR ${_fmt(precio_ars, 2)} ({_pct(var_ars) or 'sin var'})")

    # Commodities
    lines.append("")
    lines.append("## Commodities")
    for name, cmd_data in commodities.items():
        ultimo = cmd_data.get("ultimo")
        var = cmd_data.get("variacion_pct")
        unidad = cmd_data.get("unidad", "")
        fd = cmd_data.get("fecha_dato")
        if ultimo:
            fecha_str = f" [dato del {fd}]" if fd else ""
            lines.append(f"- {name.replace('_', ' ').title()}: ${_fmt(ultimo, 2)}/{unidad.split('/')[-1]} ({_pct(var) or 'sin var'}){fecha_str}")

    # Crypto (BTC, ETH)
    lines.append("")
    lines.append("## Crypto (BTC y ETH)")
    for name in ["BTC", "ETH"]:
        cry_data = crypto.get(name, {})
        ultimo = cry_data.get("ultimo")
        var = cry_data.get("variacion_pct")
        var7 = cry_data.get("variacion_7d_pct")
        if ultimo:
            lines.append(f"- {name}: USD {_fmt(ultimo)} (24h: {_pct(var) or '?'}, 7d: {_pct(var7) or '?'})")

    lines.append("")
    lines.append("---")
    lines.append("Escribí tu reporte **El Gráfico** para hoy basándote exclusivamente en estos datos.")
    lines.append("IMPORTANTE: Este es tu primer reporte. En la sección Track record, establecé las reglas de seguimiento.")

    return "\n".join(lines)


def _build_roberto_user_message(data):
    """Construir el user message para Roberto (Tactical Macro)."""
    fecha = data.get("metadata", {}).get("fecha", "?")
    macro = data.get("macro", {})
    dolar = macro.get("dolar", {})
    brechas = macro.get("brechas", {})
    inflacion = macro.get("inflacion", {})
    bcra = macro.get("bcra", {})
    tasas = macro.get("tasas", {})
    renta_fija = data.get("renta_fija", {})
    equity_ar = data.get("equity_ar", {})
    indices = data.get("indices", {})
    commodities = data.get("commodities", {})
    calculados = data.get("calculados", {})
    noticias = data.get("noticias", {})

    lines = [f"# Datos del día — {fecha}"]

    # Detectar fechas
    fechas_datos = _detectar_fechas(data, fecha)
    if fechas_datos:
        lines.append("")
        lines.append("## NOTA SOBRE FECHAS DE LOS DATOS")
        lines.append(f"El pipeline corrió el {fecha}, pero los datos pueden corresponder a distintas fechas:")
        for categoria, fecha_d in fechas_datos.items():
            lines.append(f"- {categoria}: datos del {fecha_d}")
        lines.append("- Tené en cuenta la diferencia al redactar.")

    # Dólar completo
    lines.append("")
    lines.append("## Dólar")
    dolar_tipos = [
        ("Oficial", "oficial"), ("Blue", "blue"), ("MEP (Bolsa)", "mep"),
        ("CCL (Contado con Liqui)", "ccl"), ("Mayorista", "mayorista"),
        ("Cripto", "cripto"), ("Tarjeta", "tarjeta"),
    ]
    for nombre, key in dolar_tipos:
        d = dolar.get(key, {})
        compra = _fmt(d.get("compra"), prefix="$")
        venta = _fmt(d.get("venta"), prefix="$")
        if compra and venta:
            lines.append(f"- {nombre}: {compra} compra / {venta} venta")

    # Brechas
    lines.append("")
    lines.append("## Brechas cambiarias")
    for nombre, key in [("Blue vs Oficial", "blue_oficial_pct"), ("MEP vs Oficial", "mep_oficial_pct"), ("CCL vs Oficial", "ccl_oficial_pct"), ("CCL vs MEP", "ccl_mep_pct")]:
        val = brechas.get(key)
        if val is not None:
            lines.append(f"- {nombre}: {_fmt(val, 1)}%")

    # Riesgo país
    rp = macro.get("riesgo_pais", {})
    if rp.get("valor"):
        lines.append("")
        lines.append("## Riesgo País")
        lines.append(f"- Riesgo país: {rp['valor']} puntos (fecha dato: {rp.get('fecha', '?')})")

    # Inflación
    lines.append("")
    lines.append("## Inflación")
    infl_m = inflacion.get("mensual_ultimo", {})
    if infl_m.get("valor") is not None:
        lines.append(f"- Inflación mensual: {_fmt(infl_m['valor'], 1)}% ({infl_m.get('fecha', '?')})")
    infl_ia = inflacion.get("interanual_ultimo", {})
    if infl_ia.get("valor") is not None:
        lines.append(f"- Inflación interanual: {_fmt(infl_ia['valor'], 1)}%")
    infl_anual = calculados.get("inflacion_anualizada_pct")
    if infl_anual is not None:
        lines.append(f"- Inflación anualizada (compuesta desde último mes): {_fmt(infl_anual, 1)}%")
    serie = inflacion.get("serie_12m", [])
    if serie:
        vals = [_fmt(s["valor"], 1) + "%" for s in serie if s.get("valor") is not None]
        lines.append(f"- Serie inflación últimos 12 meses: {', '.join(vals)}")

    # BCRA y Tasas
    lines.append("")
    lines.append("## BCRA y Tasas")
    if bcra.get("reservas", {}).get("valor") is not None:
        lines.append(f"- Reservas internacionales: USD {_fmt(bcra['reservas']['valor'])} millones ({bcra['reservas'].get('fecha', '?')})")
    if bcra.get("base_monetaria", {}).get("valor") is not None:
        lines.append(f"- Base monetaria: ${_fmt(bcra['base_monetaria']['valor'])} millones ARS ({bcra['base_monetaria'].get('fecha', '?')})")
    badlar = tasas.get("badlar", {})
    if badlar.get("valor") is not None:
        lines.append(f"- Tasa BADLAR: {_fmt(badlar['valor'], 2)}% TNA ({badlar.get('fecha', '?')})")
    if bcra.get("cer", {}).get("valor") is not None:
        lines.append(f"- CER: {_fmt(bcra['cer']['valor'], 2)} ({bcra['cer'].get('fecha', '?')})")
    tasa_real = calculados.get("tasa_real_plazo_fijo_pct")
    if tasa_real is not None:
        lines.append(f"- Tasa real plazo fijo: {_fmt(tasa_real, 1)}%")

    # Bonos clave
    lines.append("")
    lines.append("## Bonos Soberanos Clave")
    bonos_clave = renta_fija.get("bonos_clave", {})
    for ticker, bd in bonos_clave.items():
        ultimo = bd.get("ultimo")
        var = bd.get("variacion_pct")
        if ultimo is not None:
            lines.append(f"- {ticker}: ${_fmt(ultimo, 2)} ({_pct(var) or 'sin var'})")

    # ONs top
    lines.append("")
    lines.append("## Obligaciones Negociables (top por volumen)")
    ons = renta_fija.get("obligaciones_negociables", [])
    ons_sorted = sorted(ons, key=lambda x: x.get("volumen") or 0, reverse=True)
    for on in ons_sorted[:8]:
        ticker = on.get("ticker", "?")
        emisor = on.get("emisor", "?")
        ultimo = on.get("ultimo")
        var = on.get("variacion_pct")
        moneda = on.get("moneda", "")
        if ultimo is not None:
            lines.append(f"- {ticker} ({emisor}): ${_fmt(ultimo, 2)} {moneda} ({_pct(var) or 'sin var'})")

    # Equity AR — top movers
    lines.append("")
    lines.append("## Acciones Argentinas (top movers)")
    acciones = equity_ar.get("acciones", {})
    sorted_acciones = sorted(acciones.items(), key=lambda x: abs(x[1].get("variacion_pct") or 0), reverse=True)
    for ticker, ac_data in sorted_acciones[:8]:
        ultimo = ac_data.get("ultimo")
        var = ac_data.get("variacion_pct")
        nombre = ac_data.get("nombre", ticker)
        if ultimo is not None:
            lines.append(f"- {ticker} ({nombre}): ${_fmt(ultimo, 2)} ({_pct(var) or 'sin var'})")

    # Commodities (soja, petroleo)
    lines.append("")
    lines.append("## Commodities (clave para Argentina)")
    for name in ["soja", "petroleo_wti"]:
        cmd_data = commodities.get(name, {})
        ultimo = cmd_data.get("ultimo")
        var = cmd_data.get("variacion_pct")
        unidad = cmd_data.get("unidad", "")
        fd = cmd_data.get("fecha_dato")
        if ultimo:
            fecha_str = f" [dato del {fd}]" if fd else ""
            lines.append(f"- {name.replace('_', ' ').title()}: ${_fmt(ultimo, 2)}/{unidad.split('/')[-1]} ({_pct(var) or 'sin var'}){fecha_str}")

    # MERVAL
    lines.append("")
    lines.append("## Índice MERVAL")
    merval = indices.get("MERVAL", {})
    if merval.get("ultimo"):
        fd = merval.get("fecha_dato")
        fecha_str = f" [dato del {fd}]" if fd else ""
        lines.append(f"- MERVAL: {_fmt(merval['ultimo'])} ({_pct(merval.get('variacion_pct')) or 'sin var'}){fecha_str}")
    merval_usd = calculados.get("merval_usd_ccl")
    if merval_usd:
        lines.append(f"- MERVAL en USD (vía CCL): {_fmt(merval_usd, 0)}")

    # Calculados
    lines.append("")
    lines.append("## Indicadores Calculados")
    prima_cedear = calculados.get("cedears_prima_promedio_pct")
    if prima_cedear is not None:
        lines.append(f"- Prima promedio CEDEARs: {_fmt(prima_cedear, 1)}%")

    # Noticias
    lines.append("")
    lines.append("## Noticias Argentina")
    for i, n in enumerate(noticias.get("argentina", [])[:10], 1):
        titulo = n.get("titulo", "?")
        fuente = n.get("fuente", "?")
        lines.append(f"{i}. {titulo} — {fuente}")

    lines.append("")
    lines.append("## Noticias Internacionales (relevantes para Argentina)")
    for i, n in enumerate(noticias.get("internacionales", [])[:10], 1):
        titulo = n.get("titulo", "?")
        fuente = n.get("fuente", "?")
        lines.append(f"{i}. {titulo} — {fuente}")

    lines.append("")
    lines.append("---")
    lines.append("Escribí tu reporte **El Estratega** para hoy basándote exclusivamente en estos datos.")
    lines.append("IMPORTANTE: Este es tu primer reporte. En la sección Bitácora, establecé las reglas de seguimiento.")

    return "\n".join(lines)


def _load_latest_json():
    """Cargar el JSON diario más reciente de output/."""
    pattern = os.path.join(OUTPUT_DIR, "datos_diarios_*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        print(f"ERROR: No se encontraron archivos en {pattern}")
        sys.exit(1)
    return files[-1]


def _load_system_prompt(agente):
    """Cargar el system prompt de un agente."""
    path = os.path.join(PROMPTS_DIR, f"{agente}_system.md")
    if not os.path.exists(path):
        print(f"ERROR: No existe el prompt {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _build_user_message(agente, data):
    """Construir el user message según el agente."""
    builders = {
        "manu": _build_manu_user_message,
        "tomi": _build_tomi_user_message,
        "vale": _build_vale_user_message,
        "santi": _build_santi_user_message,
        "sol": _build_sol_user_message,
        "diego": _build_diego_user_message,
        "roberto": _build_roberto_user_message,
    }
    builder = builders.get(agente)
    if not builder:
        print(f"ERROR: No hay builder para agente '{agente}'")
        sys.exit(1)
    return builder(data)


def generar(agente, datos_path, model=None):
    """Generar un reporte para el agente dado."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY no configurada en .env")
        sys.exit(1)

    model = model or os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4")

    # Cargar datos
    with open(datos_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    fecha = data.get("metadata", {}).get("fecha", "unknown")

    # Cargar prompts
    system_prompt = _load_system_prompt(agente)
    user_message = _build_user_message(agente, data)

    print(f"Generando reporte de {agente} para {fecha}...")
    print(f"  Modelo: {model}")
    print(f"  Datos: {datos_path}")
    print(f"  System prompt: {len(system_prompt)} chars")
    print(f"  User message: {len(user_message)} chars")

    # Llamar a OpenRouter
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        max_tokens=4000,
        temperature=0.7,
    )

    reporte = response.choices[0].message.content

    # Guardar
    os.makedirs(REPORTES_DIR, exist_ok=True)
    output_path = os.path.join(REPORTES_DIR, f"{agente}_{fecha}.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(reporte)

    # Resumen
    palabras = len(reporte.split())
    print(f"\n  Reporte generado: {output_path}")
    print(f"  Palabras: {palabras}")
    print(f"  Tokens usados: {response.usage.total_tokens if response.usage else '?'}")

    limites = {
        "tomi": (500, 800),
        "vale": (600, 900),
        "santi": (700, 1200),
        "sol": (1000, 1500),
        "diego": (600, 1000),
        "roberto": (800, 1200),
    }
    min_w, max_w = limites.get(agente, (800, 1200))
    if palabras < min_w:
        print(f"  WARN: Extensión por debajo del mínimo ({min_w} palabras)")
    elif palabras > max_w:
        print(f"  WARN: Extensión por encima del máximo ({max_w} palabras)")
    else:
        print(f"  OK: Extensión dentro del rango")

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generar reporte de agente financiero")
    parser.add_argument("--agente", default="manu", help="Nombre del agente (default: manu)")
    parser.add_argument("--datos", default=None, help="Path al JSON diario (default: último disponible)")
    parser.add_argument("--model", default=None, help="Modelo OpenRouter (default: desde .env)")
    args = parser.parse_args()

    datos_path = args.datos or _load_latest_json()
    generar(args.agente, datos_path, args.model)


if __name__ == "__main__":
    main()
