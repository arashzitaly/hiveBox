from flask import Flask, jsonify
from datetime import datetime, timezone
import requests

SENSEBOX_IDS = [
    "5eba5fbad46fb8001b799786",
    "5c21ff8f919bf8001adf2488",
    "5ade1acf223bd80019a1011c",
]

__version__ = "0.0.1"

app = Flask(__name__)


@app.get("/version")
def version():
    return jsonify({"version": __version__})


@app.get("/temperature")
def temperature():
    temperatures = []

    for box_id in SENSEBOX_IDS:
        response = requests.get(f"https://api.opensensemap.org/boxes/{box_id}")
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
    return jsonify({"temperature": average})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
