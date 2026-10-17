"""Verify cache-backed endpoint behavior without external services."""

from datetime import datetime, timedelta, timezone
import importlib
import json
from unittest.mock import MagicMock, patch

import pytest
import requests
import valkey
from prometheus_client import REGISTRY
from minio.error import MinioException
from urllib3.exceptions import HTTPError


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


@pytest.mark.parametrize("outcome", ["success", "no_data", "error"])
def test_save_metrics_count_one_outcome_and_expose_it(cache_client, outcome):
    """Each shared save attempt increments only its outcome, including failures."""
    client, cache_mock, sensebox_get, module = cache_client
    labels = ("success", "error", "no_data")

    def count(label):
        return REGISTRY.get_sample_value(
            "hivebox_snapshot_saves_total", {"result": label})

    before = {label: count(label) for label in labels}
    cache_mock.get.return_value = cached_payload(module, [box(0)])
    if outcome == "no_data":
        cache_mock.get.return_value = None
        sensebox_get.return_value.json.return_value = box(20, 61)
    with patch.object(module, "storage") as storage_mock:
        storage_mock.put_object.return_value.object_name = "temperatures/test.json"
        if outcome == "error":
            storage_mock.put_object.side_effect = HTTPError("offline")
            with pytest.raises(HTTPError):
                module.store_temperature_snapshot()
        else:
            result = module.store_temperature_snapshot()
            assert (result is None) == (outcome == "no_data")
    for label in labels:
        assert count(label) - before[label] == int(label == outcome)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert f'hivebox_snapshot_saves_total{{result="{outcome}"}}' in response.text


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


def test_store_uploads_valid_zero_from_cache(cache_client):
    client, cache_mock, sensebox_get, module = cache_client
    cache_mock.get.return_value = cached_payload(module, [box(0), box(100, 61)])
    with patch.object(module, "storage") as storage_mock:
        storage_mock.put_object.return_value.object_name = "temperatures/test.json"
        response = client.get("/store")
        assert response.status_code == 200
        assert response.json == {
            "bucket": "hivebox", "object_name": "temperatures/test.json"}
        args, kwargs = storage_mock.put_object.call_args
        payload = args[2].read()
        snapshot = json.loads(payload)
        assert snapshot["temperature"] == 0.0
        assert snapshot["sensebox_ids"] == module.SENSEBOX_IDS
        assert snapshot["stored_at"]
        assert kwargs["length"] == len(payload)
        sensebox_get.assert_not_called()


def test_store_refreshes_missing_cache(cache_client):
    client, _, sensebox_get, module = cache_client
    with patch.object(module, "storage") as storage_mock:
        storage_mock.put_object.return_value.object_name = "temperatures/new.json"
        assert client.get("/store").status_code == 200
        assert sensebox_get.called
        storage_mock.put_object.assert_called_once()


def test_store_does_not_upload_old_readings(cache_client):
    client, _, sensebox_get, module = cache_client
    sensebox_get.return_value.json.return_value = box(20, 61)
    with patch.object(module, "storage") as storage_mock:
        assert client.get("/store").status_code == 503
        storage_mock.put_object.assert_not_called()


@pytest.mark.parametrize("error", [MinioException("denied"), HTTPError("offline"),
                                  OSError("connection failed")])
def test_store_reports_storage_failure(cache_client, error):
    client, cache_mock, _, module = cache_client
    cache_mock.get.return_value = cached_payload(module, [box(20)])
    with patch.object(module, "storage") as storage_mock:
        storage_mock.put_object.side_effect = error
        response = client.get("/store")
        assert response.status_code == 503
        assert response.json == {"error": "Temperature storage unavailable"}


def test_store_reports_cache_failure(cache_client):
    client, cache_mock, _, module = cache_client
    cache_mock.get.side_effect = valkey.exceptions.ConnectionError("offline")
    with patch.object(module, "storage") as storage_mock:
        response = client.get("/store")
        assert response.status_code == 503
        assert response.json == {"error": "Temperature cache unavailable"}
        storage_mock.put_object.assert_not_called()


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


def test_scheduled_refresh_retries_after_valkey_failure(cache_client):
    """A failed refresh must log its cause and allow the next attempt."""
    _, _, _, module = cache_client
    stop_event = MagicMock()
    stop_event.is_set.side_effect = [False, False, True]
    with patch.object(module, "refresh_temperature_cache") as refresh:
        refresh.side_effect = [valkey.exceptions.ConnectionError("offline"), [22.5]]
        with patch.object(module.app.logger, "exception") as log_error:
            module.run_cache_refresh_loop(stop_event)
    assert refresh.call_count == 2
    assert stop_event.wait.call_count == 2
    stop_event.wait.assert_called_with(300)
    log_error.assert_called_once_with("Scheduled cache refresh failed")


def test_scheduled_refresh_reports_no_valid_readings(cache_client):
    """An empty refresh must be visible and still wait before retrying."""
    _, _, _, module = cache_client
    stop_event = MagicMock()
    stop_event.is_set.side_effect = [False, True]
    with patch.object(module, "refresh_temperature_cache", return_value=[]):
        with patch.object(module.app.logger, "warning") as log_warning:
            module.run_cache_refresh_loop(stop_event)
    log_warning.assert_called_once_with("Scheduled cache refresh found no valid readings")
    stop_event.wait.assert_called_once_with(300)


@pytest.mark.parametrize("error", [valkey.exceptions.ConnectionError("offline"),
                                  MinioException("denied"), HTTPError("offline"),
                                  OSError("connection failed")])
def test_scheduled_store_recovers_after_failure(cache_client, error):
    """Dependency failures must not stop subsequent scheduled saves."""
    _, _, _, module = cache_client
    stop_event = MagicMock()
    stop_event.is_set.side_effect = [False, False, True]
    result = MagicMock(object_name="temperatures/recovered.json")
    with patch.object(module, "store_temperature_snapshot", side_effect=[error, result]) as save:
        with patch.object(module.app.logger, "exception") as log_error:
            module.run_snapshot_store_loop(stop_event)
    assert save.call_count == 2
    assert stop_event.wait.call_args_list == [((300,),), ((300,),)]
    log_error.assert_called_once_with("Scheduled snapshot save failed")


def test_scheduled_store_waits_when_no_valid_readings(cache_client):
    """No data must be reported without a tight retry loop."""
    _, _, _, module = cache_client
    stop_event = MagicMock()
    stop_event.is_set.side_effect = [False, True]
    with patch.object(module, "store_temperature_snapshot", return_value=None):
        with patch.object(module.app.logger, "warning") as warning:
            module.run_snapshot_store_loop(stop_event)
    warning.assert_called_once_with("Scheduled snapshot save found no valid readings")
    stop_event.wait.assert_called_once_with(300)
