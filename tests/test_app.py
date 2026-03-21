"""Unit tests for HiveBox Flask application."""

from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
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
