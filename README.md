[![Dynamic DevOps Roadmap](https://img.shields.io/badge/Dynamic_DevOps_Roadmap-559e11?style=for-the-badge&logo=Vercel&logoColor=white)](https://devopsroadmap.io/getting-started/)
[![Community](https://img.shields.io/badge/Join_Community-%23FF6719?style=for-the-badge&logo=substack&logoColor=white)](https://newsletter.devopsroadmap.io/subscribe)
[![Telegram Group](https://img.shields.io/badge/Telegram_Group-%232ca5e0?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/DevOpsHive/985)
[![Fork on GitHub](https://img.shields.io/badge/Fork_On_GitHub-%2336465D?style=for-the-badge&logo=github&logoColor=white)](https://github.com/DevOpsHiveHQ/devops-hands-on-project-hivebox/fork)

# HiveBox - DevOps End-to-End Hands-On Project

<p align="center">
  <a href="https://devopsroadmap.io/projects/hivebox" style="display: block; padding: .5em 0; text-align: center;">
    <img alt="HiveBox - DevOps End-to-End Hands-On Project" border="0" width="90%" src="https://devopsroadmap.io/img/projects/hivebox-devops-end-to-end-project.png" />
  </a>
</p>

> [!CAUTION]
> **[Fork](https://github.com/DevOpsHiveHQ/devops-hands-on-project-hivebox/fork)** this repo, and create PRs in your fork, **NOT** in this repo!

> [!TIP]
> If you are looking for the full roadmap, including this project, go back to the [getting started](https://devopsroadmap.io/getting-started) page.

This repository is the starting point for [HiveBox](https://devopsroadmap.io/projects/hivebox/), the end-to-end hands-on project.

You can fork this repository and start implementing the [HiveBox](https://devopsroadmap.io/projects/hivebox/) project. HiveBox project follows the same Dynamic MVP-style mindset used in the [roadmap](https://devopsroadmap.io/).

The project aims to cover the whole Software Development Life Cycle (SDLC). That means each phase will cover all aspects of DevOps, such as planning, coding, containers, testing, continuous integration, continuous delivery, infrastructure, etc.

Happy DevOpsing ♾️

## Before you start

Here is a pre-start checklist:

- ⭐ <a target="_blank" href="https://github.com/DevOpsHiveHQ/dynamic-devops-roadmap">Star the **roadmap** repo</a> on GitHub for better visibility.
- ✉️ <a target="_blank" href="https://newsletter.devopsroadmap.io/subscribe">Join the community</a> for the project community activities, which include mentorship, job posting, online meetings, workshops, career tips and tricks, and more.
- 🌐 <a target="_blank" href="https://t.me/DevOpsHive/985">Join the Telegram group</a> for interactive communication.

## Preparation

- [Create GitHub account](https://docs.github.com/en/get-started/start-your-journey/creating-an-account-on-github) (if you don't have one), then [fork this repository](https://github.com/DevOpsHiveHQ/devops-hands-on-project-hivebox/fork) and start from there.
- [Create GitHub project board](https://docs.github.com/en/issues/planning-and-tracking-with-projects/creating-projects/creating-a-project) for this repository (use `Kanban` template).
- Each phase should be presented as a pull request against the `main` branch. Don’t push directly to the main branch!
- Document as you go. Always assume that someone else will read your project at any phase.
- You can get senseBox IDs by checking the [openSenseMap](https://opensensemap.org/) website. Use 3 senseBox IDs close to each other (you can use the following [5eba5fbad46fb8001b799786](https://opensensemap.org/explore/5eba5fbad46fb8001b799786), [5c21ff8f919bf8001adf2488](https://opensensemap.org/explore/5c21ff8f919bf8001adf2488), and [5ade1acf223bd80019a1011c](https://opensensemap.org/explore/5ade1acf223bd80019a1011c)). Just copy the IDs, you will need them in the next steps.

<br/>
<p align="center">
  <a href="https://devopsroadmap.io/projects/hivebox/" imageanchor="1">
    <img src="https://img.shields.io/badge/Get_Started_Now-559e11?style=for-the-badge&logo=Vercel&logoColor=white" />
  </a><br/>
</p>

---

## Implementation

### Phase 2

#### What
Adds initial Python version script and Dockerfile.

#### How to test

Build the image:
```bash
docker build -t hivebox:v0.0.1 .
```

Run the container:
```bash
docker run hivebox:v0.0.1
```

Expected output:
```
v0.0.1
```

### Phase 5: Valkey cache endpoints (in progress)

The Flask app connects to Valkey using `VALKEY_HOST` (default `127.0.0.1`)
and `VALKEY_PORT` (default `6379`). These defaults apply when Python runs
directly on the host and Valkey publishes port 6379 there.

- `GET /temperature` reads fresh cached senseBox data. Missing, invalid, or
  stale cache content triggers a refresh before calculating the average.
- `GET /cache` always fetches senseBox data and replaces the cache when valid
  readings exist. It returns the new temperature average and status.
- Cache entries expire after 300 seconds. The payload contains senseBox data,
  the configured IDs, and the refresh timestamp. Original measurement times
  are checked on every read; readings older than one hour are excluded.
- Both endpoints return HTTP 503 if no valid readings exist or Valkey fails.
- Starting with `python -m src.app` starts a background refresh immediately,
  then waits 300 seconds after each attempt before retrying. Flask continues
  serving requests during refreshes. Failures are logged and the loop retries.
  Expiration alone does not fetch new data. The thread stops with the process;
  importing the module does not start it. Each application process has its own
  refresh thread. Live scheduled operation still needs verification.

For the local exercise, start the existing Valkey container:

```powershell
docker start hivebox-valkey
python -m pip install -r requirements-dev.txt
python -m src.app
```

In a second PowerShell window, call the endpoints:

```powershell
curl.exe --fail http://127.0.0.1:8080/cache
curl.exe --fail http://127.0.0.1:8080/temperature
```

With reachable Valkey and recent senseBox measurements, both return JSON with
`temperature` and `status`. Inspect the cached JSON and remaining lifetime:

```powershell
docker exec hivebox-valkey valkey-cli GET hivebox:temperature
docker exec hivebox-valkey valkey-cli TTL hivebox:temperature
```

### Phase 5: MinIO snapshots (in progress)

Set `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY` in the shell that starts HiveBox.
`MINIO_ENDPOINT` defaults to `127.0.0.1:9000`; the client currently uses HTTP
for the local exercise. Create the `hivebox` bucket before uploading.

`GET /store` uses valid cached temperatures, refreshing on a cache miss, and
uploads their average, status, configured senseBox IDs, and save timestamp as
JSON under `temperatures/<UTC timestamp>.json`. Zero degrees is valid.
HTTP 200 includes `bucket` and `object_name` after the upload succeeds.
HTTP 503 reports missing valid readings, cache failures, or storage failures.
Dependency exception details are logged rather than returned in the response.
Starting with `python -m src.app` also starts a background snapshot save
immediately, then waits 300 seconds after each attempt. Failed attempts are
logged and retried at the next interval; no valid readings means no upload.
The interval includes the save duration plus the 300-second wait. Each process
has its own daemon thread, which ends when the process exits. Importing the
module does not start the thread. Live periodic storage still needs verification.

```powershell
curl.exe --fail http://127.0.0.1:8080/store
```

`/metrics` includes `hivebox_snapshot_saves_total{result="success|error|no_data"}`
(three separate label values). Both manual and scheduled saves count once in
the shared save helper. Success counts only after upload completes; dependency
errors are counted and re-raised for the caller to handle. No valid readings
counts as `no_data`. All three series start at zero and reset on process restart.

### Phase 5: application Helm chart (in progress)

`charts/hivebox` packages the HiveBox Deployment and Service with configurable
image, replica count, dependency addresses, Secret references, resources, and
probes. Valkey and MinIO remain under `k8s/infra` Kustomize management.
See [the chart guide](charts/hivebox/README.md) for validation, installation,
and the handover from the currently Kustomize-managed application resources.

### Phase 5: readiness (in progress)

`GET /readyz` returns JSON with `status` and boolean `checks` for `senseboxes`,
`cache`, and `storage`. It returns 503 if any check fails; otherwise 200.
The agreed custom accessibility threshold is `max(1, N - 1)` failed boxes,
where N is the configured count. HTTP accessibility is tracked separately from
measurement validity during normal fetches. Unknown observations at startup,
or observations older than 600 seconds, count as unavailable.

Cache content must exist, match the configured IDs, and have a refresh timestamp
no older than 600 seconds. The existing 300-second Valkey TTL can cause readiness
to fail earlier when the key expires. Snapshot readiness lists timestamp-named
JSON objects under `temperatures/` in the existing `hivebox` bucket and checks
the latest object's MinIO last-modified timestamp, accepting ages through 600
seconds. Existing snapshots survive application restarts. Missing content,
invalid timestamps (including future dates), or dependency read failures fail
the corresponding check. A failed save does not itself invalidate a recent,
readable previous snapshot.

Readiness only inspects state: it never fetches sensor data, refreshes cache,
or uploads objects. Background loops populate state after startup. Listing
snapshot history costs more as the bucket grows; Kubernetes probe wiring and
live readiness verification remain pending.

Run automated tests (external dependencies are mocked in endpoint unit tests):

```powershell
pytest --cov=src --cov-report=xml tests/
pylint src/app.py
```
