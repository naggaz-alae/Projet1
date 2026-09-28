"""Point d'entrée de l'ingestion : API Vélib' -> tables raw de PostgreSQL.

Lancement :  python -m ingestion.load_raw
"""

import logging
import os

import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb

from ingestion.velib_client import INFORMATION_URL, STATUS_URL, fetch_stations

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("load_raw")

INSERT_STATUS = """
    INSERT INTO raw.station_status (station_id, last_reported, payload)
    VALUES (%s, %s, %s)
    ON CONFLICT (station_id, last_reported) DO NOTHING
"""

UPSERT_INFORMATION = """
    INSERT INTO raw.station_information (station_id, payload)
    VALUES (%s, %s)
    ON CONFLICT (station_id) DO UPDATE
        SET payload = EXCLUDED.payload,
            fetched_at = now()
"""


def get_connection() -> psycopg.Connection:
    load_dotenv()
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        dbname=os.environ["POSTGRES_DB"],
    )


def build_status_rows(stations: list[dict]) -> list[tuple]:
    """Transforme la réponse API en lignes prêtes à insérer.

    Les stations sans identifiant ou sans horodatage sont ignorées
    (on ne peut pas les dédoublonner).
    """
    rows = []
    for s in stations:
        if s.get("station_id") is None or s.get("last_reported") is None:
            logger.warning("Station ignorée (champs clés manquants) : %s", s)
            continue
        rows.append((int(s["station_id"]), int(s["last_reported"]), Jsonb(s)))
    return rows


def build_information_rows(stations: list[dict]) -> list[tuple]:
    return [(int(s["station_id"]), Jsonb(s)) for s in stations if s.get("station_id") is not None]


def run() -> None:
    status = fetch_stations(STATUS_URL)
    information = fetch_stations(INFORMATION_URL)

    status_rows = build_status_rows(status)
    info_rows = build_information_rows(information)

    # `with` = une transaction : tout est écrit, ou rien (en cas d'erreur)
    with get_connection() as conn, conn.cursor() as cur:
        cur.executemany(UPSERT_INFORMATION, info_rows)
        cur.execute("SELECT count(*) FROM raw.station_status")
        before = cur.fetchone()[0]
        cur.executemany(INSERT_STATUS, status_rows)
        cur.execute("SELECT count(*) FROM raw.station_status")
        after = cur.fetchone()[0]

    logger.info("Référentiel : %s stations à jour", len(info_rows))
    logger.info("Disponibilités : %s nouvelles lignes (%s reçues, %s déjà connues)",
                after - before, len(status_rows), len(status_rows) - (after - before))


if __name__ == "__main__":
    run()
