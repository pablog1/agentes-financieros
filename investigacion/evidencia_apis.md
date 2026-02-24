# Evidencia de APIs Gratuitas - 24 Feb 2026

Resultado de testear las 6 APIs gratuitas que funcionan correctamente.

---

## 1. DolarAPI

**Base URL:** `https://dolarapi.com/v1`

### Evidencia

| Tipo | Compra | Venta | Actualización |
|------|--------|-------|---------------|
| Oficial | $1.340 | $1.390 | 24/02 09:53 |
| Blue | $1.405 | $1.425 | 24/02 13:56 |
| Bolsa (MEP) | $1.398,80 | $1.398,80 | 24/02 13:56 |
| CCL | $1.443,70 | $1.443,70 | 24/02 13:56 |
| Mayorista | $1.366 | $1.375 | 24/02 11:00 |
| Cripto | $1.444,90 | $1.445 | 24/02 13:56 |
| Tarjeta | $1.742 | $1.807 | 24/02 09:53 |

### Endpoints disponibles

```
GET /v1/dolares                    # Todas las cotizaciones del dólar
GET /v1/dolares/blue               # Solo dólar blue
GET /v1/dolares/oficial            # Solo dólar oficial
GET /v1/dolares/bolsa              # Solo dólar bolsa (MEP)
GET /v1/dolares/contadoconliqui    # Solo CCL
GET /v1/dolares/mayorista          # Solo mayorista
GET /v1/dolares/cripto             # Solo cripto
GET /v1/dolares/tarjeta            # Solo tarjeta
GET /v1/cotizaciones               # Todas las monedas (USD, EUR, BRL, etc.)
GET /v1/cotizaciones/eur           # Euro
GET /v1/cotizaciones/brl           # Real brasileño
```

### Uso en Python

```python
import requests

# Todas las cotizaciones del dólar
r = requests.get("https://dolarapi.com/v1/dolares")
cotizaciones = r.json()
# [{"moneda": "USD", "casa": "oficial", "compra": 1340, "venta": 1390, ...}, ...]

# Solo dólar blue
r = requests.get("https://dolarapi.com/v1/dolares/blue")
blue = r.json()
# {"moneda": "USD", "casa": "blue", "compra": 1405, "venta": 1425, ...}

# Brecha cambiaria
oficial = requests.get("https://dolarapi.com/v1/dolares/oficial").json()
blue = requests.get("https://dolarapi.com/v1/dolares/blue").json()
brecha = (blue["venta"] / oficial["venta"] - 1) * 100
```

### Características
- Sin API key
- Sin rate limit conocido
- Respuesta JSON directa (lista o dict)
- Actualización en tiempo real durante horario de mercado

---

## 2. Bluelytics

**Base URL:** `https://api.bluelytics.com.ar/v2`

### Evidencia

| Tipo | Compra | Venta | Promedio |
|------|--------|-------|----------|
| Oficial | $1.342 | $1.393 | $1.367,50 |
| Blue | $1.405 | $1.425 | $1.415 |
| Euro oficial | $1.459 | $1.514 | $1.486,50 |
| Euro blue | $1.527 | $1.549 | $1.538 |

Última actualización: 24/02/2026 11:30:56

### Endpoints disponibles

```
GET /v2/latest           # Cotización actual (USD y EUR, oficial y blue)
GET /v2/evolution.json   # Serie histórica completa de cotizaciones
```

### Uso en Python

```python
import requests

# Cotización actual
r = requests.get("https://api.bluelytics.com.ar/v2/latest")
data = r.json()
# data["blue"]["value_sell"]  -> 1425 (venta blue)
# data["oficial"]["value_avg"] -> 1367.5 (promedio oficial)
# data["blue_euro"]["value_sell"] -> 1549 (euro blue venta)

# Serie histórica
r = requests.get("https://api.bluelytics.com.ar/v2/evolution.json")
historia = r.json()
# Lista de registros con fecha + valores blue/oficial
```

### Características
- Sin API key
- Incluye EUR además de USD
- Provee valor promedio (avg) además de compra/venta
- Endpoint de evolución histórica disponible

---

## 3. API BCRA (Banco Central)

**Base URL:** `https://api.bcra.gob.ar`

### Evidencia (Cotizaciones del 23/02/2026)

| Moneda | Código | Tipo Cotización |
|--------|--------|-----------------|
| Dólar Australia | AUD | 967,71 |
| Real | BRL | 265,55 |
| Dólar Canadiense | CAD | 1.001,17 |
| Franco Suizo | CHF | 1.770,90 |
| Peso Chileno | CLP | 1,58 |
| Yuan | CNY | 190,63 |

Total: 39 divisas disponibles

### Endpoints disponibles

```
GET /estadisticascambiarias/v1.0/Cotizaciones          # Cotizaciones de todas las divisas (hoy)
GET /estadisticascambiarias/v1.0/Maestros/Divisas       # Catálogo de divisas disponibles
```

### Uso en Python

```python
import requests

# Cotizaciones del día
r = requests.get("https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones")
data = r.json()
fecha = data["results"]["fecha"]           # "2026-02-23"
divisas = data["results"]["detalle"]       # lista de 39 divisas
# Cada divisa: {"codigoMoneda": "BRL", "descripcion": "REAL", "tipoCotizacion": 265.55, ...}

# Buscar una divisa específica
usd = next(d for d in divisas if d["codigoMoneda"] == "USD")

# Catálogo de divisas
r = requests.get("https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Maestros/Divisas")
catalogo = r.json()["results"]
# [{"codigo": "ARS", "denominacion": "PESO"}, {"codigo": "USD", ...}, ...]
```

### Características
- Sin API key
- Fuente oficial del Banco Central
- 39 divisas con cotización diaria
- Respuesta envuelta en `{"status": 200, "results": {...}}`

---

## 4. ArgentinaDatos - Riesgo País

**Base URL:** `https://api.argentinadatos.com/v1`

### Evidencia (últimos 10 registros)

| Fecha | Valor |
|-------|-------|
| 09/02/2026 | 502 |
| 10/02/2026 | 507 |
| 11/02/2026 | 506 |
| 12/02/2026 | 514 |
| 13/02/2026 | 519 |
| 16/02/2026 | 519 |
| 17/02/2026 | 511 |
| 18/02/2026 | 515 |
| 19/02/2026 | 524 |
| 20/02/2026 | 519 |

Serie histórica: 7.555 registros (desde 1999)

### Endpoints disponibles

```
GET /v1/finanzas/indices/riesgo-pais          # Serie histórica completa
GET /v1/finanzas/indices/riesgo-pais/ultimo   # Solo el último valor
```

### Uso en Python

```python
import requests

# Último valor de riesgo país
r = requests.get("https://api.argentinadatos.com/v1/finanzas/indices/riesgo-pais/ultimo")
data = r.json()
# {"valor": 519, "fecha": "2026-02-20"}

# Serie completa (7500+ registros)
r = requests.get("https://api.argentinadatos.com/v1/finanzas/indices/riesgo-pais")
serie = r.json()
# [{"valor": 937, "fecha": "1999-01-22"}, ...]
ultimos_30 = serie[-30:]
```

### Características
- Sin API key
- Serie desde 1999
- Endpoint `/ultimo` para consulta rápida
- Respuesta JSON directa (lista)

---

## 5. ArgentinaDatos - Inflación

**Base URL:** `https://api.argentinadatos.com/v1`

### Evidencia (últimos 12 meses)

| Mes | Inflación mensual (%) |
|-----|----------------------|
| Feb 2025 | 2,4% |
| Mar 2025 | 3,7% |
| Abr 2025 | 2,8% |
| May 2025 | 1,5% |
| Jun 2025 | 1,6% |
| Jul 2025 | 1,9% |
| Ago 2025 | 1,9% |
| Sep 2025 | 2,1% |
| Oct 2025 | 2,3% |
| Nov 2025 | 2,5% |
| Dic 2025 | 2,8% |
| Ene 2026 | 2,9% |

Serie histórica: 995 registros

### Endpoints disponibles

```
GET /v1/finanzas/indices/inflacion              # Inflación mensual (serie completa)
GET /v1/finanzas/indices/inflacionInteranual    # Inflación interanual
GET /v1/finanzas/tasas/plazoFijo                # Tasas de plazo fijo por entidad
GET /v1/cotizaciones/dolares                    # Cotizaciones históricas del dólar
GET /v1/cotizaciones/dolares/blue               # Histórico dólar blue
```

### Uso en Python

```python
import requests

# Inflación mensual
r = requests.get("https://api.argentinadatos.com/v1/finanzas/indices/inflacion")
inflacion = r.json()
ultimo_mes = inflacion[-1]
# {"fecha": "2026-01-31", "valor": 2.9}

# Inflación interanual
r = requests.get("https://api.argentinadatos.com/v1/finanzas/indices/inflacionInteranual")
interanual = r.json()

# Tasas de plazo fijo
r = requests.get("https://api.argentinadatos.com/v1/finanzas/tasas/plazoFijo")
tasas = r.json()
# [{"entidad": "UALA", "tnaClientes": 0.30, ...}, ...]

# Histórico dólar blue
r = requests.get("https://api.argentinadatos.com/v1/cotizaciones/dolares/blue")
blue_hist = r.json()
ultimos_5 = blue_hist[-5:]
# [{"casa": "blue", "compra": 1405, "venta": 1425, "fecha": "2026-02-23"}, ...]
```

### Características
- Sin API key
- Múltiples indicadores financieros argentinos
- Series históricas extensas
- Incluye tasas de plazo fijo con TNA por entidad

---

## 6. yfinance (Yahoo Finance)

**Librería Python:** `pip install yfinance`

### Evidencia - CEDEAR AAPL.BA (últimos 5 días)

| Fecha | Open | High | Low | Close | Volumen |
|-------|------|------|-----|-------|---------|
| 18/02 | 19.190 | 19.510 | 19.130 | 19.170 | 76.802 |
| 19/02 | 19.120 | 19.180 | 18.830 | 18.860 | 57.734 |
| 20/02 | 18.850 | 19.230 | 18.680 | 19.120 | 53.679 |
| 23/02 | 19.120 | 19.450 | 18.860 | 19.190 | 69.718 |
| 24/02 | 19.330 | 19.430 | 19.160 | 19.370 | 4.676 |

### Otros tickers testeados

| Ticker | Descripción | Último precio |
|--------|-------------|---------------|
| AAPL.BA | Apple CEDEAR | $19.370 ARS |
| GGAL.BA | Galicia CEDEAR | $6.990 ARS |
| MELI.BA | MercadoLibre CEDEAR | $22.840 ARS |
| ^MERV | Índice MERVAL | 2.783.327 |

### Métodos disponibles

```python
import yfinance as yf

ticker = yf.Ticker("AAPL.BA")

# Precio histórico (OHLCV)
hist = ticker.history(period="5d")      # 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
hist = ticker.history(start="2026-01-01", end="2026-02-24")
# Columnas: Open, High, Low, Close, Volume, Dividends, Stock Splits

# Último precio
ultimo = ticker.history(period="1d")["Close"].iloc[-1]

# Info del ticker
info = ticker.info    # dict con sector, industry, marketCap, etc.

# CEDEARs argentinos: agregar .BA al ticker de US
# AAPL.BA, GOOGL.BA, MSFT.BA, AMZN.BA, MELI.BA, GGAL.BA, etc.

# Acciones US directas
us = yf.Ticker("AAPL")
us_hist = us.history(period="5d")

# Múltiples tickers a la vez
data = yf.download(["AAPL.BA", "GGAL.BA", "MELI.BA"], period="1mo")

# Índice MERVAL
merval = yf.Ticker("^MERV")
merval_hist = merval.history(period="1mo")
```

### Tickers útiles para Argentina

```
CEDEARs:     AAPL.BA, GOOGL.BA, MSFT.BA, AMZN.BA, TSLA.BA, MELI.BA, GGAL.BA
Acciones AR: GGAL.BA, YPF.BA, PAMP.BA, BBAR.BA, CEPU.BA, TXAR.BA
Índices:     ^MERV (Merval)
US:          AAPL, GOOGL, MSFT, AMZN, TSLA, SPY, QQQ
```

### Características
- Sin API key (usa Yahoo Finance por detrás)
- Datos OHLCV con frecuencia diaria
- Amplia cobertura: CEDEARs, acciones AR, acciones US, índices, ETFs
- Descarga masiva con `yf.download()`
- Datos de dividendos y splits incluidos

---

## 7. RSS Ámbito Financiero

**Feed URL:** `https://www.ambito.com/rss/economia.xml`

### Evidencia (24 Feb 2026, ~20 noticias)

| Hora | Titular |
|------|---------|
| 10:29 | ¿Se mueve el plazo fijo? Así operan los bancos hoy, martes 24 de febrero |
| 09:30 | Cuenta DNI: cómo aprovechar los descuentos de la última semana de febrero |
| 09:09 | Tras la aceleración de la inflación, las consultoras recalibran al alza sus proyecciones para el resto del año |
| 08:56 | Aumenta la luz en la provincia de Buenos Aires: aprueban suba de entre el 12% y el 17% |
| 08:38 | EEUU comienza a aplicar los nuevos aranceles del 10% pese al fallo de la Corte Suprema |

### Campos por noticia
- **title** — Titular completo
- **link** — URL al artículo
- **published** — Fecha y hora de publicación
- **summary** — Resumen/copete del artículo (1-2 oraciones)
- **tags** — Categorías/etiquetas

### Uso en Python

```python
import feedparser

d = feedparser.parse("https://www.ambito.com/rss/economia.xml")
for entry in d.entries:
    print(entry.title)       # "¿Se mueve el plazo fijo?..."
    print(entry.link)        # URL completa
    print(entry.published)   # "Tue, 24 Feb 2026 10:29:00 -0300"
    print(entry.summary)     # Copete/resumen
```

### Características
- Sin API key
- ~20 noticias recientes de economía argentina
- Incluye resumen (copete) útil como contexto para el agente
- Actualización continua durante el día

---

## 8. RSS El Cronista

**Feed URL:** `https://www.cronista.com/files/rss/finanzas.xml`

### Evidencia (24 Feb 2026, ~37 noticias)

| Hora | Titular | Autor |
|------|---------|-------|
| 14:56 | Dólar abajo de $1400: ¿es bueno o malo para Argentina? | Lara López Calvo |
| 14:52 | La morosidad en los préstamos no bancarios no para de crecer | Mariano Gorodisch |
| 14:48 | Dólar blue hoy: a cuánto cotiza el martes 24 de febrero con el MEP y el CCL | — |
| 14:33 | El BCRA podría comprar hasta u$s 31.000 millones: cómo impactaría en la deuda local | Julián Yosovitch |
| 14:31 | Dólar hoy: a cuánto cotiza el oficial en los bancos de la City este martes 24 de febrero | — |

### Campos por noticia
- **title** — Titular completo
- **link** — URL al artículo
- **published** — Fecha y hora de publicación
- **author** — Nombre del periodista (cuando está disponible)
- **summary** — Resumen (puede estar vacío en algunas notas)
- **content** — Contenido extendido (HTML)
- **media_content** — Imagen asociada

### Uso en Python

```python
import feedparser

d = feedparser.parse("https://www.cronista.com/files/rss/finanzas.xml")
for entry in d.entries:
    print(entry.title)                       # Titular
    print(entry.link)                        # URL
    print(entry.published)                   # Fecha
    print(entry.get("author", "sin autor"))  # Periodista
```

### Características
- Sin API key
- ~37 noticias de finanzas y mercados
- Mayor volumen que Ámbito (casi el doble)
- Incluye autor (periodista) en muchas notas
- Campo media_content con imagen de portada

---

## 9. RSS Bloomberg Markets

**Feed URL:** `https://feeds.bloomberg.com/markets/news.rss`

### Evidencia (24 Feb 2026, ~30 noticias)

| Hora | Titular |
|------|---------|
| 14:50 | S&P 500 Rises as Traders Assess Fallout From AI-Fueled Slump |
| 05:08 | Bitcoin Heads for Worst Month Since Crypto Collapse of June 2022 |
| 22:27 (23/02) | Stocks Bounce After AI-Fueled Slide as AMD Surges: Markets Wrap |

### Campos por noticia
- **title** — Titular completo
- **link** — URL al artículo
- **summary** — Resumen (1-2 oraciones con contexto)
- **published** — Fecha y hora

### Uso en Python

```python
import feedparser

d = feedparser.parse("https://feeds.bloomberg.com/markets/news.rss")
for entry in d.entries:
    print(entry.title)       # "S&P 500 Rises as Traders..."
    print(entry.summary)     # Resumen con contexto
    print(entry.link)        # URL completa
    print(entry.published)   # "Tue, 24 Feb 2026 14:50:49 +0000"
```

### Características
- Sin API key
- ~30 noticias de mercados globales
- Resúmenes de buena calidad, útiles como contexto para el agente
- Cobertura: acciones, bonos, commodities, crypto, macro global

---

## 10. RSS CNBC Finance

**Feed URL:** `https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664`

### Evidencia (24 Feb 2026, ~30 noticias)

| Hora | Titular |
|------|---------|
| 13:00 | Fed's Goolsbee calls for a hold on cuts as current rate of inflation is too high |
| 12:40 | Stocks making the biggest moves premarket: AMD, Home Depot, Hims & Health |
| 13:17 | Jamie Dimon says 'watch out' as lofty asset prices add to economic risk |

### Campos por noticia
- **title** — Titular completo
- **link** — URL al artículo
- **summary** — Resumen/descripción
- **published** — Fecha y hora

### Uso en Python

```python
import feedparser

url = ("https://search.cnbc.com/rs/search/combinedcms/view.xml"
       "?partnerId=wrss01&id=10000664")
d = feedparser.parse(url)
for entry in d.entries:
    print(entry.title)
    print(entry.get("summary", ""))
    print(entry.link)
```

### Características
- Sin API key
- ~30 noticias de finanzas US
- Fuerte cobertura de Fed, earnings, mercados US
- Resúmenes concisos

---

## 11. RSS Financial Times Markets

**Feed URL:** `https://www.ft.com/rss/markets`

### Evidencia (24 Feb 2026, ~25 noticias)

| Hora | Titular |
|------|---------|
| 14:38 | Investors seek shelter from AI rout in asset-heavy stocks |
| 13:00 | Stripe valuation soars to $159bn in latest share sale |
| 12:25 | Russian 'illicit oil traders' exposed by email blunder placed under UK sanctions |

### Campos por noticia
- **title** — Titular completo
- **link** — URL al artículo
- **summary** — Resumen con análisis
- **published** — Fecha y hora

### Uso en Python

```python
import feedparser

d = feedparser.parse("https://www.ft.com/rss/markets")
for entry in d.entries:
    print(entry.title)
    print(entry.summary)
    print(entry.link)
```

### Características
- Sin API key
- ~25 noticias de mercados con enfoque analítico
- Calidad editorial alta (análisis, no solo breaking news)
- Cobertura global: UK, Europa, Asia, US

---

## 12. RSS Infobae Economía

**Feed URL:** `https://www.infobae.com/arc/outboundfeeds/rss/category/economia/`

### Evidencia (24 Feb 2026, ~100 noticias)

| Hora | Titular |
|------|---------|
| 14:56 | El Gobierno prepara un aumento de peajes en autopistas y rutas nacionales |
| 14:51 | Mercados: suben las acciones y caen los bonos, atentos a factores locales |
| 14:43 | Influenza aviar: la Argentina suspendió las exportaciones y enfrenta un desafío sanitario |

### Campos por noticia
- **title** — Titular completo
- **link** — URL al artículo
- **summary** — Resumen (cuando disponible)
- **published** — Fecha y hora

### Uso en Python

```python
import feedparser

d = feedparser.parse("https://www.infobae.com/arc/outboundfeeds/rss/category/economia/")
for entry in d.entries:
    print(entry.title)
    print(entry.link)
    print(entry.published)
```

### Características
- Sin API key
- ~100 noticias (el feed más grande de todos)
- Cobertura amplia: economía AR, agro, energía, mercados, política económica
- Alto volumen útil para tener contexto variado

---

## 13. BCRA API v4.0 - Datos Macro

**Base URL:** `https://api.bcra.gob.ar/estadisticas/v4.0`

### Evidencia (24 Feb 2026)

| Variable | ID | Valor | Fecha |
|----------|-----|-------|-------|
| Reservas internacionales | 1 | USD 44.904M | 21/02/2026 |
| Base monetaria | 15 | $41.882.460M ARS | 14/02/2026 |
| CER | 30 | 710,62 | 21/02/2026 |
| Tasa BADLAR | 7 | 32,69% TNA | 21/02/2026 |
| TC Minorista | 4 | $1.393 | 21/02/2026 |
| TC Mayorista | 5 | $1.372 | 21/02/2026 |

Total: 1.176 variables disponibles

### Endpoints disponibles

```
GET /estadisticas/v4.0/Monetarias/{idVariable}?desde=YYYY-MM-DD&hasta=YYYY-MM-DD&limit=N
```

### Uso en Python

```python
import requests

# Reservas internacionales (ID 1)
url = "https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias/1?desde=2026-01-01&hasta=2026-12-31&limit=3"
r = requests.get(url)
data = r.json()
detalle = data["results"][0]["detalle"]
# [{"fecha": "2026-02-21", "valor": 44904}, ...]

# Base monetaria (ID 15)
url = "https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias/15?desde=2026-01-01&hasta=2026-12-31&limit=3"

# CER (ID 30)
url = "https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias/30?desde=2026-01-01&hasta=2026-12-31&limit=3"

# Tasa BADLAR (ID 7)
url = "https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias/7?desde=2026-01-01&hasta=2026-12-31&limit=3"
```

### IDs de variables útiles

| ID | Variable |
|----|----------|
| 1 | Reservas internacionales |
| 4 | TC minorista ($/USD) |
| 5 | TC mayorista ($/USD) |
| 7 | Tasa BADLAR |
| 15 | Base monetaria |
| 30 | CER |
| 160 | Tasa política monetaria (discontinuada jul 2025) |

### Características
- Sin API key, sin registro
- v2.0 deprecada (retorna 400), v3.0 se depreca 28/02/2026, usar v4.0
- 1.176 variables disponibles
- Series históricas extensas
- Respuesta: `{"status": 200, "results": [{"idVariable": 1, "detalle": [...]}]}`

---

## 14. PyOBD - Bonos Soberanos AR (Open BYMA Data)

**Librería Python:** `pip install PyOBD @ git+https://github.com/franco-lamas/PyOBD`
**API REST subyacente:** `https://open.bymadata.com.ar/vanoms-be-core/rest/api/bymadata/free/`

### Evidencia - Bonos (24 Feb 2026)

| Ticker | Último | Var% | Volumen |
|--------|--------|------|---------|
| AL29 | $96.520 | +1,35% | 2.141.825 |
| AL30 | $93.850 | +1,19% | 30.289.023 |
| AL35 | $78.000 | +0,97% | 2.534.826 |
| GD30 | $87.950 | +1,03% | 6.312.444 |
| GD35 | $80.800 | +0,12% | 1.879.988 |

Total: 189 bonos disponibles

### Evidencia - Lecaps/Boncaps

Total: 158 letras, mayoría con precio activo

### Evidencia - Obligaciones Negociables

Total: 2.920 tickers (236 con precio activo). Emisores: YPF, Telecom, Pan American, etc.

### Uso en Python

```python
import PyOBD

obd = PyOBD.openBYMAdata()

# Bonos soberanos
bonds = obd.get_bonds()
# DataFrame con: symbol, last, bid, ask, volume, change, maturity, etc.
al30 = bonds[bonds["symbol"] == "AL30"]

# Lecaps / Boncaps
short = obd.get_short_term_bonds()

# Obligaciones negociables
ons = obd.get_negociable_obligations()

# Acciones líderes
leaders = obd.get_leading_equity()

# CEDEARs
cedears = obd.get_cedears()
```

### Endpoints REST directos (sin PyOBD)

```
POST /vanoms-be-core/rest/api/bymadata/free/public-bonds
POST /vanoms-be-core/rest/api/bymadata/free/lebacs
POST /vanoms-be-core/rest/api/bymadata/free/negociable-obligations
POST /vanoms-be-core/rest/api/bymadata/free/leading-equity
POST /vanoms-be-core/rest/api/bymadata/free/general-equity
POST /vanoms-be-core/rest/api/bymadata/free/cedears
POST /vanoms-be-core/rest/api/bymadata/free/options
```

### Características
- Sin API key, sin cuenta de broker
- Gratis permanentemente (datos públicos con 20 min de delay)
- PyOBD es un wrapper Python sobre la API REST de open.bymadata.com.ar
- Se puede usar la API REST directamente desde cualquier lenguaje
- Cobertura: bonos, letras, ONs, acciones, CEDEARs, opciones

---

## 15. INDEC - Calendario Económico

**Fuente:** `https://www.indec.gob.ar/ftp/cuadros/publicaciones/calendario_1sem2026.pdf`

### Evidencia (24 Feb 2026)

PDF del calendario de difusión del 1er semestre 2026, parseable con pdfplumber. Contiene fechas de publicación de:
- **IPC** (Índice de Precios al Consumidor) — mensual
- **EMAE** (Estimador Mensual de Actividad Económica) — mensual
- **Empleo** — trimestral
- **Comercio exterior** — mensual
- **Actividad industrial** — mensual
- Otros indicadores estadísticos

### Uso en Python

```python
import requests
import pdfplumber
import io

url = "https://www.indec.gob.ar/ftp/cuadros/publicaciones/calendario_1sem2026.pdf"
r = requests.get(url, timeout=15)
pdf = pdfplumber.open(io.BytesIO(r.content))
text = pdf.pages[0].extract_text()
# Contiene tabla con fechas de difusión de cada indicador
```

### Características
- Sin API key
- PDF oficial del INDEC
- Se publica semestralmente (1sem y 2sem)
- Parseable automáticamente con pdfplumber
- Trading Economics descartada (free tier solo sample data, no Argentina)

---

## Resumen comparativo

| API | Dato principal | Latencia | Histórico | Mejor para |
|-----|---------------|----------|-----------|------------|
| DolarAPI | Cotizaciones dólar (7 tipos) | ~200ms | No | Cotización actual de todos los dólares |
| Bluelytics | Dólar + Euro (blue/oficial) | ~300ms | Sí | Blue/oficial con historia y EUR |
| BCRA Cambiarias | 39 divisas oficiales | ~500ms | No | Cotizaciones oficiales de divisas |
| BCRA Macro v4 | Reservas, base monetaria, CER, BADLAR | ~500ms | Sí | Datos macro del Banco Central |
| ArgentinaDatos | Riesgo país, inflación, tasas | ~300ms | Sí (desde 1999) | Indicadores macro argentinos |
| yfinance | Precios acciones/CEDEARs | ~1-2s | Sí | Precios de activos financieros |
| PyOBD / BYMA | Bonos, Lecaps, ONs, acciones AR | ~1-2s | No | Renta fija y variable AR con 20min delay |
| INDEC PDF | Calendario económico | ~2s | No | Fechas de publicación de indicadores |
| RSS Ámbito | Noticias economía AR (~20) | ~500ms | No | Titulares + copetes de economía |
| RSS Cronista | Noticias finanzas AR (~37) | ~500ms | No | Titulares + autor de finanzas/mercados |
| RSS Bloomberg | Noticias mercados globales (~30) | ~500ms | No | Mercados globales, macro, crypto |
| RSS CNBC | Noticias finanzas US (~30) | ~500ms | No | Fed, earnings, mercados US |
| RSS FT Markets | Noticias mercados (~25) | ~500ms | No | Análisis global de mercados |
| RSS Infobae | Noticias economía AR (~100) | ~500ms | No | Mayor volumen, economía AR amplia |

### Cobertura de datos sin API key

```
Dólar (oficial, blue, MEP, CCL, cripto, tarjeta) ✅ DolarAPI + Bluelytics
Euro (oficial y blue)                              ✅ Bluelytics
Cotizaciones divisas (39 monedas)                  ✅ BCRA Cambiarias
Reservas, base monetaria, CER, BADLAR             ✅ BCRA Macro v4
Riesgo país                                        ✅ ArgentinaDatos
Inflación mensual e interanual                     ✅ ArgentinaDatos
Tasas plazo fijo                                   ✅ ArgentinaDatos
Precios CEDEARs / acciones AR                      ✅ yfinance
Precios acciones US                                ✅ yfinance
Índice MERVAL                                      ✅ yfinance
Bonos soberanos AR (189 bonos)                     ✅ PyOBD / BYMA
Lecaps / Boncaps (158 letras)                      ✅ PyOBD / BYMA
Obligaciones negociables (2.920 tickers)           ✅ PyOBD / BYMA
Calendario económico (IPC, EMAE, empleo)           ✅ INDEC PDFs
Noticias economía AR (titulares + copetes)         ✅ RSS Ámbito
Noticias finanzas AR (titulares + autor)            ✅ RSS Cronista
Noticias economía AR amplia (~100)                  ✅ RSS Infobae
Noticias mercados globales                          ✅ RSS Bloomberg
Noticias finanzas US (Fed, earnings)                ✅ RSS CNBC
Noticias mercados (análisis global)                 ✅ RSS FT Markets
```
