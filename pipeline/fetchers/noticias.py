"""
Fetcher de noticias vía RSS feeds.
Fuentes: Ámbito, Cronista, Infobae (AR), Bloomberg, CNBC, FT (intl).
"""

import logging
import re

import feedparser

from pipeline.config import RSS_FEEDS_AR, RSS_FEEDS_INTL, MAX_NOTICIAS_PER_FEED

logger = logging.getLogger(__name__)


def _clean_html(text):
    """Limpiar tags HTML de summaries RSS."""
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", "", text)
    return clean.strip()[:500]


def _fetch_rss_feed(url, source_name, max_items=None):
    """Fetch y parsear un feed RSS individual."""
    if max_items is None:
        max_items = MAX_NOTICIAS_PER_FEED
    try:
        d = feedparser.parse(url)
        if d.bozo and not d.entries:
            logger.warning(f"RSS {source_name} error de parseo: {d.bozo_exception}")
            return []

        noticias = []
        for entry in d.entries[:max_items]:
            noticias.append({
                "titulo": (entry.get("title") or "").strip(),
                "fuente": source_name,
                "url": entry.get("link", ""),
                "resumen": _clean_html(entry.get("summary", "")),
                "fecha": entry.get("published", ""),
                "autor": entry.get("author"),
            })
        return noticias
    except Exception as e:
        logger.warning(f"RSS {source_name} falló: {e}")
        return []


def _fetch_noticias_ar():
    """Fetch noticias argentinas de todos los feeds AR."""
    todas = []
    for name, url in RSS_FEEDS_AR.items():
        logger.info(f"Fetching RSS {name}...")
        noticias = _fetch_rss_feed(url, name)
        todas.extend(noticias)
        logger.info(f"  → {len(noticias)} noticias de {name}")
    return todas


def _fetch_noticias_intl():
    """Fetch noticias internacionales de todos los feeds intl."""
    todas = []
    for name, url in RSS_FEEDS_INTL.items():
        logger.info(f"Fetching RSS {name}...")
        noticias = _fetch_rss_feed(url, name)
        todas.extend(noticias)
        logger.info(f"  → {len(noticias)} noticias de {name}")
    return todas


# --- Función pública ---

def fetch_noticias():
    """Fetch todas las noticias. Retorna (data_dict, status_dict)."""
    ar = _fetch_noticias_ar()
    intl = _fetch_noticias_intl()

    status = {
        "ar": "ok" if len(ar) >= 5 else ("parcial" if ar else "error"),
        "intl": "ok" if len(intl) >= 5 else ("parcial" if intl else "error"),
    }

    data = {
        "argentina": ar,
        "internacionales": intl,
    }

    return data, status
