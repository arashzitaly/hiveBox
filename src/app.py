"""HiveBox Flask application."""

from datetime import datetime, timezone
import os
import requests
from flask import Flask, jsonify
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from werkzeug.wrappers import Response

SENSEBOX_IDS = os.environ.get(
    "SENSEBOX_IDS",
    "5eba5fbad46fb8001b799786,5c21ff8f919bf8001adf2488,5ade1acf223bd80019a1011c",
).split(",")

__version__ = "0.0.1"

app = Flask(__name__)


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
    return age.total_seconds() <= 3600


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


def fetch_recent_temperature(box_id):
    """Fetch one recent temperature value for a configured senseBox."""
    response = requests.get(
        f"https://api.opensensemap.org/boxes/{box_id}", timeout=5)
    response.raise_for_status()
    return extract_recent_temperature(response.json())


@app.get("/version")
def version():
    """Return the application version."""
    return jsonify({"version": __version__})


@app.get("/temperature")
def temperature():
    """Return the average temperature from openSenseMap senseBoxes."""
    temperatures = []

    for box_id in SENSEBOX_IDS:
        try:
            recent_temperature = fetch_recent_temperature(box_id)
            if recent_temperature is not None:
                temperatures.append(recent_temperature)
        except (KeyError, TypeError, ValueError, requests.RequestException):
            continue

    if not temperatures:
        return jsonify({"error": "No valid temperature data within the last hour"}), 503

    average = round(sum(temperatures) / len(temperatures), 2)
    status = calculate_temperature_status(average)

    return jsonify({"temperature": average, "status": status})


@app.get("/metrics")
def metrics():
    """Return Prometheus metrics."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
