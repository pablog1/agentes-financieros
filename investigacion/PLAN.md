# Plan: MVP Validación de Acceso a Datos Financieros

## Contexto

Construir un script Python que recolecte datos de mercado de un día completo y genere un JSON estructurado. Esto valida que podemos obtener programáticamente los datos que 3 agentes de IA (El Macro, El Equity Analyst, El Estratega de Portafolio) necesitarían para generar contenido financiero diario para una comunidad de inversores argentinos.

**Si el JSON sale completo → el riesgo de datos queda validado. Si hay huecos → quedan documentados en `status`.**

---

## Estructura del Proyecto

```
agentes-financieros/
├── start.md              # (ya existe) spec original
├── .env                  # API keys reales (en .gitignore)
├── .env.example          # Template sin secretos
├── .gitignore
├── requirements.txt      # requests, beautifulsoup4, yfinance, python-dotenv
├── config.py             # Constantes: tickers, ratios, URLs, API keys, timeouts
├── fetchers/
│   ├── __init__.py       # vacío
│   ├── macro.py          # Bloque 1: Dólar, BCRA, riesgo país, inflación, reservas
│   ├── equities_us.py    # Bloque 2A: Precio, P/E, market cap, dividend yield (10 tickers)
│   ├── cedears_byma.py   # Bloque 2B: Precios CEDEARs en ARS (yfinance, rava, teórico)
│   └── news.py           # Bloque 3: Noticias (Tavily, NewsAPI)
├── main.py               # Orquesta todo, compone JSON, escribe a disco
└── output/
    └── market_data_YYYY-MM-DD.json
```

---

## Orden de Implementación

| Paso | Archivo | Descripción |
|------|---------|-------------|
| 1 | `.env.example`, `.gitignore`, `requirements.txt` | Setup del proyecto |
| 2 | `config.py` | Constantes centralizadas (URLs, keys, tickers, ratios, timeouts) |
| 3 | `fetchers/__init__.py` | Paquete vacío |
| 4 | `fetchers/macro.py` | **Bloque 1** — El más crítico |
| 5 | `fetchers/equities_us.py` | **Bloque 2A** — Segundo en criticidad |
| 6 | `fetchers/cedears_byma.py` | **Bloque 2B** — El más riesgoso |
| 7 | `fetchers/news.py` | **Bloque 3** — Menor prioridad |
| 8 | `main.py` | Orquestador + composición del JSON |

---

## Detalle por Archivo

### `config.py`
- `load_dotenv()` al importar
- API keys desde env vars: `ALPHA_VANTAGE_API_KEY`, `FMP_API_KEY`, `TAVILY_API_KEY`, `NEWSAPI_KEY`
- `TICKERS = ["MELI", "AAPL", "GOOGL", "MSFT", "GLOB", "GGAL", "KO", "AMZN", "TSLA", "JPM"]`
- `RATIOS_CEDEAR` dict hardcodeado
- URLs centralizadas de todas las APIs/fuentes
- `REQUEST_TIMEOUT = 15` segundos

### `fetchers/macro.py` — Bloque 1
5 funciones de fetch + 1 función pública:

| Función | Fuente primaria | Fallback | Retorna |
|---------|----------------|----------|---------|
| `fetch_dolar()` | dolarapi.com (sin key) | bluelytics (sin key) | 4 cotizaciones (oficial, MEP, CCL, blue) |
| `fetch_tasa_bcra()` | API BCRA variable 6 | None + nota | tasa de política monetaria |
| `fetch_riesgo_pais()` | argentinadatos.com (sin key) | scraping Ámbito | EMBI+ |
| `fetch_inflacion()` | API BCRA | argentinadatos.com | IPC mensual |
| `fetch_reservas_bcra()` | API BCRA variable 1 | None + nota | reservas internacionales |
| **`fetch_macro()`** | Llama a las 5 anteriores | — | Dict unificado + `macro_ok` + `errores_macro` |

**Criterio `macro_ok`:** True si tiene dólar (4 tipos) + tasa BCRA + riesgo país.

### `fetchers/equities_us.py` — Bloque 2A
| Función | Descripción |
|---------|-------------|
| `_fetch_alpha_vantage(ticker)` | 2 requests: GLOBAL_QUOTE (precio) + OVERVIEW (P/E, market cap, div yield). 25 req/día free. |
| `_fetch_fmp(ticker)` | 1 request: /quote/{ticker}. 250 req/día free. |
| `fetch_single_equity(ticker)` | Intenta AV → FMP → None. Retorna dict por ticker. |
| **`fetch_equities()`** | Itera 10 tickers con `sleep(1)` entre calls. Retorna lista + `equities_us_ok` + errores. |

**Criterio `equities_us_ok`:** True si al menos 5 tickers tienen precio.

### `fetchers/cedears_byma.py` — Bloque 2B (más riesgoso)
| Función | Descripción |
|---------|-------------|
| `_fetch_yfinance(ticker)` | yfinance con sufijo `.BA`. Puede no tener todos los CEDEARs. |
| `_fetch_rava(ticker)` | Scraping Rava Bursátil. Frágil, puede requerir JS. |
| `_calcular_precio_teorico(precio_us, ratio, ccl)` | `(precio_us / ratio) * dolar_ccl` — fallback final, siempre funciona si hay datos. |
| **`fetch_cedears(equities_data, dolar_ccl)`** | Intenta yfinance → rava → teórico por cada ticker. |

**Dependencia:** Necesita resultados de Bloque 1 (`dolar_ccl`) y Bloque 2A (`precio_us`).
**Criterio `cedears_byma_ok`:** True si al menos 5 tickers tienen precio en ARS.

### `fetchers/news.py` — Bloque 3
| Función | Descripción |
|---------|-------------|
| `_fetch_tavily()` | POST a Tavily con query "argentina mercado financiero dolar cedear". 5 resultados. |
| `_fetch_newsapi()` | GET a NewsAPI con filtro español, 5 resultados. |
| `_clasificar_relevancia(titulo, resumen)` | Heurístico por keywords → "macro" / "equity" / "portfolio" |
| **`fetch_news()`** | Intenta Tavily → NewsAPI. Retorna lista + `noticias_ok` + errores. |

**Criterio `noticias_ok`:** True si al menos 3 noticias.

### `main.py` — Orquestador
| Función | Descripción |
|---------|-------------|
| `setup_logging()` | Logging a stdout con timestamps |
| `format_market_cap(value)` | `3500000000000` → `"3.5T"` |
| `compose_json(macro, equities, cedears, news)` | Arma el JSON final mergeando datos US + CEDEARs por ticker |
| `save_json(data)` | Escribe a `output/market_data_YYYY-MM-DD.json` con `ensure_ascii=False` |
| **`main()`** | Ejecuta bloques en orden: macro → equities → cedears(depende de ambos) → news → compose → save |

---

## Patrón de Fallback (todos los fetchers)

```
1. Intentar fuente primaria (GET + timeout 15s + raise_for_status)
2. Si falla → log warning → intentar fuente secundaria
3. Si ambas fallan → log error → retornar dict con None + "fuente": "ninguna"
4. NUNCA lanzar excepción al caller
```

Cada función siempre retorna un dict válido (con `None` en campos fallidos).

---

## Diagrama de Dependencias de Ejecución

```
main.py
  ├── fetch_macro()              [independiente]
  ├── fetch_equities()           [independiente]
  ├── fetch_cedears(equities, ccl)  [DEPENDE de macro + equities]
  ├── fetch_news()               [independiente]
  ├── compose_json(todo)         [DEPENDE de todos]
  └── save_json()
```

---

## Verificación

1. **Sin API keys** → `python main.py` → debería obtener dólar + riesgo país (fuentes sin key). Resto en null.
2. **Con Alpha Vantage key** → debería llenar los 10 tickers US.
3. **Verificar CEDEARs** → yfinance debería funcionar para algunos `.BA`. Resto con precio teórico.
4. **Con Tavily key** → debería obtener 5 noticias.
5. **Validar JSON** → `python -m json.tool output/market_data_*.json` y verificar estructura contra spec.
6. **Verificar logs** → no excepciones no capturadas, warnings claros para cada fallback usado.
