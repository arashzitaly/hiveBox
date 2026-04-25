"""Unit tests for HiveBox Flask application."""

from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import importlib
import pytest
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the app."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_version(client):
    """Test /version returns correct version string."""
    response = client.get("/version")
    assert response.status_code == 200
    assert response.get_json() == {"version": "0.0.1"}


def test_metrics_returns_prometheus_text(client):
    """Test /metrics returns Prometheus metrics text."""
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.content_type.startswith("text/plain")
    assert b"python_info" in response.data


def test_sensebox_ids_can_be_configured_from_env(monkeypatch):
    """Test senseBox IDs are read from the SENSEBOX_IDS environment variable."""
    monkeypatch.setenv("SENSEBOX_IDS", "box-one,box-two")

    import src.app as app_module

    reloaded_app = importlib.reload(app_module)

    assert reloaded_app.SENSEBOX_IDS == ["box-one", "box-two"]


def make_mock_box(temp_value):
    """Return a mock senseBox API response with a given temperature."""
    return {
        "sensors": [
            {
                "title": "Temperatur",
                "lastMeasurement": {
                    "value": str(temp_value),
                    "createdAt": datetime.now(timezone.utc).strftime(
                        "%Y-%m-%dT%H:%M:%S.000Z"
                    ),
                },
            }
        ]
    }


@patch("src.app.requests.get")
def test_temperature_returns_200(mock_get, client):
    """Test /temperature returns 200 with valid mocked data."""
    mock_response = MagicMock()
    mock_response.json.return_value = make_mock_box(10.0)
    mock_get.return_value = mock_response

    response = client.get("/temperature")
    assert response.status_code == 200


@patch("src.app.requests.get")
def test_temperature_returns_float(mock_get, client):
    """Test /temperature returns a float temperature value."""
    mock_response = MagicMock()
    mock_response.json.return_value = make_mock_box(10.0)
    mock_get.return_value = mock_response

    response = client.get("/temperature")
    data = response.get_json()
    assert "temperature" in data
    assert isinstance(data["temperature"], float)


@pytest.mark.parametrize(
    ("temperature_value", "expected_status"),
    [
        (9.0, "Too Cold"),
        (20.0, "Good"),
        (38.0, "Too Hot"),
    ],
)
@patch("src.app.requests.get")
def test_temperature_returns_status(
    mock_get, client, temperature_value, expected_status
):
    """Test /temperature returns the required Phase 4 status field."""
    mock_response = MagicMock()
    mock_response.json.return_value = make_mock_box(temperature_value)
    mock_get.return_value = mock_response

    response = client.get("/temperature")
    data = response.get_json()

    assert response.status_code == 200
    assert data["status"] == expected_status
