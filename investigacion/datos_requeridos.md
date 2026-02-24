# Requerimientos de Datos - Agente Financiero

Tracking de fuentes de datos para que el agente escriba noticias y reportes financieros argentinos.

Última actualización: 24 Feb 2026

---

## Resumen

| Categoría | Estado | Fuente | Costo |
|-----------|--------|--------|-------|
| Cotizaciones dólar (7 tipos + EUR) | ✅ Resuelto | DolarAPI + Bluelytics | Gratis |
| Acciones argentinas | ✅ Resuelto | yfinance | Gratis |
| CEDEARs y acciones US | ✅ Resuelto | yfinance | Gratis |
| Fundamentals (P/E, balances, etc.) | ✅ Resuelto | yfinance | Gratis |
| Índices (MERVAL, S&P, Nasdaq, Dow) | ✅ Resuelto | yfinance | Gratis |
| Commodities (soja, maíz, trigo, petróleo, oro) | ✅ Resuelto | yfinance | Gratis |
| Crypto (BTC, ETH) | ✅ Resuelto | yfinance | Gratis |
| Riesgo país | ✅ Resuelto | ArgentinaDatos | Gratis |
| Inflación mensual e interanual | ✅ Resuelto | ArgentinaDatos | Gratis |
| Tasas plazo fijo | ✅ Resuelto | ArgentinaDatos | Gratis |
| Cotizaciones divisas (39 monedas) | ✅ Resuelto | BCRA API | Gratis |
| Noticias financieras AR | ✅ Resuelto | RSS Ámbito + Cronista | Gratis |
| Noticias internacionales | ✅ Resuelto | RSS Bloomberg + CNBC + FT + Infobae | Gratis |
| Bonos soberanos AR | ✅ Resuelto | PyOBD (Open BYMA Data) | Gratis, sin cuenta |
| Obligaciones negociables | ✅ Resuelto | PyOBD (Open BYMA Data) | Gratis, sin cuenta |
| Datos macro BCRA | ✅ Resuelto | BCRA API v4.0 | Gratis |
| Calendario económico | ✅ Resuelto | INDEC PDFs (pdfplumber) | Gratis |

---

## ✅ Resuelto

### Cotizaciones dólar
- **DolarAPI** — Oficial, blue, MEP, CCL, mayorista, cripto, tarjeta. Sin key.
- **Bluelytics** — USD y EUR (blue + oficial), con serie histórica. Sin key.

### Indicadores macro AR
- **ArgentinaDatos** — Riesgo país (serie desde 1999), inflación mensual/interanual, tasas de plazo fijo por entidad. Sin key.

### Cotizaciones divisas
- **BCRA API** — 39 divisas con cotización oficial diaria. Sin key.

### Noticias financieras AR
- **RSS Ámbito Financiero** — ~20 noticias de economía (título, link, resumen, fecha)
- **RSS El Cronista** — ~37 noticias de finanzas (título, link, resumen, fecha, autor)
- **RSS Infobae Economía** — ~100 noticias de economía AR (título, link, resumen)
- Integrado en test_apis.py con feedparser. Sin key.

### Bonos soberanos AR
- **PyOBD (Open BYMA Data)** — 189 bonos + 158 Lecaps/Boncaps. Sin key, sin cuenta de broker.
  - Bonos: AL29, AL30, AL35, AL41, GD30, GD35, GD38, GD41, AE38 (en ARS y USD)
  - Lecaps/Boncaps: S17A6, S30A6, S29Y6, etc.
  - Datos: precio, bid/ask, volumen, variación, vencimiento
  - Delay: 20 minutos vs tiempo real
  - Obligaciones negociables: 2.920 tickers (236 con precio activo), YPF, Telecom, Pan American, etc.
  - Nota: IOL API y PPI API disponibles como alternativa si se necesita datos en tiempo real (requieren cuenta broker gratuita)

### Datos macro BCRA
- **BCRA API v4.0** — Sin key, sin registro. La v2.0 fue deprecada, la v4.0 es la actual.
  - Reservas internacionales (ID 1): USD 44.904M
  - Base monetaria (ID 15): $41.882.460M ARS
  - CER (ID 30): 710,62
  - Tasa BADLAR (ID 7): 32,69% TNA
  - TC Minorista (ID 4) y Mayorista (ID 5)
  - Tasa política monetaria (ID 160): datos hasta jul 2025 (discontinuada por cambio de instrumento)
  - 1.176 variables disponibles en total
  - Nota: v3.0 se depreca el 28/02/2026, usar v4.0

### Noticias internacionales
- **RSS Bloomberg Markets** — ~30 noticias de mercados globales (título, resumen, link)
- **RSS CNBC Finance** — ~30 noticias de finanzas US (título, resumen, link)
- **RSS Financial Times Markets** — ~25 noticias de mercados (título, resumen, link)
- Integrado en test_apis.py con feedparser. Sin key.
- Nota: Tavily y NewsAPI siguen disponibles como opción adicional si se necesita búsqueda contextual (requieren registro gratuito)

### Mercados (acciones, commodities, crypto, índices)
- **yfinance** — Sin key. Cobertura:
  - Acciones AR (YPFD, GGAL, PAMP, BBAR, CEPU, MELI, etc.)
  - CEDEARs y acciones US con fundamentals completos (balances, income statement, dividendos)
  - Índices: MERVAL, S&P 500, Nasdaq, Dow Jones
  - Commodities: soja, maíz, trigo, petróleo WTI, oro
  - Crypto: BTC, ETH
  - ETF Argentina (ARGT)
  - Datos históricos extensos (algunos desde 1996)
  - Nota importante: YPF cotiza como YPFD en BYMA, usar YPFD.BA

### Calendario económico
- **INDEC PDFs** — Calendario de difusión semestral, parseable con pdfplumber. Sin key.
  - Fechas de publicación de IPC, EMAE, empleo, comercio exterior, actividad industrial
  - PDF: `calendario_1sem2026.pdf` y `calendario_2sem2026.pdf`
  - Se descarga y parsea automáticamente con pdfplumber
  - Nota: Trading Economics API descartada (free tier solo devuelve sample data, no datos de Argentina)

---

## Opcional (no resuelto, prioridad baja)

### Búsqueda contextual
**Prioridad: BAJA** — Los RSS ya cubren noticias. Estas APIs servirían para que el agente busque contexto puntual sobre un tema específico.

| Opción | Límite free tier | Estado |
|--------|-----------------|--------|
| Tavily | 1000 req/mes | Key no configurada |
| NewsAPI | 100 req/día | Key no configurada |

Acción: evaluar si los RSS son suficientes o si se necesita búsqueda ad-hoc.

---

## Changelog

| Fecha | Cambio |
|-------|--------|
| 24 Feb 2026 | Creación inicial. 11 categorías resueltas con APIs gratuitas. 1 parcial (RSS noticias). 4 pendientes identificados. |
| 24 Feb 2026 | RSS Ámbito + Cronista integrados con feedparser. Noticias AR pasa de ⚠️ Parcial a ✅ Resuelto. |
| 24 Feb 2026 | Noticias internacionales resueltas con RSS (Bloomberg, CNBC, FT, Infobae). Sin necesidad de API keys. |
| 24 Feb 2026 | Bonos soberanos AR resueltos con PyOBD (Open BYMA Data). 189 bonos + 158 Lecaps sin key ni cuenta broker. |
| 24 Feb 2026 | Datos macro BCRA resueltos con API v4.0 (la v2.0 estaba deprecada). Reservas, base monetaria, CER, BADLAR, TC. Total: 16 resueltas, 1 pendiente + 1 opcional. |
| 24 Feb 2026 | Calendario económico resuelto con INDEC PDFs (pdfplumber). Trading Economics descartada. Total: 17 resueltas, 1 opcional. |
