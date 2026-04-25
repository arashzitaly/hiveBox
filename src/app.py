"""HiveBox Flask application."""

from datetime import datetime, timezone
import os
import requests
from flask import Flask, jsonify
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

SENSEBOX_IDS = os.environ.get(
    "SENSEBOX_IDS",
    "5eba5fbad46fb8001b799786,5c21ff8f919bf8001adf2488,5ade1acf223bd80019a1011c",
).split(",")

__version__ = "0.0.1"

app = Flask(__name__)


def temperature_status(temperature_value):
    """Return the Phase 4 status label for a temperature value."""
    if temperature_value < 10:
        return "Too Cold"
    if 11 <= temperature_value <= 36:
        return "Good"
    if temperature_value > 37:
        return "Too Hot"
    return "Good"


@app.get("/version")
def version():
    """Return the application version."""
    return jsonify({"version": __version__})


@app.get("/metrics")
def metrics():
    """Return default Prometheus metrics."""
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


@app.get("/temperature")
def temperature():
    """Return the average temperature from openSenseMap senseBoxes."""
    temperatures = []

    for box_id in SENSEBOX_IDS:
        response = requests.get(
            f"https://api.opensensemap.org/boxes/{box_id}", timeout=5)
        box = response.json()

        for sensor in box["sensors"]:
            if sensor["title"] == "Temperatur":
                measurement = sensor["lastMeasurement"]
                created_at = datetime.fromisoformat(
                    measurement["createdAt"].replace("Z", "+00:00")
                )
                age = datetime.now(timezone.utc) - created_at
                if age.total_seconds() <= 3600:
                    temperatures.append(float(measurement["value"]))
                break

    if not temperatures:
        return jsonify({"error": "No valid temperature data within the last hour"}), 503

    average = round(sum(temperatures) / len(temperatures), 2)
    return jsonify({"temperature": average, "status": temperature_status(average)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
