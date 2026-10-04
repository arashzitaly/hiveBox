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
- Scheduled refresh every five minutes is not implemented yet. Expiration
  alone does not fetch new data.

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

Run automated tests (Valkey and openSenseMap are mocked in cache tests):

```powershell
pytest --cov=src --cov-report=xml tests/
pylint src/app.py
```
