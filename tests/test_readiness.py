"""Readiness must inspect dependencies without triggering fetches or uploads."""

from datetime import datetime, timedelta, timezone
import importlib
import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import requests
import valkey
from urllib3.exceptions import HTTPError


@pytest.fixture
def readiness():
    module = importlib.import_module("src.app")
    now = datetime.now(timezone.utc)
    with patch.object(module, "cache") as cache_mock, \
            patch.object(module, "storage") as storage_mock, \
            patch.dict(module.SENSEBOX_ACCESS, clear=True):
        for box_id in module.SENSEBOX_IDS:
            module.record_sensebox_access(box_id, True)
        cache_mock.get.return_value = json.dumps({
            "sensebox_ids": module.SENSEBOX_IDS, "boxes": [{}],
            "refreshed_at": now.isoformat(),
        })
        storage_mock.list_objects.return_value = [SimpleNamespace(
            object_name="temperatures/2026-10-01T00-00-00-000000Z.json",
            last_modified=now - timedelta(minutes=5),
        )]
        yield module, module.app.test_client(), cache_mock, storage_mock


def test_ready_reads_persisted_snapshot_without_writes(readiness):
    module, client, cache_mock, storage_mock = readiness
    with patch.object(module, "fetch_box_data") as fetch:
        response = client.get("/readyz")
    assert response.status_code == 200
    assert all(response.json["checks"].values())
    fetch.assert_not_called()
    cache_mock.set.assert_not_called()
    storage_mock.put_object.assert_not_called()


@pytest.mark.parametrize("stored", [None, "invalid", "null", "{}"])
def test_missing_or_invalid_cache_is_not_ready(readiness, stored):
    _, client, cache_mock, _ = readiness
    cache_mock.get.return_value = stored
    assert client.get("/readyz").status_code == 503


@pytest.mark.parametrize("age_seconds, expected", [(599, 200), (601, 503), (-60, 503)])
def test_cache_age_limit(readiness, age_seconds, expected):
    _, client, cache_mock, _ = readiness
    data = json.loads(cache_mock.get.return_value)
    data["refreshed_at"] = (
        datetime.now(timezone.utc) - timedelta(seconds=age_seconds)).isoformat()
    cache_mock.get.return_value = json.dumps(data)
    assert client.get("/readyz").status_code == expected


@pytest.mark.parametrize("age_seconds, expected", [(599, 200), (601, 503), (-60, 503)])
def test_snapshot_age_limit(readiness, age_seconds, expected):
    _, client, _, storage_mock = readiness
    storage_mock.list_objects.return_value[0].last_modified = (
        datetime.now(timezone.utc) - timedelta(seconds=age_seconds))
    assert client.get("/readyz").status_code == expected


def test_no_snapshot_is_not_ready(readiness):
    _, client, _, storage_mock = readiness
    storage_mock.list_objects.return_value = []
    assert client.get("/readyz").status_code == 503


@pytest.mark.parametrize("count, failures, expected", [
    (1, 0, 200), (1, 1, 503), (3, 1, 200), (3, 2, 503),
    (5, 3, 200), (5, 4, 503),
])
def test_custom_accessibility_threshold(readiness, count, failures, expected):
    module, client, cache_mock, _ = readiness
    ids = [f"box-{index}" for index in range(count)]
    data = json.loads(cache_mock.get.return_value)
    data["sensebox_ids"] = ids
    cache_mock.get.return_value = json.dumps(data)
    with patch.object(module, "SENSEBOX_IDS", ids):
        for index, box_id in enumerate(ids):
            module.record_sensebox_access(box_id, index >= failures)
        assert client.get("/readyz").status_code == expected


def test_unknown_startup_accessibility_is_not_ready(readiness):
    module, client, _, _ = readiness
    module.SENSEBOX_ACCESS.clear()
    assert client.get("/readyz").status_code == 503


def test_expired_accessibility_observations_are_not_ready(readiness):
    module, client, _, _ = readiness
    old = datetime.now(timezone.utc) - timedelta(minutes=11)
    for box_id in module.SENSEBOX_IDS:
        module.SENSEBOX_ACCESS[box_id] = (True, old)
    assert client.get("/readyz").status_code == 503


def test_readiness_dependency_failures(readiness):
    _, client, cache_mock, storage_mock = readiness
    cache_mock.get.side_effect = valkey.exceptions.ConnectionError("offline")
    storage_mock.list_objects.side_effect = HTTPError("offline")
    response = client.get("/readyz")
    assert response.status_code == 503
    assert response.json["checks"] == {
        "senseboxes": True, "cache": False, "storage": False}


def test_http_success_with_old_reading_is_accessible(readiness):
    module, _, _, _ = readiness
    with patch.object(module.requests, "get") as get:
        get.return_value.json.return_value = {"sensors": []}
        module.fetch_box_data("old-reading")
        assert module.SENSEBOX_ACCESS["old-reading"][0] is True
        get.side_effect = requests.ConnectionError("offline")
        with pytest.raises(requests.ConnectionError):
            module.fetch_box_data("old-reading")
        assert module.SENSEBOX_ACCESS["old-reading"][0] is False
