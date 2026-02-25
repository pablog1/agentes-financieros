"""
Validador de calidad de reportes de agentes financieros.
Uso: python3 agentes/validar_reporte.py agentes/reportes/manu_2026-02-24.md [--datos output/datos_diarios_2026-02-24.json] [--llm]
"""

import argparse
import glob
import json
import os
import re
import sys

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


# --- Utilidades ---

def _extraer_numeros(texto):
    """Extraer todos los números del texto (soporta formato argentino)."""
    # Buscar patrones como 1.395, 44.904, 2,9, 519, etc.
    numeros = []
    # Formato argentino: 1.234,56 o 1.234
    for match in re.finditer(r'\b(\d{1,3}(?:\.\d{3})*(?:,\d+)?)\b', texto):
        num_str = match.group(1).replace(".", "").replace(",", ".")
        try:
            numeros.append(float(num_str))
        except ValueError:
            pass
    return numeros


def _extraer_numeros_json(data):
    """Extraer recursivamente todos los valores numéricos del JSON de datos."""
    numeros = set()

    def _walk(obj):
        if isinstance(obj, (int, float)):
            numeros.add(float(obj))
            # Agregar variantes redondeadas (conservadoras)
            numeros.add(round(obj))
            numeros.add(round(obj, 1))
            numeros.add(round(obj, 2))
            # Solo redondear a centenas para números muy grandes (>10000)
            # Esto cubre "44.900" por 44904, pero no genera falsos matches en rangos de FX
            if obj > 10000:
                numeros.add(float(int(obj / 100) * 100))
                numeros.add(float(int(obj / 1000) * 1000))
        elif isinstance(obj, dict):
            for v in obj.values():
                _walk(v)
        elif isinstance(obj, list):
            for v in obj:
                _walk(v)
        elif isinstance(obj, str):
            # Extraer números de strings (ej: fechas "2026-02-24" -> 2026, 2, 24)
            for m in re.finditer(r'\b(\d+(?:\.\d+)?)\b', obj):
                try:
                    numeros.add(float(m.group(1)))
                except ValueError:
                    pass

    _walk(data)
    return numeros


def _extraer_numeros_con_contexto(texto):
    """Extraer números del reporte con su contexto circundante."""
    resultados = []
    for match in re.finditer(r'\b(\d{1,3}(?:\.\d{3})*(?:,\d+)?)\b', texto):
        num_str = match.group(1).replace(".", "").replace(",", ".")
        try:
            valor = float(num_str)
        except ValueError:
            continue
        # Capturar contexto (40 chars antes y después)
        start = max(0, match.start() - 40)
        end = min(len(texto), match.end() + 40)
        contexto = texto[start:end].replace("\n", " ").strip()
        resultados.append((valor, match.group(1), contexto))
    return resultados


def _word_count(texto):
    """Contar palabras (excluyendo markdown syntax)."""
    # Remover markdown headers, links, emphasis markers
    clean = re.sub(r'[#*_\[\]()>|`]', ' ', texto)
    clean = re.sub(r'\s+', ' ', clean)
    return len(clean.split())


# --- Checks automáticos ---

def check_extension(reporte, min_words=800, max_words=1200):
    """Verificar extensión del reporte."""
    count = _word_count(reporte)
    if count < min_words:
        return "FAIL", f"Extensión: {count} palabras (mínimo: {min_words})"
    elif count > max_words:
        return "WARN", f"Extensión: {count} palabras (máximo: {max_words})"
    return "OK", f"Extensión: {count} palabras (rango: {min_words}-{max_words})"


def check_disclaimer(reporte, agente="manu"):
    """Verificar que incluya el disclaimer de cierre."""
    if agente == "tomi":
        patterns = [
            r"esto es especulaci[oó]n.{0,5}no inversi[oó]n",
            r"esto no es consejo financiero",
        ]
    elif agente == "vale":
        patterns = [
            r"esto no es asesoramiento financiero",
            r"consult[aá] con tu asesor",
        ]
    elif agente == "santi":
        patterns = [
            r"esto es an[aá]lisis fundamental",
            r"hac[eé] tu propia investigaci[oó]n",
        ]
    elif agente == "sol":
        patterns = [
            r"portafolios modelo.{0,10}ejercicios educativos",
            r"no.{0,5}recomendaciones personalizadas",
        ]
    elif agente == "diego":
        patterns = [
            r"an[aá]lisis t[eé]cnico.{0,10}probabilidades",
            r"siempre us[aá] stop loss",
        ]
    elif agente == "roberto":
        patterns = [
            r"esto no es recomendaci[oó]n",
            r"mi lectura del mercado",
        ]
    elif agente == "editor":
        patterns = [
            r"siete miradas.{0,5}una redacci[oó]n",
            r"las decisiones son tuyas",
        ]
    else:
        patterns = [
            r"esto es análisis.{0,5}no predicción",
            r"el mercado hace lo que quiere",
        ]
    for pattern in patterns:
        if re.search(pattern, reporte, re.IGNORECASE):
            return "OK", "Disclaimer presente"
    return "FAIL", "Disclaimer faltante"


def check_titulo(reporte, agente="manu"):
    """Verificar formato del título (nuevo formato: H1 dinámico + nombre del reporte en subtítulo)."""
    # Nuevo formato: H1 es un titular dinámico, nombre del reporte aparece en línea siguiente
    # como **El Tablero** — [fecha] o similar
    titulo_patterns = {
        "manu": (r'\*\*\s*El Tablero\s*\*\*\s*[—–-]', "El Tablero"),
        "tomi": (r'\*\*\s*Señales\s*\*\*\s*[—–-]', "Señales"),
        "vale": (r'\*\*\s*Renta [Ff]ija [Hh]oy\s*\*\*\s*[—–-]', "Renta Fija Hoy"),
        "santi": (r'\*\*\s*Research Diario\s*\*\*\s*[—–-]', "Research Diario"),
        "sol": (r'\*\*\s*Portafolio\s*\*\*\s*[—–-]', "Portafolio"),
        "diego": (r'\*\*\s*Técnico\s*\*\*\s*[—–-]', "Técnico"),
        "roberto": (r'\*\*\s*(Oportunidad|Sin novedad)\s*\*\*\s*[—–-]', "Oportunidad/Sin novedad"),
        "editor": (r'\*\*\s*La Redacción\s*\*\*\s*[—–-]', "La Redacción"),
    }
    if agente in titulo_patterns:
        pattern, nombre = titulo_patterns[agente]
        # También aceptar el formato viejo por retrocompatibilidad
        old_pattern = pattern.replace(r'\*\*\s*', r'').replace(r'\s*\*\*', r'')
        old_h1_pattern = r'#\s*' + old_pattern
        if re.search(pattern, reporte, re.IGNORECASE):
            # Verificar que hay un H1 dinámico antes
            if re.search(r'^#\s+\S', reporte, re.MULTILINE):
                return "OK", f"Título correcto ({nombre} con titular dinámico)"
            return "WARN", f"Nombre del reporte presente pero falta titular H1"
        if re.search(old_h1_pattern, reporte, re.IGNORECASE):
            return "OK", f"Título correcto ({nombre}, formato clásico)"
        return "FAIL", f"Título incorrecto (debe incluir '**{nombre}** — [fecha]')"
    return "OK", "Check de título no implementado para este agente"


def check_secciones(reporte, agente="manu"):
    """Verificar que todas las secciones obligatorias estén presentes."""
    secciones_por_agente = {
        "manu": [
            ("resumen en 30 segundos", r"resumen.{0,10}30\s*segundo"),
            ("Argentina hoy", r"argentina\s+hoy"),
            ("El mundo que nos afecta", r"mundo.{0,10}(afecta|nos)"),
            ("Conexión de puntos", r"conexi[oó]n.{0,10}punto"),
            ("Lo que viene", r"lo que viene"),
        ],
        "tomi": [
            ("Qué se movió", r"qu[eé]\s+se\s+movi[oó]"),
            ("La oportunidad", r"la\s+oportunidad"),
            ("Aprendizaje", r"aprendizaje"),
            ("Track record", r"track\s*record"),
        ],
        "vale": [
            ("Panorama del día", r"panorama.{0,10}d[ií]a"),
            ("Comparativa de rendimientos", r"comparativa.{0,10}rendimiento"),
            ("Oportunidad o alerta", r"oportunidad.{0,5}(o|y).{0,5}alerta"),
            ("Simulación simple", r"simulaci[oó]n"),
        ],
        "santi": [
            ("Mercado ayer", r"mercado\s+(ayer|hoy)"),
            ("Análisis del día", r"an[aá]lisis.{0,10}d[ií]a"),
            ("Tabla de seguimiento", r"tabla.{0,10}seguimiento"),
            ("Scorecard", r"scorecard"),
        ],
        "sol": [
            ("Lectura del entorno", r"lectura.{0,10}entorno"),
            ("Portafolio modelo", r"portafolio.{0,10}modelo"),
            ("Movimiento de la semana", r"movimiento.{0,10}semana"),
            ("Escenario de riesgo", r"escenario.{0,10}riesgo"),
            ("Matriz de correlación", r"matriz.{0,10}correlaci[oó]n"),
        ],
        "diego": [
            ("Vista de mercado", r"vista.{0,10}mercado"),
            ("Setups activos", r"setups?\s+activo"),
            ("Gestión de trades", r"gesti[oó]n.{0,10}trade"),
            ("Lección técnica", r"lecci[oó]n.{0,10}t[eé]cnic"),
        ],
        "roberto": [
            ("Lectura política", r"lectura.{0,10}(pol[ií]tic|macro)"),
            ("La tesis", r"la\s+tesis"),
            ("Bitácora", r"bit[aá]cora"),
            ("Perspectiva", r"perspectiva"),
        ],
        "editor": [
            ("El día en un párrafo", r"(el\s+)?d[ií]a\s+en\s+un\s+p[aá]rrafo"),
            ("Lo que dice el equipo", r"(lo\s+)?que\s+dice\s+el\s+equipo"),
            ("La tensión del día", r"tensi[oó]n.{0,10}d[ií]a"),
            ("Lo que vigilo mañana", r"(lo\s+)?que\s+vigilo"),
        ],
    }

    if agente not in secciones_por_agente:
        return "OK", "Check de secciones no implementado para este agente"

    secciones = secciones_por_agente[agente]

    encontradas = 0
    faltantes = []
    for nombre, pattern in secciones:
        if re.search(pattern, reporte, re.IGNORECASE):
            encontradas += 1
        else:
            faltantes.append(nombre)

    if encontradas == len(secciones):
        return "OK", f"{encontradas}/{len(secciones)} secciones detectadas"
    else:
        return "FAIL", f"{encontradas}/{len(secciones)} secciones. Faltan: {', '.join(faltantes)}"


def check_fuentes(reporte):
    """Verificar que se citen fuentes (en paréntesis, en prosa, o como mención directa)."""
    fuentes_conocidas = r'(?:DolarAPI|Yahoo\s*Finance|BCRA|INDEC|ArgentinaDatos|Bloomberg|CNBC|Ámbito|Cronista|Infobae|cálculo propio|JP\s*Morgan)'
    # Patrón 1: (fuente: X)
    fuentes_paren = re.findall(r'\(fuente:?\s*[^)]+\)', reporte, re.IGNORECASE)
    # Patrón 2: "según X", "datos de X"
    fuentes_prosa = re.findall(r'(?:según|datos de|fuente:)\s+' + fuentes_conocidas, reporte, re.IGNORECASE)
    # Patrón 3: mención directa de fuente en contexto de datos
    fuentes_mencion = re.findall(fuentes_conocidas, reporte, re.IGNORECASE)
    # Contar fuentes únicas mencionadas (al menos tienen que nombrar la fuente)
    fuentes_unicas = set()
    for f in fuentes_paren:
        fuentes_unicas.add(f.lower())
    for f in fuentes_prosa:
        fuentes_unicas.add(f.lower())
    for f in fuentes_mencion:
        fuentes_unicas.add(f.lower().strip())

    count_menciones = len(fuentes_mencion)
    count_unicas = len(fuentes_unicas)

    if count_unicas >= 2:
        return "OK", f"{count_unicas} fuentes distintas mencionadas ({count_menciones} menciones)"
    elif count_unicas >= 1:
        return "WARN", f"Solo {count_unicas} fuente mencionada (se esperan ≥2)"
    return "FAIL", "No se encontraron menciones de fuentes de datos"


def check_datos_vs_json(reporte, data):
    """Verificar datos del reporte contra el JSON fuente."""
    macro = data.get("macro", {})
    verificaciones = []
    errores = []

    # Riesgo país
    rp = macro.get("riesgo_pais", {}).get("valor")
    if rp:
        if str(rp) in reporte or str(int(rp)) in reporte:
            verificaciones.append(f"Riesgo país ({rp}): OK")
        else:
            # Puede no mencionarse, eso es OK si no es relevante
            verificaciones.append(f"Riesgo país ({rp}): no mencionado")

    # Dólar oficial venta
    oficial = macro.get("dolar", {}).get("oficial", {}).get("venta")
    if oficial:
        oficial_str = f"{int(oficial):,}".replace(",", ".")
        if oficial_str in reporte or str(int(oficial)) in reporte:
            verificaciones.append(f"Dólar oficial ({oficial}): OK")

    # Dólar blue venta
    blue = macro.get("dolar", {}).get("blue", {}).get("venta")
    if blue:
        if str(int(blue)) in reporte:
            verificaciones.append(f"Dólar blue ({blue}): OK")

    # Inflación
    infl = macro.get("inflacion", {}).get("mensual_ultimo", {}).get("valor")
    if infl:
        infl_str = str(infl).replace(".", ",")
        if infl_str in reporte or str(infl) in reporte:
            verificaciones.append(f"Inflación ({infl}%): OK")

    # Reservas
    reservas = macro.get("bcra", {}).get("reservas", {}).get("valor")
    if reservas:
        res_int = int(reservas)
        if str(res_int) in reporte or f"{res_int:,}".replace(",", ".") in reporte:
            verificaciones.append(f"Reservas ({reservas}M): OK")

    # Buscar datos inventados (números que no están en el JSON)
    numeros_json = _extraer_numeros_json(data)
    numeros_reporte = _extraer_numeros_con_contexto(reporte)

    # Números que ignoramos por ser demasiado comunes o ambiguos
    IGNORAR_MENORES_A = 20  # 1, 2, 3... son muy comunes en prosa
    IGNORAR_EXACTOS = {100, 200, 300, 500, 1000}  # Números redondos genéricos

    # Patrones de contexto que excluimos (temporales, décadas, ordinales)
    CONTEXTO_EXCLUIR = re.compile(
        r'(?:'
        r"(?:los|la|las|el)\s*['\u2019]?\d{2}\b"  # "los '90", "los 80"
        r'|\d+\s*(?:días?|semanas?|meses?|horas?|minutos?|años?|hs)\b'  # "45 días"
        r'|\d+\s*(?:de\s+)?(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)'  # fechas en prosa
        r')',
        re.IGNORECASE
    )

    sospechosos = []
    for valor, original, contexto in numeros_reporte:
        if valor < IGNORAR_MENORES_A:
            continue
        if valor in IGNORAR_EXACTOS:
            continue
        # Excluir por contexto temporal/décadas
        if CONTEXTO_EXCLUIR.search(contexto):
            continue
        # Verificar si el número está en el JSON (con tolerancia del 0.5%)
        # Comparar tanto el valor como su absoluto (el regex no captura signos negativos)
        encontrado = False
        for json_num in numeros_json:
            if json_num == 0:
                continue
            abs_json = abs(json_num)
            if abs_json < 0.001:
                continue
            # Match directo con tolerancia
            if abs(valor - json_num) / max(abs_json, 1) < 0.005:
                encontrado = True
                break
            # Match por valor absoluto (para negativos como -40,6% → 40,6)
            if abs(valor - abs_json) / max(abs_json, 1) < 0.005:
                encontrado = True
                break
        if not encontrado:
            sospechosos.append((valor, original, contexto))

    if sospechosos:
        for val, orig, ctx in sospechosos:
            errores.append(f"Posible dato inventado: {orig} → \"{ctx}\"")

    datos_ok = len(verificaciones)
    n_sosp = len(sospechosos)

    if n_sosp > 3:
        status = "FAIL"
    elif n_sosp > 0:
        status = "WARN"
    elif datos_ok >= 3:
        status = "OK"
    elif datos_ok >= 1:
        status = "WARN"
    else:
        status = "FAIL"

    detail = f"Datos verificados: {datos_ok} coincidencias"
    if sospechosos:
        detail += f" | {n_sosp} número(s) sospechoso(s) no encontrado(s) en JSON"
    if errores:
        detail += f"\n           Alertas: {'; '.join(errores[:5])}"
        if len(errores) > 5:
            detail += f" ... y {len(errores) - 5} más"

    return status, detail, verificaciones


def check_anti_hallucination(reporte, data):
    """Detectar patrones comunes de alucinación en reportes financieros."""
    alertas = []

    # --- 1. Años históricos no presentes en los datos ---
    # Extraer todos los años mencionados en el reporte
    anios_reporte = set(int(m) for m in re.findall(r'\b((?:19|20)\d{2})\b', reporte))
    # Extraer años que sí están en el JSON (de fechas, timestamps, etc.)
    json_str = json.dumps(data)
    anios_json = set(int(m) for m in re.findall(r'\b((?:19|20)\d{2})\b', json_str))
    # Años en el reporte que no están en el JSON
    anios_inventados = anios_reporte - anios_json
    for anio in sorted(anios_inventados):
        # Buscar el contexto donde aparece el año
        for match in re.finditer(r'\b' + str(anio) + r'\b', reporte):
            start = max(0, match.start() - 50)
            end = min(len(reporte), match.end() + 50)
            ctx = reporte[start:end].replace("\n", " ").strip()
            alertas.append(f"Año histórico sin respaldo en datos: {anio} → \"{ctx}\"")
            break  # Solo una alerta por año

    # --- 2. Claims de yield/rendimiento/maturity sin datos ---
    yield_patterns = [
        (r'rendimiento\s+(?:impl[ií]cito|estimado|anual)?\s*(?:del?\s*)?\d+[.,]\d+\s*%', "Rendimiento/yield con número específico"),
        (r'yield\s+(?:del?\s*)?\d+[.,]\d+\s*%', "Yield con número específico"),
        (r'maturity\s+(?:en\s+)?(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(?:de\s+)?\d{4}', "Fecha de maturity específica"),
        (r'vencimiento\s+(?:en\s+)?(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(?:de\s+)?\d{4}', "Fecha de vencimiento específica"),
        (r'tir\s+(?:del?\s*)?\d+[.,]\d+\s*%', "TIR con número específico"),
        (r'spread\s+(?:sobre\s+)?\w+\s+(?:de\s+)?\d+\s+(?:puntos|bps|basis)', "Spread sobre referencia externa"),
    ]
    for pattern, desc in yield_patterns:
        match = re.search(pattern, reporte, re.IGNORECASE)
        if match:
            # Verificar si hay datos de yield/maturity en el JSON
            has_yield_data = "yield" in json_str.lower() or "rendimiento" in json_str.lower() or "maturity" in json_str.lower()
            if not has_yield_data:
                ctx = match.group()
                alertas.append(f"{desc} (sin datos de yield en JSON): \"{ctx}\"")

    # --- 3. Eventos futuros no respaldados por noticias ---
    evento_patterns = [
        (r'(?:pr[oó]xima|la|esta)\s+(?:semana|lunes|martes|miércoles|jueves|viernes).*?(?:licitaci[oó]n|subasta|reuni[oó]n|anuncio)', "Evento futuro"),
        (r'licitaci[oó]n\s+del\s+tesoro', "Licitación del Tesoro"),
        (r'reuni[oó]n\s+(?:del?\s+)?(?:BCRA|directorio|Fed|FOMC)', "Reunión de organismo"),
        (r'(?:el|este)\s+(?:próximo\s+)?(?:lunes|martes|miércoles|jueves|viernes)\s+(?:se\s+)?(?:publica|sale|vence|licita)', "Evento futuro específico"),
    ]
    noticias_str = json.dumps(data.get("noticias", {}), ensure_ascii=False).lower()
    for pattern, desc in evento_patterns:
        match = re.search(pattern, reporte, re.IGNORECASE)
        if match:
            # Verificar si el evento está mencionado en las noticias
            evento_texto = match.group().lower()
            palabras_clave = [p for p in evento_texto.split() if len(p) > 4]
            respaldado = any(p in noticias_str for p in palabras_clave)
            if not respaldado:
                alertas.append(f"{desc} sin respaldo en noticias: \"{match.group()}\"")

    # --- 4. Comparaciones históricas con números específicos ---
    hist_patterns = [
        r'(?:en|durante|el|desde|como en)\s+(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(?:de\s+)?(?:19|20)\d{2}\s+(?:cuando|el|la|los)',
        r'(?:lleg[oó]|cay[oó]|subi[oó]|cotiz[oó]|estaba)\s+(?:a|en)\s+(?:USD\s+)?\d+[.,]?\d*\s+(?:centavos|puntos|d[oó]lares)',
        r'multiplic(?:aron|ó)\s+por\s+\d+[.,]?\d*x?\s+en\s+(?:menos\s+de\s+)?\d+',
    ]
    for pattern in hist_patterns:
        match = re.search(pattern, reporte, re.IGNORECASE)
        if match:
            alertas.append(f"Comparación histórica con datos específicos: \"{match.group()}\"")

    # --- 5. Países/referencias externas sin datos ---
    ref_externa_patterns = [
        (r'prima\s+(?:de\s+)?\w+\s+(?:puntos?\s+)?sobre\s+(?:Brasil|México|Colombia|Chile|Perú)', "Prima sobre país sin datos"),
        (r'(?:spread|brecha)\s+(?:con|vs|versus|contra)\s+(?:Brasil|México|Colombia|Chile|Perú)', "Spread vs país sin datos"),
    ]
    for pattern, desc in ref_externa_patterns:
        match = re.search(pattern, reporte, re.IGNORECASE)
        if match:
            pais = re.search(r'(Brasil|México|Colombia|Chile|Perú)', match.group(), re.IGNORECASE)
            pais_nombre = pais.group() if pais else "externo"
            if pais_nombre.lower() not in json_str.lower():
                alertas.append(f"{desc}: \"{match.group()}\"")

    # Resultado
    if not alertas:
        return "OK", "Sin patrones de alucinación detectados", []

    status = "FAIL" if len(alertas) >= 2 else "WARN"
    detail = f"{len(alertas)} patrón(es) de alucinación detectado(s)"
    return status, detail, alertas


def check_no_recomendaciones(reporte):
    """Verificar que no haya recomendaciones de compra/venta."""
    patterns = [
        r'\b(comprá|vendé|invertí en|poné plata en)\b',
        r'\b(recomiendo|recomendamos|te sugiero)\s+(comprar|vender|invertir)',
        r'\b(es momento de comprar|hay que comprar|conviene comprar)\b',
    ]
    for pattern in patterns:
        match = re.search(pattern, reporte, re.IGNORECASE)
        if match:
            return "WARN", f"Posible recomendación detectada: '{match.group()}'"
    return "OK", "Sin recomendaciones de compra/venta detectadas"


# --- Validación LLM ---

def check_llm(reporte, data, model=None, agente="manu"):
    """Validación de calidad via LLM (OpenRouter)."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None, "OPENROUTER_API_KEY no configurada, skip LLM check"

    try:
        from openai import OpenAI
    except ImportError:
        return None, "openai library no instalada, skip LLM check"

    model = model or os.getenv("OPENROUTER_MODEL_VALIDATOR", os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4"))

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    agent_descriptions = {
        "manu": "Manu (Analista Macroeconómico, 38 años, analítico, directo, algo cínico)",
        "tomi": "Tomi (Crypto y Tendencias de Alto Riesgo, 24 años, energético, directo, crypto-bullish pero transparente con riesgos)",
        "vale": "Vale (Analista de Renta Fija, 52 años, prudente, metódica, ultra conservadora, tono maternal)",
        "santi": "Santi (Analista de Acciones y CEDEARs, 32 años, nerd de fundamentals, entusiasta pero riguroso)",
        "sol": "Sol (Estratega de Portafolio, 41 años, estructurada, metodológica, piensa en sistemas y diversificación)",
        "diego": "Diego (Analista Técnico, 35 años, frío, calculador, disciplinado, habla en probabilidades)",
        "roberto": "Roberto (Oportunista Macro, 45 años, experimentado, cínico, contrarian, piensa en asimetrías)",
    }
    agent_desc = agent_descriptions.get(agente, f"agente '{agente}'")

    admin_prompt = (
        "Sos el Agente Admin de un equipo de analistas financieros IA. "
        "Tu trabajo es evaluar la calidad de los reportes antes de publicarlos.\n\n"
        f"Evaluá el siguiente reporte del agente {agent_desc} considerando:\n\n"
        "1. **Tono** (1-10): ¿Es consistente con su personalidad? ¿Suena auténtico?\n"
        "2. **Coherencia** (1-10): ¿Hay contradicciones internas? ¿Los argumentos fluyen lógicamente?\n"
        "3. **Datos** (1-10): ¿Todos los números citados coinciden con los datos provistos? ¿Hay datos que parezcan inventados?\n"
        "4. **Calidad editorial** (1-10): ¿Es publicable? ¿La prosa es fluida? ¿Las secciones están bien desarrolladas?\n"
        "5. **Valor agregado** (1-10): ¿El análisis va más allá de listar datos? ¿Agrega insight real?\n\n"
        "REGLAS PARA EVALUAR DATOS (sé ESTRICTO):\n"
        "- El redondeo razonable NO es un error (ej: 32,6875% → 32,69% es aceptable).\n"
        "- Los datos extraídos de titulares de noticias con cita de fuente son válidos.\n"
        "- Las métricas calculadas deben estar correctamente etiquetadas como 'cálculo propio', pero NO penalices por usarlas si están bien señalizadas.\n"
        "- HALLUCINATIONS: Buscá activamente datos que NO estén en el JSON. "
        "Comparaciones históricas como 'hace un año valía X', 'en 2024 fue Y', 'históricamente sube/baja' "
        "son INVENTADAS si no hay datos históricos en el JSON provisto. "
        "Penalizá FUERTE (máximo 6/10 en Datos) si encontrás cualquier dato, comparación o afirmación que no esté respaldada por los datos provistos.\n"
        "- También penalizá si el reporte convierte precios a pesos argentinos sin que eso sea relevante para su audiencia.\n\n"
        'Respondé ÚNICAMENTE en este formato JSON (sin markdown, sin texto adicional):\n'
        '{"tono": {"score": N, "comentario": "..."}, '
        '"coherencia": {"score": N, "comentario": "..."}, '
        '"datos": {"score": N, "comentario": "..."}, '
        '"calidad_editorial": {"score": N, "comentario": "..."}, '
        '"valor_agregado": {"score": N, "comentario": "..."}, '
        '"rating_global": N.N, '
        '"aprobado": true/false, '
        '"sugerencias": ["...", "..."]}'
    )

    # Preparar datos resumidos para el admin (incluir TODOS los datos relevantes)
    # Renta fija: resumir bonos clave y ONs top por volumen
    rf = data.get("renta_fija", {})
    rf_resumen = {"bonos_clave": rf.get("bonos_clave", {})}
    ons = rf.get("obligaciones_negociables", [])
    rf_resumen["obligaciones_negociables_top"] = sorted(
        ons, key=lambda x: x.get("volumen") or 0, reverse=True
    )[:10]

    # Equity AR: resumir top movers
    eq = data.get("equity_ar", {})
    acciones = eq.get("acciones", {})
    eq_resumen = {
        k: {"ultimo": v.get("ultimo"), "variacion_pct": v.get("variacion_pct"), "nombre": v.get("nombre")}
        for k, v in sorted(acciones.items(), key=lambda x: abs(x[1].get("variacion_pct") or 0), reverse=True)[:10]
    }

    # Noticias: incluir titulares para verificar referencias
    noticias = data.get("noticias", {})
    noticias_resumen = {
        "argentina": [{"titulo": n.get("titulo"), "fuente": n.get("fuente")} for n in noticias.get("argentina", [])[:10]],
        "internacionales": [{"titulo": n.get("titulo"), "fuente": n.get("fuente")} for n in noticias.get("internacionales", [])[:10]],
    }

    datos_resumen = json.dumps({
        "macro": data.get("macro", {}),
        "indices": data.get("indices", {}),
        "commodities": data.get("commodities", {}),
        "crypto": {k: {"ultimo": v.get("ultimo"), "variacion_pct": v.get("variacion_pct")} for k, v in data.get("crypto", {}).items()},
        "calculados": data.get("calculados", {}),
        "renta_fija": rf_resumen,
        "equity_ar": eq_resumen,
        "noticias": noticias_resumen,
    }, ensure_ascii=False, indent=2)

    user_msg = f"""## REPORTE A EVALUAR:

{reporte}

## DATOS DEL DÍA (para verificar exactitud):

{datos_resumen}"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": admin_prompt},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=1500,
            temperature=0.3,
        )

        result_text = response.choices[0].message.content.strip()
        # Limpiar posible markdown wrapping
        result_text = re.sub(r'^```json\s*', '', result_text)
        result_text = re.sub(r'\s*```$', '', result_text)

        result = json.loads(result_text)
        return result, "ok"
    except json.JSONDecodeError as e:
        return None, f"Error parseando respuesta LLM: {e}\nRespuesta: {result_text[:200]}"
    except Exception as e:
        return None, f"Error en LLM check: {e}"


# --- Main ---

def validar(reporte_path, datos_path=None, use_llm=False, llm_model=None):
    """Ejecutar todas las validaciones sobre un reporte."""
    with open(reporte_path, "r", encoding="utf-8") as f:
        reporte = f.read()

    # Detectar agente del filename
    basename = os.path.basename(reporte_path)
    agente = basename.split("_")[0]

    # Cargar datos
    if datos_path is None:
        # Intentar encontrar el JSON que corresponde a la fecha del reporte
        fecha_match = re.search(r'(\d{4}-\d{2}-\d{2})', basename)
        if fecha_match:
            fecha = fecha_match.group(1)
            candidate = os.path.join(OUTPUT_DIR, f"datos_diarios_{fecha}.json")
            if os.path.exists(candidate):
                datos_path = candidate

        if datos_path is None:
            # Fallback: último JSON disponible
            pattern = os.path.join(OUTPUT_DIR, "datos_diarios_*.json")
            files = sorted(glob.glob(pattern))
            if files:
                datos_path = files[-1]

    data = None
    if datos_path and os.path.exists(datos_path):
        with open(datos_path, "r", encoding="utf-8") as f:
            data = json.load(f)

    # Ejecutar checks
    print(f"\n{'=' * 60}")
    print(f"VALIDACIÓN — {agente} — {basename}")
    print(f"{'=' * 60}")
    print()

    results = []

    # Checks automáticos
    print("CHECKS AUTOMÁTICOS:")

    # Extensión depende del agente
    extension_limites = {
        "manu": (800, 1200),
        "tomi": (500, 800),
        "vale": (600, 900),
        "santi": (700, 1200),
        "sol": (1000, 1500),
        "diego": (600, 1000),
        "roberto": (200, 1200),  # 200 for "sin novedad", 1200 for full report
        "editor": (700, 1200),
    }
    min_w, max_w = extension_limites.get(agente, (800, 1200))
    ext_check = check_extension(reporte, min_words=min_w, max_words=max_w)

    checks = [
        ext_check,
        check_disclaimer(reporte, agente),
        check_titulo(reporte, agente),
        check_secciones(reporte, agente),
        check_fuentes(reporte),
        check_no_recomendaciones(reporte),
    ]

    for status, detail in checks:
        tag = f"[{status}]"
        print(f"  {tag:<8} {detail}")
        results.append((status, detail))

    # Check datos vs JSON
    if data:
        status, detail, verificaciones = check_datos_vs_json(reporte, data)
        print(f"  [{status}]   {detail}")
        for v in verificaciones:
            print(f"           {v}")
        results.append((status, detail))

        # Check anti-alucinación
        ah_status, ah_detail, ah_alertas = check_anti_hallucination(reporte, data)
        print(f"  [{ah_status}]   Anti-alucinación: {ah_detail}")
        for a in ah_alertas:
            print(f"           ⚠ {a}")
        results.append((ah_status, ah_detail))
    else:
        print(f"  [SKIP]  Datos vs JSON: no se encontró archivo de datos")

    # Check LLM
    if use_llm:
        print()
        print("CHECK LLM (Admin):")
        llm_result, llm_status = check_llm(reporte, data or {}, llm_model, agente)
        if llm_result:
            for key in ["tono", "coherencia", "datos", "calidad_editorial", "valor_agregado"]:
                item = llm_result.get(key, {})
                score = item.get("score", "?")
                comment = item.get("comentario", "")
                print(f"  {key.replace('_', ' ').title()}: {score}/10 — \"{comment}\"")

            rating = llm_result.get("rating_global", "?")
            aprobado = llm_result.get("aprobado", False)
            print(f"\n  RATING GLOBAL: {rating}/10")
            print(f"  RESULTADO: {'APROBADO' if aprobado else 'NECESITA AJUSTES'}")

            sugerencias = llm_result.get("sugerencias", [])
            if sugerencias:
                print(f"\n  SUGERENCIAS:")
                for s in sugerencias:
                    print(f"    - {s}")
        else:
            print(f"  [SKIP]  {llm_status}")

    # Resumen
    fails = sum(1 for s, _ in results if s == "FAIL")
    warns = sum(1 for s, _ in results if s == "WARN")
    print()
    if fails:
        print(f"RESULTADO: {fails} FAIL(s), {warns} WARN(s)")
    elif warns:
        print(f"RESULTADO: OK con {warns} advertencia(s)")
    else:
        print("RESULTADO: TODOS LOS CHECKS OK")
    print(f"{'=' * 60}")

    return fails == 0


def main():
    parser = argparse.ArgumentParser(description="Validar reporte de agente financiero")
    parser.add_argument("reporte", help="Path al reporte .md a validar")
    parser.add_argument("--datos", default=None, help="Path al JSON diario (auto-detect si no se especifica)")
    parser.add_argument("--llm", action="store_true", help="Incluir validación LLM (usa OpenRouter)")
    parser.add_argument("--model", default=None, help="Modelo para validación LLM")
    args = parser.parse_args()

    if not os.path.exists(args.reporte):
        print(f"ERROR: No existe {args.reporte}")
        sys.exit(1)

    ok = validar(args.reporte, args.datos, args.llm, args.model)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
