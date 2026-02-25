"""
Push reportes y datos diarios a PostgreSQL.
Uso: python3 scripts/push_to_db.py [--fecha YYYY-MM-DD] [--datos path/to/json]

Lee los .md de agentes/reportes/ y el JSON de output/, luego hace UPSERT en la DB.
"""

import os
import re
import sys
import json
import argparse
from datetime import date

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)

try:
    import psycopg2
    from psycopg2.extras import Json
except ImportError:
    print("ERROR: psycopg2-binary no instalado. Ejecutar: pip install psycopg2-binary")
    sys.exit(1)

from dotenv import load_dotenv

load_dotenv(os.path.join(BASE_DIR, ".env"))

AGENTES = ["manu", "tomi", "vale", "santi", "sol", "diego", "roberto", "editor"]
REPORTES_DIR = os.path.join(BASE_DIR, "agentes", "reportes")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def get_db_url():
    url = os.getenv("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL no configurada en .env")
        sys.exit(1)
    return url


def parse_report(filepath):
    """Extrae título, contenido, excerpt y word_count de un .md."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Título: primer heading #
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "Sin título"

    # Word count
    words = content.split()
    word_count = len(words)

    # Excerpt: primer párrafo después del título (no vacío, no heading)
    lines = content.split("\n")
    excerpt = ""
    past_title = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            past_title = True
            continue
        if past_title and stripped and not stripped.startswith("#"):
            # Limpiar markdown básico
            clean = re.sub(r"[*_`\[\]]", "", stripped)
            clean = re.sub(r"\(http[^)]+\)", "", clean)
            excerpt = clean[:300]
            break

    if not excerpt and word_count > 10:
        excerpt = " ".join(words[:50]) + "..."

    return {
        "title": title,
        "content": content,
        "word_count": word_count,
        "excerpt": excerpt,
    }


def push_reports(conn, fecha):
    """UPSERT reportes del día en la tabla reports."""
    print(f"\n--- Pusheando reportes para {fecha} ---")
    cur = conn.cursor()

    pushed = 0
    for agente in AGENTES:
        filepath = os.path.join(REPORTES_DIR, f"{agente}_{fecha}.md")
        if not os.path.exists(filepath):
            print(f"  SKIP {agente}: archivo no encontrado ({filepath})")
            continue

        report = parse_report(filepath)

        cur.execute(
            """
            INSERT INTO reports (agent_id, date, title, content, word_count, excerpt, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            ON CONFLICT (agent_id, date) DO UPDATE SET
                title = EXCLUDED.title,
                content = EXCLUDED.content,
                word_count = EXCLUDED.word_count,
                excerpt = EXCLUDED.excerpt,
                updated_at = NOW()
            """,
            (agente, fecha, report["title"], report["content"], report["word_count"], report["excerpt"]),
        )
        pushed += 1
        print(f"  ✓ {agente}: {report['title'][:60]}... ({report['word_count']} palabras)")

    conn.commit()
    cur.close()
    print(f"\n  Total: {pushed} reportes pusheados")
    return pushed


def push_daily_data(conn, fecha, datos_path=None):
    """UPSERT JSON del pipeline en la tabla daily_data."""
    if datos_path is None:
        datos_path = os.path.join(OUTPUT_DIR, f"datos_diarios_{fecha}.json")

    if not os.path.exists(datos_path):
        print(f"\n  SKIP daily_data: archivo no encontrado ({datos_path})")
        return False

    print(f"\n--- Pusheando datos diarios: {datos_path} ---")

    with open(datos_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO daily_data (date, data, created_at)
        VALUES (%s, %s, NOW())
        ON CONFLICT (date) DO UPDATE SET
            data = EXCLUDED.data
        """,
        (fecha, Json(data)),
    )
    conn.commit()
    cur.close()

    size_kb = os.path.getsize(datos_path) / 1024
    print(f"  ✓ daily_data: {size_kb:.0f} KB")
    return True


def main():
    parser = argparse.ArgumentParser(description="Push reportes y datos a PostgreSQL")
    parser.add_argument(
        "--fecha",
        default=date.today().isoformat(),
        help="Fecha (YYYY-MM-DD, default: hoy)",
    )
    parser.add_argument(
        "--datos",
        default=None,
        help="Path al JSON de datos diarios",
    )
    parser.add_argument(
        "--solo-reportes",
        action="store_true",
        help="Solo pushear reportes, no datos diarios",
    )
    parser.add_argument(
        "--solo-datos",
        action="store_true",
        help="Solo pushear datos diarios, no reportes",
    )
    args = parser.parse_args()

    db_url = get_db_url()
    print(f"Conectando a PostgreSQL...")

    try:
        conn = psycopg2.connect(db_url)
        print("  ✓ Conexión exitosa")
    except Exception as e:
        print(f"  ERROR conectando: {e}")
        sys.exit(1)

    try:
        if not args.solo_datos:
            push_reports(conn, args.fecha)
        if not args.solo_reportes:
            push_daily_data(conn, args.fecha, args.datos)

        print("\n✓ Push completo")
    except Exception as e:
        print(f"\nERROR: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
