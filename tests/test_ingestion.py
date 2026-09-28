"""Tests unitaires : aucun appel réseau réel, aucune base de données.

On simule (mock) l'API pour vérifier le comportement de notre code.
Lancement :  pytest -v
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from ingestion.load_raw import build_status_rows
from ingestion.velib_client import VelibAPIError, fetch_stations

SAMPLE_STATION = {
    "station_id": 213688169,
    "stationCode": "16107",
    "num_bikes_available": 4,
    "num_bikes_available_types": [{"mechanical": 2}, {"ebike": 2}],
    "num_docks_available": 31,
    "is_installed": 1,
    "is_renting": 1,
    "is_returning": 1,
    "last_reported": 1790535617,
}


def fake_response(payload: dict) -> MagicMock:
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


@patch("ingestion.velib_client.requests.get")
def test_fetch_returns_station_list(mock_get):
    mock_get.return_value = fake_response({"data": {"stations": [SAMPLE_STATION]}})
    stations = fetch_stations("http://fake-url")
    assert stations == [SAMPLE_STATION]


@patch("ingestion.velib_client.time.sleep")  # on ne veut pas attendre pendant les tests
@patch("ingestion.velib_client.requests.get")
def test_fetch_retries_then_fails(mock_get, _mock_sleep):
    mock_get.side_effect = requests.ConnectionError("réseau coupé")
    with pytest.raises(VelibAPIError):
        fetch_stations("http://fake-url", retries=3)
    assert mock_get.call_count == 3


@patch("ingestion.velib_client.time.sleep")
@patch("ingestion.velib_client.requests.get")
def test_fetch_rejects_empty_payload(mock_get, _mock_sleep):
    mock_get.return_value = fake_response({"data": {"stations": []}})
    with pytest.raises(VelibAPIError):
        fetch_stations("http://fake-url", retries=1)


def test_build_status_rows_skips_incomplete_stations():
    incomplete = {"station_id": 1}  # pas de last_reported
    rows = build_status_rows([SAMPLE_STATION, incomplete])
    assert len(rows) == 1
    assert rows[0][0] == 213688169
    assert rows[0][1] == 1790535617
