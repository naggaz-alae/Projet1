"""Client HTTP pour l'API open data Vélib' Métropole (format GBFS).

Rôle unique : aller chercher les données et renvoyer une liste de stations.
Il ne sait rien de la base de données -> facile à tester isolément.
"""

import logging
import time

import requests

BASE_URL = "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole"
STATUS_URL = f"{BASE_URL}/station_status.json"
INFORMATION_URL = f"{BASE_URL}/station_information.json"

logger = logging.getLogger(__name__)


class VelibAPIError(Exception):
    """Levée quand l'API ne renvoie pas de données exploitables."""


def fetch_stations(url: str, retries: int = 3, timeout: int = 10) -> list[dict]:
    """Appelle l'API et renvoie la liste `data.stations`.

    Réessaie `retries` fois en cas d'erreur réseau (attente 2s, 4s, 8s...).
    """
    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()  # erreur si code HTTP 4xx / 5xx
            body = response.json()
            stations = body["data"]["stations"]
            if not stations:
                raise VelibAPIError(f"Aucune station renvoyée par {url}")
            logger.info("%s stations récupérées depuis %s", len(stations), url)
            return stations
        except (requests.RequestException, KeyError, ValueError) as err:
            last_error = err
            logger.warning("Tentative %s/%s échouée : %s", attempt, retries, err)
            if attempt < retries:
                time.sleep(2**attempt)

    raise VelibAPIError(f"Échec après {retries} tentatives : {last_error}")
