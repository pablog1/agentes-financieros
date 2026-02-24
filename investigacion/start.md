# Plan de Validación de Acceso a Datos — MVP Agentes Financieros

## Objetivo

Construir un script en Python que simule la recolección de datos de un día de mercado completo. El script debe devolver un JSON estructurado con toda la información que tres agentes de IA especializados necesitarían para generar contenido financiero diario enfocado en inversores argentinos.

Si el JSON sale completo y con datos reales, el riesgo de acceso a datos queda validado. Si hay huecos, quedan documentados en el campo `status`.

---

## Contexto del Proyecto

Estamos construyendo una comunidad paga de inversores argentinos ($10-15 USD/mes) con contenido diario generado por agentes de IA. Los agentes son:

- **El Macro**: Analiza contexto Argentina y global (dólar, tasas, inflación, Fed, riesgo país).
- **El Equity Analyst**: Analiza acciones US y CEDEARs (valuaciones, fundamentals, comparaciones).
- **El Estratega de Portafolio**: Propone asignaciones y escenarios de riesgo basados en un simulador.

Este script valida que podemos obtener programáticamente los datos que estos agentes necesitan.

---

## Estructura del JSON Esperado

```json
{
  "fecha": "2025-02-24",
  "macro": {
    "dolar_oficial": 1065.0,
    "dolar_mep": 1180.0,
    "dolar_ccl": 1195.0,
    "dolar_blue": 1210.0,
    "tasa_bcra": 29.0,
    "riesgo_pais": 680,
    "inflacion_mensual": 2.7,
    "reservas_bcra": 28500
  },
  "cedears": [
    {
      "ticker_us": "AAPL",
      "precio_us": 232.5,
      "pe_ratio": 28.3,
      "market_cap": "3.5T",
      "dividend_yield": 0.55,
      "precio_cedear_ars": 15200,
      "ratio_conversion": 10,
      "fuente_us": "alpha_vantage",
      "fuente_byma": "rava"
    }
  ],
  "noticias": [
    {
      "titulo": "...",
      "fuente": "...",
      "url": "...",
      "resumen": "...",
      "relevancia": "macro|equity|portfolio"
    }
  ],
  "status": {
    "macro_ok": true,
    "cedears_us_ok": true,
    "cedears_byma_ok": false,
    "noticias_ok": true,
    "notas": "Detalle de qué falló y por qué"
  }
}
```

---

## Bloques de Datos (ejecutar en este orden)

### Bloque 1 — Contexto Macro Argentina

**Datos requeridos:**
- Dólar: oficial, MEP, CCL, blue (cierre del día)
- Tasa de política monetaria del BCRA
- Riesgo país (EMBI+)
- Inflación mensual última conocida
- Reservas internacionales del BCRA

**APIs a probar (en orden de preferencia):**

| Dato | Fuente primaria | Fuente fallback | Notas |
|------|----------------|-----------------|-------|
| Dólar (todas las cotizaciones) | `https://dolarapi.com/v1/dolares` | Bluelytics (`https://api.bluelytics.com.ar/v2/latest`) | Ambas son gratuitas y sin API key |
| Tasa BCRA | API BCRA (`https://api.bcra.gob.ar/`) | Scraping BCRA | Endpoint: `/estadisticas/v2.0/DatosVariable/6/2025-01-01/2025-12-31` (tasa de política monetaria) |
| Riesgo país | Ámbito Financiero (scraping) | `https://api.argentinadatos.com/v1/finanzas/indices/riesgoCountry` | Verificar si ArgentinaDatos tiene este endpoint activo |
| Inflación | API BCRA | ArgentinaDatos (`https://api.argentinadatos.com/v1/finanzas/indices/inflacion`) | Usar el último dato disponible |
| Reservas BCRA | API BCRA | Scraping BCRA | Endpoint: `/estadisticas/v2.0/DatosVariable/1/2025-01-01/2025-12-31` |

**Criterio de éxito:** Obtener al menos dólar (4 cotizaciones) + tasa BCRA + riesgo país. Inflación y reservas son nice-to-have (cambian menos seguido).

---

### Bloque 2A — Mercado US (Fundamentals de Acciones)

**Datos requeridos para cada ticker:**
- Precio de cierre
- P/E ratio
- Market cap
- Dividend yield

**Tickers a validar (10 CEDEARs más populares):**
`MELI, AAPL, GOOGL, MSFT, GLOB, GGAL, KO, AMZN, TSLA, JPM`

**APIs a probar:**

| Fuente | Endpoint | API Key | Límites |
|--------|----------|---------|---------|
| Alpha Vantage | `GLOBAL_QUOTE` + `OVERVIEW` | Sí (gratis, 25 req/día) | Limitado en plan free, suficiente para MVP |
| Financial Modeling Prep | `/quote` + `/profile` | Sí (gratis, 250 req/día) | Mejor rate limit que Alpha Vantage |

**Notas:**
- Probar ambas APIs y elegir la que tenga mejor cobertura y rate limit.
- Alpha Vantage `GLOBAL_QUOTE` da precio; `OVERVIEW` da P/E, market cap, dividend yield.
- Financial Modeling Prep `/quote` da todo en un solo call.

**Criterio de éxito:** Obtener precio + P/E + market cap de los 10 tickers. Dividend yield es nice-to-have.

---

### Bloque 2B — Precios CEDEARs en BYMA (el más riesgoso)

**Datos requeridos:**
- Precio del CEDEAR en ARS para cada uno de los 10 tickers
- Ratio de conversión CEDEAR/acción

**Fuentes a probar (en orden):**

1. **Rava Bursátil** (`https://www.rava.com/`) — Scraping de la tabla de cotizaciones de CEDEARs. Probar con `requests` + `BeautifulSoup`. Si la data se carga con JS, probar con `playwright` o `selenium`.

2. **GMA Capital** — Ver si exponen datos de CEDEARs públicamente.

3. **IOL (InvertirOnline)** — Tienen API pero requiere cuenta. Si tenés cuenta, probar autenticación y endpoints de cotizaciones.

4. **BYMA Data** (`https://open.bymadata.com.ar/`) — Portal de datos abiertos de BYMA. Verificar si tienen endpoint de cotizaciones de CEDEARs.

5. **Yahoo Finance** — A veces tiene tickers argentinos con sufijo `.BA` (ej: `AAPL.BA`). Probar con `yfinance` library.

**Ratios de conversión:**
Los ratios no cambian frecuentemente. Se pueden hardcodear en un diccionario y actualizar manualmente cuando cambien:

```python
RATIOS_CEDEAR = {
    "MELI": 6,
    "AAPL": 10,
    "GOOGL": 18,
    "MSFT": 10,
    "GLOB": 5,
    "GGAL": 10,
    "KO": 5,
    "AMZN": 72,
    "TSLA": 15,
    "JPM": 4
}
```

> **NOTA:** Estos ratios pueden estar desactualizados. Verificar contra fuente oficial de BYMA antes de usar.

**Criterio de éxito:** Obtener precio en ARS de al menos 5 de los 10 CEDEARs por alguna vía. Si ninguna fuente funciona de forma programática, documentar el hallazgo — es un blocker importante.

---

### Bloque 3 — Noticias y Sentimiento (menor prioridad)

**Datos requeridos:**
- 5 noticias financieras relevantes del día para Argentina/mercados
- (Opcional) Sentimiento social sobre dólar, Merval, o activos puntuales

**Fuentes a probar:**

| Fuente | Uso | Notas |
|--------|-----|-------|
| Tavily AI (`https://tavily.com/`) | Búsqueda curada de noticias | API key gratis con límite. Probar query: "argentina mercado financiero dolar" |
| NewsAPI (`https://newsapi.org/`) | Noticias generales | Plan gratis disponible. Filtrar por fuentes argentinas |
| SocialSearcher | Sentimiento social | Probar mención de "dolar" o "cedear" en últimas 24hs |

**Criterio de éxito:** Obtener al menos 3-5 noticias relevantes del día con título, fuente y resumen. El sentimiento social es totalmente opcional para el MVP.

---

## Instrucciones Técnicas

### Setup
```bash
mkdir finagents-data-validation
cd finagents-data-validation
python -m venv venv
source venv/bin/activate
pip install requests beautifulsoup4 yfinance python-dotenv
```

### Estructura del proyecto
```
finagents-data-validation/
├── .env                  # API keys
├── config.py             # Tickers, ratios, URLs base
├── fetchers/
│   ├── macro.py          # Bloque 1: Dólar, BCRA, riesgo país
│   ├── equities_us.py    # Bloque 2A: Data US via Alpha Vantage / FMP
│   ├── cedears_byma.py   # Bloque 2B: Precios BYMA (scraping)
│   └── news.py           # Bloque 3: Noticias
├── main.py               # Orquesta todo y genera el JSON final
└── output/
    └── market_data_YYYY-MM-DD.json
```

### Cómo ejecutar
```bash
python main.py
```

Debe generar un archivo `output/market_data_YYYY-MM-DD.json` con la estructura definida arriba.

### Variables de entorno necesarias (.env)
```
ALPHA_VANTAGE_API_KEY=tu_key_aqui
FMP_API_KEY=tu_key_aqui
TAVILY_API_KEY=tu_key_aqui
```

---

## Criterios de Éxito Global

| Bloque | Mínimo viable | Ideal |
|--------|--------------|-------|
| Macro Argentina | Dólar (4 tipos) + tasa BCRA + riesgo país | Todo el bloque completo |
| Mercado US | Precio + P/E de 10 tickers | Precio + P/E + market cap + dividend yield |
| CEDEARs BYMA | Precio ARS de al menos 5 tickers | Precio ARS de los 10 tickers |
| Noticias | 3 noticias relevantes | 5 noticias + sentimiento social |

**Si los bloques 1 y 2A funcionan, el proyecto es viable.** El bloque 2B (BYMA) puede resolverse con workarounds (calcular precio teórico del CEDEAR a partir del precio US + ratio + tipo de cambio CCL). El bloque 3 es nice-to-have.

---

## Qué hacer con los resultados

- **Todo verde:** El riesgo de datos está validado. Pasar a la fase 2: probar calidad de contenido generado con estos datos como input.
- **BYMA falla:** No es blocker. Se puede calcular precio teórico: `precio_cedear_teorico = (precio_us / ratio) * dolar_ccl`. No es exacto (ignora spread) pero es útil para análisis.
- **APIs argentinas inestables:** Evaluar si vale la pena mantener fallbacks o si la inestabilidad es un riesgo operativo demasiado alto para un producto diario.
- **Todo rojo:** Replantear el approach. Quizás el contenido debe ser más cualitativo y menos dependiente de data real-time.