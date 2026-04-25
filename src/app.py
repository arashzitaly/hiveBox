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
            response = requests.get(
                f"https://api.opensensemap.org/boxes/{box_id}", timeout=5)
            response.raise_for_status()
            box = response.json()

            for sensor in box.get("sensors", []):
                if sensor.get("title") == "Temperatur":
                    measurement = sensor.get("lastMeasurement")
                    if not measurement:
                        break

                    created_at = datetime.fromisoformat(
                        measurement["createdAt"].replace("Z", "+00:00")
                    )
                    age = datetime.now(timezone.utc) - created_at
                    if age.total_seconds() <= 3600:
                        temperatures.append(float(measurement["value"]))
                    break
        except (KeyError, TypeError, ValueError, requests.RequestException):
            continue

    if not temperatures:
        return jsonify({"error": "No valid temperature data within the last hour"}), 503

    average = round(sum(temperatures) / len(temperatures), 2)

    if average < 10:
        status = "Too Cold"
    elif average <= 36:
        status = "Good"
    else:
        status = "Too Hot"

    return jsonify({"temperature": average, "status": status})


@app.get("/metrics")
def metrics():
    """Return Prometheus metrics."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
