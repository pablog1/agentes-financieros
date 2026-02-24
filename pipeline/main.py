"""
Orquestador del pipeline de datos diarios.
Ejecuta todos los fetchers, calcula campos derivados, compone y guarda el JSON.
"""

import json
import logging
import os
import sys
from datetime import date, datetime

from pipeline.config import OUTPUT_DIR, OUTPUT_FILENAME_TEMPLATE
from pipeline.fetchers.macro import fetch_macro
from pipeline.fetchers.renta_fija import fetch_renta_fija
from pipeline.fetchers.equity import fetch_equity
from pipeline.fetchers.indices_commodities import fetch_indices_commodities_crypto
from pipeline.fetchers.noticias import fetch_noticias

logger = logging.getLogger("pipeline")


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )


def _safe_float(val):
    if val is None:
        return None
    try:
        f = float(val)
        return None if f != f else f
    except (ValueError, TypeError):
        return None


def _compute_calculated(macro, indices, crypto, renta_fija, cedears):
    """Calcular métricas derivadas que cruzan categorías."""
    calculados = {}

    # MERVAL en USD vía CCL
    merval = (indices.get("MERVAL") or {}).get("ultimo")
    ccl_venta = (macro.get("dolar", {}).get("ccl") or {}).get("venta")
    if merval and ccl_venta and ccl_venta > 0:
        calculados["merval_usd_ccl"] = round(merval / ccl_venta, 2)
    else:
        calculados["merval_usd_ccl"] = None

    # Ratio ETH/BTC
    btc = (crypto.get("BTC") or {}).get("ultimo")
    eth = (crypto.get("ETH") or {}).get("ultimo")
    if btc and eth and btc > 0:
        calculados["ratio_eth_btc"] = round(eth / btc, 6)
    else:
        calculados["ratio_eth_btc"] = None

    # Inflación anualizada (último mes * compuesto)
    infl = macro.get("inflacion", {}).get("mensual_ultimo", {}).get("valor")
    if infl:
        calculados["inflacion_anualizada_pct"] = round(((1 + infl / 100) ** 12 - 1) * 100, 2)
    else:
        calculados["inflacion_anualizada_pct"] = None

    # Tasa real plazo fijo: promedio TNA - inflación anualizada
    tasas = renta_fija.get("tasas_plazo_fijo", [])
    if tasas and calculados.get("inflacion_anualizada_pct") is not None:
        tnas = [t.get("tna_clientes") for t in tasas if t.get("tna_clientes")]
        if tnas:
            avg_tna = sum(tnas) / len(tnas)
            calculados["tasa_real_plazo_fijo_pct"] = round(
                avg_tna - calculados["inflacion_anualizada_pct"], 2
            )
        else:
            calculados["tasa_real_plazo_fijo_pct"] = None
    else:
        calculados["tasa_real_plazo_fijo_pct"] = None

    # Prima/descuento promedio de CEDEARs
    primas = [
        c.get("prima_descuento_pct")
        for c in cedears.values()
        if c.get("prima_descuento_pct") is not None
    ]
    if primas:
        calculados["cedears_prima_promedio_pct"] = round(sum(primas) / len(primas), 2)
    else:
        calculados["cedears_prima_promedio_pct"] = None

    return calculados


def _check_date_sync(output):
    """Verificar sincronización de fechas entre categorías de datos."""
    hoy = output["metadata"]["fecha"]
    warnings = []

    # Verificar índices
    for name, idx in output.get("indices", {}).items():
        fd = idx.get("fecha_dato")
        if fd and fd != hoy:
            warnings.append(f"  {name}: dato del {fd} (pipeline corrió el {hoy})")

    # Verificar commodities
    for name, cmd in output.get("commodities", {}).items():
        fd = cmd.get("fecha_dato")
        if fd and fd != hoy:
            warnings.append(f"  {name}: dato del {fd}")

    # Riesgo país
    rp_fecha = output.get("macro", {}).get("riesgo_pais", {}).get("fecha")
    if rp_fecha and rp_fecha != hoy:
        warnings.append(f"  Riesgo país: dato del {rp_fecha}")

    if warnings:
        logger.warning("DESFASAJE DE FECHAS detectado:")
        for w in warnings:
            logger.warning(w)
        output["metadata"]["advertencia_fechas"] = True
    else:
        output["metadata"]["advertencia_fechas"] = False


def save_json(data):
    """Guardar JSON en el directorio output."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = OUTPUT_FILENAME_TEMPLATE.format(fecha=date.today().isoformat())
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    return filepath


def _print_summary(output):
    """Imprimir resumen del pipeline."""
    print("\n" + "=" * 60)
    print(f"RESUMEN — {output['metadata']['fecha']}")
    print("=" * 60)

    # Macro
    dolar = output.get("macro", {}).get("dolar", {})
    tipos_ok = sum(1 for v in dolar.values() if isinstance(v, dict) and v.get("venta"))
    rp = output.get("macro", {}).get("riesgo_pais", {}).get("valor")
    print(f"  Dólar: {tipos_ok} tipos con precio")
    print(f"  Riesgo país: {rp}")

    # Brechas
    brechas = output.get("macro", {}).get("brechas", {})
    if brechas.get("ccl_oficial_pct"):
        print(f"  Brecha CCL/Oficial: {brechas['ccl_oficial_pct']}%")

    # Renta fija
    rf = output.get("renta_fija", {})
    bonos_ok = sum(1 for v in rf.get("bonos_clave", {}).values() if v.get("ultimo"))
    lecaps = len(rf.get("lecaps_boncaps", []))
    ons = len(rf.get("obligaciones_negociables", []))
    print(f"  Bonos clave: {bonos_ok}/8 con precio")
    print(f"  Lecaps: {lecaps} | ONs: {ons}")

    # Equity
    eq = output.get("equity_ar", {}).get("acciones", {})
    acciones_ok = sum(1 for v in eq.values() if v.get("ultimo"))
    ced = output.get("cedears", {})
    cedears_ok = sum(1 for v in ced.values() if v.get("precio_cedear_ars"))
    fund_ok = sum(1 for v in ced.values() if v.get("fundamentals", {}).get("pe_ratio"))
    print(f"  Acciones AR: {acciones_ok}/{len(eq)} con precio")
    print(f"  CEDEARs: {cedears_ok}/{len(ced)} con precio | {fund_ok} con fundamentals")

    # Índices
    idx = output.get("indices", {})
    idx_ok = sum(1 for v in idx.values() if v.get("ultimo"))
    print(f"  Índices: {idx_ok}/{len(idx)} con precio")

    # Commodities
    cmd = output.get("commodities", {})
    cmd_ok = sum(1 for v in cmd.values() if v.get("ultimo"))
    print(f"  Commodities: {cmd_ok}/{len(cmd)} con precio")

    # Crypto
    cry = output.get("crypto", {})
    cry_ok = sum(1 for v in cry.values() if v.get("ultimo"))
    print(f"  Crypto: {cry_ok}/{len(cry)} con precio")

    # Noticias
    news = output.get("noticias", {})
    ar_news = len(news.get("argentina", []))
    intl_news = len(news.get("internacionales", []))
    print(f"  Noticias: {ar_news} AR + {intl_news} intl")

    # Calculados
    calc = output.get("calculados", {})
    merval_usd = calc.get("merval_usd_ccl")
    if merval_usd:
        print(f"  MERVAL en USD (CCL): {merval_usd}")

    # Metadata
    print(f"\n  Duración: {output['metadata'].get('duracion_segundos', '?')}s")
    errores = output["metadata"].get("errores", [])
    if errores:
        print(f"  Errores: {len(errores)}")
        for e in errores:
            print(f"    - {e}")
    else:
        print("  Errores: ninguno")
    print("=" * 60)


def main():
    setup_logging()
    logger.info("=== Pipeline de datos diarios — Inicio ===")
    start_time = datetime.utcnow()
    errores = []

    # --- Fase 1: Fetches independientes ---
    logger.info("Fase 1: Macro, Renta Fija, Índices/Commodities/Crypto, Noticias...")

    logger.info("--- MACRO ---")
    macro_data, macro_status = fetch_macro()

    logger.info("--- RENTA FIJA ---")
    renta_fija_data, rf_status = fetch_renta_fija()

    logger.info("--- ÍNDICES / COMMODITIES / CRYPTO ---")
    indices_data, commodities_data, crypto_data, icr_status = fetch_indices_commodities_crypto()

    logger.info("--- NOTICIAS ---")
    noticias_data, news_status = fetch_noticias()

    # --- Fase 2: Equity (depende de CCL) ---
    ccl_venta = (macro_data.get("dolar", {}).get("ccl") or {}).get("venta")
    logger.info(f"--- EQUITY (CCL={ccl_venta}) ---")
    equity_ar_data, cedears_data, eq_status = fetch_equity(ccl_venta)

    # --- Fase 3: Campos calculados ---
    logger.info("Calculando métricas derivadas...")
    calculados = _compute_calculated(
        macro_data, indices_data, crypto_data, renta_fija_data, cedears_data
    )

    # --- Componer JSON final ---
    end_time = datetime.utcnow()
    duracion = round((end_time - start_time).total_seconds(), 1)

    output = {
        "metadata": {
            "fecha": date.today().isoformat(),
            "timestamp_utc": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "duracion_segundos": duracion,
            "version": "1.0.0",
            "fuentes": {
                **macro_status,
                "yfinance": {"status": eq_status},
                "yfinance_indices": {"status": icr_status},
                "pyobd": {"status": rf_status},
                "rss_ar": {"status": news_status.get("ar", "unknown")},
                "rss_intl": {"status": news_status.get("intl", "unknown")},
            },
            "errores": errores,
        },
        "macro": macro_data,
        "renta_fija": renta_fija_data,
        "equity_ar": equity_ar_data,
        "cedears": cedears_data,
        "indices": indices_data,
        "commodities": commodities_data,
        "crypto": crypto_data,
        "noticias": noticias_data,
        "calculados": calculados,
    }

    # --- Check de sincronización de fechas ---
    _check_date_sync(output)

    # --- Guardar ---
    filepath = save_json(output)
    logger.info(f"=== Pipeline completo. Archivo: {filepath} ===")
    _print_summary(output)
    return filepath


if __name__ == "__main__":
    main()
