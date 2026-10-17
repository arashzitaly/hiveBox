"""HiveBox Flask application."""

from datetime import datetime, timezone
import io
import json
import os
import threading
import requests
import valkey
from flask import Flask, jsonify
from minio import Minio
from minio.error import MinioException
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from urllib3.exceptions import HTTPError
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

storage = Minio(
    os.environ.get("MINIO_ENDPOINT", "127.0.0.1:9000"),
    access_key=os.environ.get("MINIO_ACCESS_KEY"),
    secret_key=os.environ.get("MINIO_SECRET_KEY"),
    secure=False,
)
STORAGE_BUCKET = "hivebox"
STORAGE_INTERVAL_SECONDS = 300
READINESS_MAX_AGE_SECONDS = 600
SENSEBOX_ACCESS = {}
SENSEBOX_ACCESS_LOCK = threading.Lock()
SNAPSHOT_SAVES = Counter(
    "hivebox_snapshot_saves_total",
    "Temperature snapshot save attempts",
    ["result"],
)
for save_outcome in ("success", "error", "no_data"):
    SNAPSHOT_SAVES.labels(result=save_outcome)


def save_temperature_snapshot(data):
    """Upload a JSON snapshot to MinIO with a timestamped object name."""
    payload = json.dumps(data).encode("utf-8")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%fZ")
    object_name = f"temperatures/{timestamp}.json"

    return storage.put_object(
        STORAGE_BUCKET,
        object_name,
        io.BytesIO(payload),
        length=len(payload),
        content_type="application/json",
    )


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
    try:
        response = requests.get(
            f"https://api.opensensemap.org/boxes/{box_id}", timeout=5)
        response.raise_for_status()
    except requests.RequestException:
        record_sensebox_access(box_id, False)
        raise
    record_sensebox_access(box_id, True)
    return response.json()


def record_sensebox_access(box_id, accessible):
    """Record HTTP accessibility independently of measurement validity."""
    with SENSEBOX_ACCESS_LOCK:
        SENSEBOX_ACCESS[box_id] = (accessible, datetime.now(timezone.utc))


def timestamp_is_ready(timestamp):
    """Accept aware timestamps from now through two cycles ago."""
    age = (datetime.now(timezone.utc) - timestamp).total_seconds()
    return 0 <= age <= READINESS_MAX_AGE_SECONDS


def senseboxes_are_ready():
    """Treat missing or outdated accessibility observations as unavailable."""
    with SENSEBOX_ACCESS_LOCK:
        observations = dict(SENSEBOX_ACCESS)
    failures = 0
    for box_id in SENSEBOX_IDS:
        accessible, checked_at = observations.get(box_id, (False, None))
        if not accessible or checked_at is None or not timestamp_is_ready(checked_at):
            failures += 1
    return bool(SENSEBOX_IDS) and failures < max(1, len(SENSEBOX_IDS) - 1)


def cache_is_ready():
    """Inspect existing cache content without refreshing it."""
    try:
        data = read_cached_temperature()
        return (
            isinstance(data, dict)
            and data["sensebox_ids"] == SENSEBOX_IDS
            and isinstance(data["boxes"], list)
            and bool(data["boxes"])
            and timestamp_is_ready(datetime.fromisoformat(data["refreshed_at"]))
        )
    except (valkey.exceptions.ValkeyError, KeyError, TypeError, ValueError):
        return False


def snapshot_is_ready():
    """Find persisted snapshot objects, including those saved before a restart."""
    try:
        latest = None
        for item in storage.list_objects(STORAGE_BUCKET, prefix="temperatures/", recursive=True):
            name = item.object_name.removeprefix("temperatures/")
            try:
                datetime.strptime(name, "%Y-%m-%dT%H-%M-%S-%fZ.json")
            except ValueError:
                continue
            if item.last_modified is not None:
                if latest is None or item.last_modified > latest:
                    latest = item.last_modified
        return latest is not None and timestamp_is_ready(latest)
    except (MinioException, HTTPError, OSError, TypeError, ValueError):
        return False


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
            app.logger.exception("Failed to fetch senseBox %s", box_id)
            continue

    temperatures = temperatures_from_boxes(boxes)
    if temperatures:
        save_cached_temperature({
            "boxes": boxes,
            "sensebox_ids": SENSEBOX_IDS,
            "refreshed_at": datetime.now(timezone.utc).isoformat(),
        })
    return temperatures


def run_cache_refresh_loop(stop_event=None):
    """Refresh immediately, then wait five minutes between attempts."""
    if stop_event is None:
        stop_event = threading.Event()
    while not stop_event.is_set():
        try:
            if not refresh_temperature_cache():
                app.logger.warning(
                    "Scheduled cache refresh found no valid readings")
        except valkey.exceptions.ValkeyError:
            app.logger.exception("Scheduled cache refresh failed")
        stop_event.wait(CACHE_TTL_SECONDS)


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


def store_temperature_snapshot():
    """Upload an average of valid readings, or return None when none exist."""
    try:
        temperatures = cached_temperature_values()
        if not temperatures:
            temperatures = refresh_temperature_cache()
        if not temperatures:
            SNAPSHOT_SAVES.labels(result="no_data").inc()
            return None
        average = round(sum(temperatures) / len(temperatures), 2)
        snapshot = {
            "temperature": average,
            "status": calculate_temperature_status(average),
            "sensebox_ids": SENSEBOX_IDS,
            "stored_at": datetime.now(timezone.utc).isoformat(),
        }
        result = save_temperature_snapshot(snapshot)
    except (valkey.exceptions.ValkeyError, MinioException, HTTPError, OSError):
        SNAPSHOT_SAVES.labels(result="error").inc()
        raise
    SNAPSHOT_SAVES.labels(result="success").inc()
    return result


def run_snapshot_store_loop(stop_event=None):
    """Save immediately and wait five minutes after each successful or failed attempt."""
    if stop_event is None:
        stop_event = threading.Event()
    while not stop_event.is_set():
        try:
            result = store_temperature_snapshot()
            if result is None:
                app.logger.warning("Scheduled snapshot save found no valid readings")
            else:
                app.logger.info("Scheduled snapshot saved: %s", result.object_name)
        except (valkey.exceptions.ValkeyError, MinioException, HTTPError, OSError):
            app.logger.exception("Scheduled snapshot save failed")
        stop_event.wait(STORAGE_INTERVAL_SECONDS)


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


@app.get("/store")
def store():
    """Save a temperature snapshot immediately, reporting dependency failures."""
    try:
        result = store_temperature_snapshot()
    except valkey.exceptions.ValkeyError:
        app.logger.exception("Snapshot save failed: cache unavailable")
        return jsonify({"error": "Temperature cache unavailable"}), 503
    except (MinioException, HTTPError, OSError):
        app.logger.exception("Snapshot save failed: storage unavailable")
        return jsonify({"error": "Temperature storage unavailable"}), 503

    if result is None:
        return jsonify({"error": "No valid temperature data within the last hour"}), 503
    return jsonify({"bucket": STORAGE_BUCKET, "object_name": result.object_name})


@app.get("/readyz")
def readyz():
    """Inspect readiness without fetching sensor data or writing snapshots."""
    checks = {
        "senseboxes": senseboxes_are_ready(),
        "cache": cache_is_ready(),
        "storage": snapshot_is_ready(),
    }
    ready = all(checks.values())
    return jsonify({"status": "ready" if ready else "not_ready", "checks": checks}), (
        200 if ready else 503)


@app.get("/metrics")
def metrics():
    """Return Prometheus metrics."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    threading.Thread(
        target=run_cache_refresh_loop, name="cache-refresh", daemon=True
    ).start()
    threading.Thread(
        target=run_snapshot_store_loop, name="snapshot-store", daemon=True
    ).start()
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=8080)
