"""HiveBox Flask application."""

from datetime import datetime, timezone
import json
import os
import requests
import valkey
from flask import Flask, jsonify
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from werkzeug.wrappers import Response

SENSEBOX_IDS = os.environ.get(
    "SENSEBOX_IDS",
    "5eba5fbad46fb8001b799786,5c21ff8f919bf8001adf2488,5ade1acf223bd80019a1011c",
).split(",")

__version__ = "0.0.1"

app = Flask(__name__)
cache = valkey.Valkey(
    host=os.environ.get("VALKEY_HOST", "127.0.0.1"),
    port=int(os.environ.get("VALKEY_PORT", "6379")),
    decode_responses=True,
    socket_connect_timeout=3,
    socket_timeout=3,
)
CACHE_KEY = "hivebox:temperature"
CACHE_TTL_SECONDS = 300


def save_cached_temperature(data):
    """Convert a temperature dictionary to JSON and cache it for five minutes."""
    return cache.set(CACHE_KEY, json.dumps(data), ex=CACHE_TTL_SECONDS)


def read_cached_temperature():
    """Restore the cached dictionary, or return None when the key is missing."""
    stored = cache.get(CACHE_KEY)
    if stored is None:
        return None
    return json.loads(stored)


def calculate_temperature_status(average):
    """Return the Phase 4 temperature status for an average value."""
    if average < 10:
        return "Too Cold"
    if average <= 36:
        return "Good"
    return "Too Hot"


def is_recent_measurement(created_at):
    """Return whether a measurement timestamp is no older than one hour."""
    measured_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    age = datetime.now(timezone.utc) - measured_at
    return 0 <= age.total_seconds() <= 3600


def extract_recent_temperature(box):
    """Return the latest recent temperature from a senseBox payload."""
    for sensor in box.get("sensors", []):
        if sensor.get("title") != "Temperatur":
            continue

        measurement = sensor.get("lastMeasurement")
        if not measurement or not is_recent_measurement(measurement["createdAt"]):
            return None

        return float(measurement["value"])

    return None


def fetch_box_data(box_id):
    """Fetch a senseBox payload, including original measurement timestamps."""
    response = requests.get(
        f"https://api.opensensemap.org/boxes/{box_id}", timeout=5)
    response.raise_for_status()
    return response.json()


def temperatures_from_boxes(boxes):
    """Select valid temperatures, checking measurement age on every read."""
    temperatures = []
    for box in boxes:
        if not isinstance(box, dict):
            continue
        try:
            value = extract_recent_temperature(box)
            if value is not None:
                temperatures.append(value)
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
    return temperatures


def refresh_temperature_cache():
    """Fetch current senseBox data and replace the cache when readings are valid."""
    boxes = []
    for box_id in SENSEBOX_IDS:
        try:
            boxes.append(fetch_box_data(box_id))
        except (KeyError, TypeError, ValueError, requests.RequestException):
            continue

    temperatures = temperatures_from_boxes(boxes)
    if temperatures:
        save_cached_temperature({
            "boxes": boxes,
            "sensebox_ids": SENSEBOX_IDS,
            "refreshed_at": datetime.now(timezone.utc).isoformat(),
        })
    return temperatures


def cached_temperature_values():
    """Read temperatures only when the cache is fresh and matches configured IDs."""
    try:
        data = read_cached_temperature()
        if data is None or data["sensebox_ids"] != SENSEBOX_IDS:
            return []
        refreshed_at = datetime.fromisoformat(data["refreshed_at"])
        age = (datetime.now(timezone.utc) - refreshed_at).total_seconds()
        if not 0 <= age < CACHE_TTL_SECONDS:
            return []
        return temperatures_from_boxes(data["boxes"])
    except (KeyError, TypeError, ValueError, AttributeError):
        return []


def temperature_response(force_refresh=False):
    """Return a temperature result from cache or a fresh senseBox fetch."""
    try:
        temperatures = [] if force_refresh else cached_temperature_values()
        if not temperatures:
            temperatures = refresh_temperature_cache()
    except valkey.exceptions.ValkeyError:
        return jsonify({"error": "Temperature cache unavailable"}), 503

    if not temperatures:
        return jsonify({"error": "No valid temperature data within the last hour"}), 503

    average = round(sum(temperatures) / len(temperatures), 2)
    return jsonify({
        "temperature": average,
        "status": calculate_temperature_status(average),
    })


@app.get("/version")
def version():
    """Return the application version."""
    return jsonify({"version": __version__})


@app.get("/temperature")
def temperature():
    """Return an average from fresh cached readings, refreshing on a cache miss."""
    return temperature_response()


@app.get("/cache")
def refresh_cache():
    """Force an immediate senseBox fetch and cache update."""
    return temperature_response(force_refresh=True)


@app.get("/metrics")
def metrics():
    """Return Prometheus metrics."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=8080)
