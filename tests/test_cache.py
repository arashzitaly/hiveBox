"""Verify cache-backed endpoint behavior without external services."""

from datetime import datetime, timedelta, timezone
import importlib
import json
from unittest.mock import MagicMock, patch

import pytest
import requests
import valkey


@pytest.fixture
def cache_client():
    """Provide a Flask client with isolated Valkey and senseBox dependencies."""
    module = importlib.import_module("src.app")
    module.app.config["TESTING"] = True
    with patch.object(module, "cache") as cache_mock:
        with patch.object(module.requests, "get") as sensebox_get:
            cache_mock.get.return_value = None
            response = MagicMock()
            response.json.return_value = box(22.5)
            sensebox_get.return_value = response
            with module.app.test_client() as client:
                yield client, cache_mock, sensebox_get, module


def box(value, age_minutes=0):
    """Build one sensor reading with its original measurement time."""
    return {"sensors": [{
        "title": "Temperatur",
        "lastMeasurement": {
            "value": str(value),
            "createdAt": (
                datetime.now(timezone.utc) - timedelta(minutes=age_minutes)
            ).isoformat(),
        },
    }]}


def cached_payload(module, boxes, age_minutes=0):
    """Build cache content independently of its Valkey expiration."""
    return json.dumps({
        "boxes": boxes,
        "sensebox_ids": module.SENSEBOX_IDS,
        "refreshed_at": (
            datetime.now(timezone.utc) - timedelta(minutes=age_minutes)
        ).isoformat(),
    })


def test_fresh_cache_skips_sensebox_fetch(cache_client):
    client, cache_mock, sensebox_get, module = cache_client
    cache_mock.get.return_value = cached_payload(module, [box(20), box(24)])
    response = client.get("/temperature")
    assert response.status_code == 200
    assert response.json == {"temperature": 22.0, "status": "Good"}
    sensebox_get.assert_not_called()
    cache_mock.set.assert_not_called()


def test_cache_miss_fetches_and_stores_json(cache_client):
    client, cache_mock, sensebox_get, module = cache_client
    response = client.get("/temperature")
    assert response.status_code == 200
    assert response.json == {"temperature": 22.5, "status": "Good"}
    assert sensebox_get.call_count == len(module.SENSEBOX_IDS)
    args, kwargs = cache_mock.set.call_args
    assert args[0] == module.CACHE_KEY
    stored = json.loads(args[1])
    assert stored["sensebox_ids"] == module.SENSEBOX_IDS
    assert stored["boxes"][0]["sensors"][0]["lastMeasurement"]["createdAt"]
    assert kwargs == {"ex": 300}


def test_stale_cache_refreshes_before_returning(cache_client):
    client, cache_mock, sensebox_get, module = cache_client
    cache_mock.get.return_value = cached_payload(module, [box(5)], age_minutes=6)
    response = client.get("/temperature")
    assert response.status_code == 200
    assert response.json["temperature"] == 22.5
    assert sensebox_get.called
    cache_mock.set.assert_called_once()


@pytest.mark.parametrize("stored", ["invalid JSON", '{"temperature": 22.5}', "null"])
def test_invalid_cache_refreshes(cache_client, stored):
    client, cache_mock, sensebox_get, _ = cache_client
    cache_mock.get.return_value = stored
    assert client.get("/temperature").status_code == 200
    assert sensebox_get.called
    cache_mock.set.assert_called_once()


def test_cache_endpoint_forces_refresh(cache_client):
    client, cache_mock, sensebox_get, module = cache_client
    cache_mock.get.return_value = cached_payload(module, [box(5)])
    response = client.get("/cache")
    assert response.status_code == 200
    assert response.json["temperature"] == 22.5
    assert sensebox_get.call_count == len(module.SENSEBOX_IDS)
    cache_mock.get.assert_not_called()
    cache_mock.set.assert_called_once()


def test_old_sensor_reading_is_excluded_from_fresh_cache(cache_client):
    client, cache_mock, sensebox_get, module = cache_client
    cache_mock.get.return_value = cached_payload(module, [box(20), box(100, 61)])
    response = client.get("/temperature")
    assert response.status_code == 200
    assert response.json["temperature"] == 20.0
    sensebox_get.assert_not_called()


def test_all_cached_readings_old_triggers_refresh(cache_client):
    client, cache_mock, sensebox_get, module = cache_client
    cache_mock.get.return_value = cached_payload(module, [box(100, 61)])
    assert client.get("/temperature").json["temperature"] == 22.5
    assert sensebox_get.called


@pytest.mark.parametrize("endpoint", ["/temperature", "/cache"])
def test_no_recent_readings_returns_503_without_write(cache_client, endpoint):
    client, cache_mock, sensebox_get, _ = cache_client
    sensebox_get.return_value.json.return_value = box(22.5, 61)
    response = client.get(endpoint)
    assert response.status_code == 503
    assert response.json == {"error": "No valid temperature data within the last hour"}
    cache_mock.set.assert_not_called()


def test_sensebox_outage_returns_503(cache_client):
    client, cache_mock, sensebox_get, _ = cache_client
    sensebox_get.side_effect = requests.ConnectionError("senseBox unavailable")
    assert client.get("/temperature").status_code == 503
    cache_mock.set.assert_not_called()


@pytest.mark.parametrize("operation", ["get", "set"])
def test_valkey_failure_returns_503(cache_client, operation):
    client, cache_mock, _, _ = cache_client
    getattr(cache_mock, operation).side_effect = valkey.exceptions.ConnectionError()
    response = client.get("/temperature")
    assert response.status_code == 503
    assert response.json == {"error": "Temperature cache unavailable"}


def test_changed_sensebox_configuration_invalidates_cache(cache_client):
    client, cache_mock, sensebox_get, module = cache_client
    stored = json.loads(cached_payload(module, [box(5)]))
    stored["sensebox_ids"] = ["different-box"]
    cache_mock.get.return_value = json.dumps(stored)
    assert client.get("/temperature").json["temperature"] == 22.5
    assert sensebox_get.called
