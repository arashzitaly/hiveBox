import pytest
from src.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_version(client):
    response = client.get("/version")
    assert response.status_code == 200
    data = response.get_json()
    assert data == {"version": "0.0.1"}


def test_temperature_returns_200(client):
    response = client.get("/temperature")
    assert response.status_code == 200


def test_temperature_returns_float(client):
    response = client.get("/temperature")
    data = response.get_json()
    assert "temperature" in data
    assert isinstance(data["temperature"], float)
