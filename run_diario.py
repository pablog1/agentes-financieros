"""
Pipeline diario completo: extracción de datos → generación de reportes → validación.
Uso: python3 run_diario.py [--agentes manu] [--skip-datos] [--skip-validacion] [--llm]
"""

import argparse
import sys
import os
import time

BASE_DIR = os.path.dirname(__file__)
sys.path.insert(0, BASE_DIR)


def paso_datos(skip=False):
    """Paso 1: Extraer datos del día."""
    print("\n" + "=" * 60)
    print("PASO 1: EXTRACCIÓN DE DATOS")
    print("=" * 60)

    if skip:
        # Buscar el último JSON disponible
        from pipeline.config import OUTPUT_DIR
        import glob

        pattern = os.path.join(OUTPUT_DIR, "datos_diarios_*.json")
        files = sorted(glob.glob(pattern))
        if not files:
            print("ERROR: No hay datos previos y se pidió --skip-datos")
            return None
        path = files[-1]
        print(f"  Usando datos existentes: {path}")
        return path

    from pipeline.main import main as pipeline_main
    path = pipeline_main()
    return path


def paso_generacion(agentes, datos_path):
    """Paso 2: Generar reportes para cada agente."""
    print("\n" + "=" * 60)
    print("PASO 2: GENERACIÓN DE REPORTES")
    print("=" * 60)

    from agentes.generar_reporte import generar

    reportes = {}
    for agente in agentes:
        print(f"\n--- Generando: {agente} ---")
        try:
            path = generar(agente, datos_path)
            reportes[agente] = path
        except Exception as e:
            print(f"  ERROR generando {agente}: {e}")
            reportes[agente] = None

    return reportes


def paso_validacion(reportes, datos_path, use_llm=False):
    """Paso 3: Validar cada reporte generado."""
    print("\n" + "=" * 60)
    print("PASO 3: VALIDACIÓN DE REPORTES")
    print("=" * 60)

    from agentes.validar_reporte import validar

    resultados = {}
    for agente, reporte_path in reportes.items():
        if reporte_path is None:
            print(f"\n--- {agente}: SKIP (no se generó) ---")
            resultados[agente] = False
            continue

        ok = validar(reporte_path, datos_path, use_llm=use_llm)
        resultados[agente] = ok

    return resultados


def resumen_final(datos_path, reportes, resultados, duracion):
    """Imprimir resumen final del pipeline completo."""
    print("\n" + "=" * 60)
    print("RESUMEN FINAL")
    print("=" * 60)
    print(f"  Datos: {datos_path}")
    print(f"  Duración total: {duracion:.1f}s")
    print()

    for agente in reportes:
        reporte = reportes.get(agente)
        ok = resultados.get(agente, False)
        estado = "OK" if ok else "FAIL"
        path = reporte or "(no generado)"
        print(f"  [{estado}] {agente}: {path}")

    total = len(reportes)
    aprobados = sum(1 for v in resultados.values() if v)
    print(f"\n  Aprobados: {aprobados}/{total}")
    print("=" * 60)

    return all(resultados.values())


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline diario: datos → reportes → validación"
    )
    parser.add_argument(
        "--agentes",
        nargs="+",
        default=["manu", "tomi", "vale", "santi", "sol", "diego", "roberto"],
        help="Agentes a generar (default: todos)",
    )
    parser.add_argument(
        "--skip-datos",
        action="store_true",
        help="Usar datos existentes en vez de re-extraer",
    )
    parser.add_argument(
        "--skip-validacion",
        action="store_true",
        help="No ejecutar validación",
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Incluir validación LLM (más lento, usa OpenRouter)",
    )
    parser.add_argument(
        "--datos",
        default=None,
        help="Path específico al JSON de datos",
    )
    args = parser.parse_args()

    start = time.time()

    # Paso 1: Datos
    if args.datos:
        datos_path = args.datos
        print(f"Usando datos especificados: {datos_path}")
    else:
        datos_path = paso_datos(skip=args.skip_datos)

    if not datos_path or not os.path.exists(datos_path):
        print("ERROR: No se pudieron obtener datos. Abortando.")
        sys.exit(1)

    # Paso 2: Generación
    reportes = paso_generacion(args.agentes, datos_path)

    # Paso 3: Validación
    if args.skip_validacion:
        resultados = {a: True for a in args.agentes}
        print("\n(Validación omitida con --skip-validacion)")
    else:
        resultados = paso_validacion(reportes, datos_path, use_llm=args.llm)

    # Resumen
    duracion = time.time() - start
    ok = resumen_final(datos_path, reportes, resultados, duracion)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
