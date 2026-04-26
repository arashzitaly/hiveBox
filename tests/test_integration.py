"""Integration tests for HiveBox HTTP endpoints."""

from threading import Thread

import pytest
import requests
from werkzeug.serving import make_server

from src.app import app


@pytest.fixture(name="live_server")
def fixture_live_server():
    """Run the Flask app through a local WSGI server for HTTP integration tests."""
    server = make_server("127.0.0.1", 0, app)
    port = server.server_port
    thread = Thread(target=server.serve_forever)
    thread.start()

    yield f"http://127.0.0.1:{port}"

    server.shutdown()
    thread.join()


def test_version_endpoint_over_http(live_server):
    """Test /version through a real HTTP request."""
    response = requests.get(f"{live_server}/version", timeout=5)

    assert response.status_code == 200
    assert response.json() == {"version": "0.0.1"}


def test_metrics_endpoint_over_http(live_server):
    """Test /metrics through a real HTTP request."""
    response = requests.get(f"{live_server}/metrics", timeout=5)

    assert response.status_code == 200
    assert "python_info" in response.text
