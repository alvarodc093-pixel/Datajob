"""
DataJobs Radar - ingesta.py
API de Adzuna -> SQLite (con cache de respuestas crudas).

Ejecucion:
    python ingesta.py            # descarga lo que falte en el cache
    python ingesta.py --force    # ignora el cache y vuelve a pedir todo a la API
    python ingesta.py --dry-run  # muestra que consultas haria sin llamar a la API

El cache guarda cada respuesta cruda en la tabla api_cache. Volver a ejecutar
sin --force NO consume peticiones de la API.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import time
from pathlib import Path

import requests
import tomllib

BASE_URL = "https://api.adzuna.com/v1/api/jobs"
RESULTS_PER_PAGE = 50  # maximo que permite Adzuna
DB_PATH = Path(__file__).parent / "datos.db"
SECRETS_PATH = Path(__file__).parent / "secrets.toml"

# Paises de interes: Espana + Europa (+ Alemania destacada).
COUNTRIES = ["es", "de", "fr", "nl", "pl", "it", "at", "be", "ch"]

# Busquedas: cubren los roles que comparamos en el proyecto.
QUERIES = ["data analyst", "analista de datos", "bi analyst", "data scientist"]

# Busquedas adicionales para captar ofertas remotas (Adzuna no tiene filtro).
REMOTE_QUERIES = ["data analyst remote", "analista de datos remoto",
                  "bi analyst remote", "data scientist remote"]

# Moneda por pais (solo para documentar la columna salary_currency).
CURRENCY = {
    "es": "EUR", "de": "EUR", "fr": "EUR", "nl": "EUR", "pl": "PLN",
    "it": "EUR", "ie": "EUR", "at": "EUR", "be": "EUR", "ch": "CHF",
}

# Palabras que indican que una oferta permite remoto.
REMOTE_KEYWORDS = (
    "remote", "fully remote", "100% remote", "work from home", "wfh",
    "home office", "remoto", "teletrabajo", "trabajo en remoto",
    "100% remoto", "trabajo remoto", "a distancia",
)


def cargar_secretos() -> dict:
    if not SECRETS_PATH.exists():
        sys.exit(
            f"No existe {SECRETS_PATH.name}. Copia secrets_ejemplo.toml "
            "como secrets.toml y pega tu app_id y app_key de Adzuna."
        )
    with SECRETS_PATH.open("rb") as f:
        return tomllib.load(f)


def crear_esquema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS api_cache (
            cache_key  TEXT PRIMARY KEY,
            country    TEXT,
            query      TEXT,
            page       INTEGER,
            fetched_at TEXT,
            payload    TEXT
        );

        CREATE TABLE IF NOT EXISTS ofertas (
            id                  TEXT PRIMARY KEY,
            title               TEXT,
            description         TEXT,
            salary_min          REAL,
            salary_max          REAL,
            salary_is_predicted INTEGER,
            salary_currency     TEXT,
            contract_type       TEXT,
            contract_time       TEXT,
            category_label      TEXT,
            category_tag        TEXT,
            company             TEXT,
            location_display    TEXT,
            location_area       TEXT,
            latitude            REAL,
            longitude           REAL,
            remote              INTEGER,
            created             TEXT,
            redirect_url        TEXT,
            country             TEXT,
            query_used          TEXT,
            fetched_at          TEXT
        );
        """
    )
    conn.commit()


def cache_key(country: str, query: str, page: int) -> str:
    raw = f"{country}|{query}|{page}".encode()
    return hashlib.sha256(raw).hexdigest()


def llamar_api(session: requests.Session, secrets: dict, country: str,
               query: str, page: int) -> dict:
    url = f"{BASE_URL}/{country}/search/{page}"
    params = {
        "app_id": secrets["adzuna"]["app_id"],
        "app_key": secrets["adzuna"]["app_key"],
        "what": query,
        "results_per_page": RESULTS_PER_PAGE,
        "content-type": "application/json",
    }
    resp = session.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def normalizar_oferta(ad: dict, country: str, query: str,
                      fetched_at: str) -> dict:
    loc = ad.get("location") or {}
    area = loc.get("area") or []
    cat = ad.get("category") or {}
    company = (ad.get("company") or {}).get("display_name") or ""
    title = ad.get("title") or ""
    description = ad.get("description") or ""

    texto_busqueda = f"{title} {description} {loc.get('display_name', '')}".lower()
    es_remoto = any(k in texto_busqueda for k in REMOTE_KEYWORDS)

    return {
        "id": str(ad.get("id")),
        "title": title,
        "description": description,
        "salary_min": ad.get("salary_min"),
        "salary_max": ad.get("salary_max"),
        "salary_is_predicted": ad.get("salary_is_predicted"),
        "salary_currency": CURRENCY.get(country, ""),
        "contract_type": ad.get("contract_type"),
        "contract_time": ad.get("contract_time"),
        "category_label": cat.get("label"),
        "category_tag": cat.get("tag"),
        "company": company,
        "location_display": loc.get("display_name"),
        "location_area": json.dumps(area, ensure_ascii=False),
        "latitude": ad.get("latitude"),
        "longitude": ad.get("longitude"),
        "remote": 1 if es_remoto else 0,
        "created": ad.get("created"),
        "redirect_url": ad.get("redirect_url"),
        "country": country,
        "query_used": query,
        "fetched_at": fetched_at,
    }


def guardar_cache(conn: sqlite3.Connection, key: str, country: str,
                  query: str, page: int, fetched_at: str, payload: dict) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO api_cache VALUES (?, ?, ?, ?, ?, ?)",
        (key, country, query, page, fetched_at, json.dumps(payload)),
    )
    conn.commit()


def insertar_ofertas(conn: sqlite3.Connection, rows: list[dict]) -> int:
    cols = list(rows[0].keys()) if rows else []
    if not cols:
        return 0
    placeholders = ", ".join("?" for _ in cols)
    sql = (
        f"INSERT OR IGNORE INTO ofertas ({', '.join(cols)}) "
        f"VALUES ({placeholders})"
    )
    nuevos = 0
    for r in rows:
        cur = conn.execute(sql, [r[c] for c in cols])
        nuevos += cur.rowcount
    conn.commit()
    return nuevos


def consultas_planificadas() -> list[tuple[str, str, int]]:
    consultas = [(c, q, 1) for c in COUNTRIES for q in QUERIES]
    consultas += [(c, q, 1) for c in COUNTRIES for q in REMOTE_QUERIES]
    return consultas


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingesta de ofertas de Adzuna")
    parser.add_argument("--force", action="store_true",
                        help="Ignora el cache y vuelve a llamar a la API")
    parser.add_argument("--dry-run", action="store_true",
                        help="Muestra las consultas sin llamar a la API")
    args = parser.parse_args()

    if args.dry_run:
        for c, q, p in consultas_planificadas():
            print(f"GET /jobs/{c}/search/{p}  what={q!r}")
        print(f"\nTotal: {len(consultas_planificadas())} peticiones (a cachear).")
        return

    secrets = cargar_secretos()
    conn = sqlite3.connect(DB_PATH)
    crear_esquema(conn)

    session = requests.Session()
    total_nuevos = 0
    total_cacheados = 0

    for country, query, page in consultas_planificadas():
        key = cache_key(country, query, page)
        fetched_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")

        if not args.force:
            cur = conn.execute(
                "SELECT payload FROM api_cache WHERE cache_key = ?", (key,)
            )
            fila = cur.fetchone()
            if fila:
                total_cacheados += 1
                payload = json.loads(fila[0])
            else:
                payload = None
        else:
            payload = None

        if payload is None:
            print(f"-> Descargando {country} / {query!r} ...")
            for intento in (1, 2):
                try:
                    payload = llamar_api(session, secrets, country, query, page)
                    break
                except requests.RequestException as e:
                    print(f"   Error (intento {intento}): {e}")
                    time.sleep(2)
            else:
                print(f"   [!] No se pudo descargar {country} / {query!r}. "
                      "Se omite.")
                continue
            guardar_cache(conn, key, country, query, page, fetched_at, payload)
            time.sleep(0.6)  # respeta el rate limit de la API
        else:
            print(f"=  Cache {country} / {query!r}")

        resultados = payload.get("results") or []
        ofertas = [normalizar_oferta(ad, country, query, fetched_at)
                   for ad in resultados]
        nuevos = insertar_ofertas(conn, ofertas)
        total_nuevos += nuevos
        if not ofertas:
            print(f"   (sin resultados para {country} / {query!r})")

    conn.close()
    print(f"\nListo. Nuevas ofertas guardadas: {total_nuevos} | "
          f"Respuestas desde cache: {total_cacheados}")


if __name__ == "__main__":
    main()
