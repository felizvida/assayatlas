# Deployment

## Local run

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python scripts/build_examples.py
./.venv/bin/python run.py
```

The app listens on `127.0.0.1:5000`.

## Runtime state

The app now maintains a persisted workspace database at `data/assayatlas.db`.

- `data/generated/use_cases.json` remains the seed source for tutorial and initial workspace content.
- `data/assayatlas.db` is created automatically and seeded on first access to workspace records.
- The runtime applies schema migrations automatically on startup.
- The runtime persists figure and manuscript edits through the same SQLite application core used for projects and export jobs.
- Delete the database only if you intentionally want to reseed the workspace from the generated manifest.

## Docker build

```bash
docker build -t assayatlas .
docker run --rm -p 5000:5000 assayatlas
```

## Health check

Use the health endpoint after startup:

```bash
curl http://127.0.0.1:5000/healthz
```

Expected response:

```json
{"ok": true, "manifest": true, "workspace_db": true, "workspace_schema_version": 2}
```

## Runtime API surface

The persisted workspace currently exposes:

- `GET /api/workspace`
- `GET|PATCH /api/projects/<slug>`
- `GET|PATCH /api/figures/<slug>`
- `GET|PATCH /api/manuscripts/<slug>`
- `GET|POST /api/export-jobs`
- `PATCH /api/export-jobs/<job_key>`
- `GET /api/workspace-events`

## Release pull workflow

For a pull-based deployment from GitHub:

```bash
cd /srv/assayatlas
git fetch --tags origin
git checkout main
git pull --ff-only origin main
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python scripts/build_examples.py
./.venv/bin/python -m unittest tests.test_app -v
./.venv/bin/python run.py
```

If you deploy by tag instead of by branch head:

```bash
cd /srv/assayatlas
git fetch --tags origin
git checkout v0.1.1
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python scripts/build_examples.py
./.venv/bin/python run.py
```

## Regenerating tutorial content

Any time you change the analysis generator, rerun:

```bash
./.venv/bin/python scripts/build_examples.py
```

This rebuilds:

- chart assets,
- the manifest JSON,
- the real-data tutorial,
- and the use-case catalog.

If you want the persisted workspace to reseed from the regenerated manifest:

```bash
rm -f data/assayatlas.db
./.venv/bin/python run.py
```

## Roll-forward notes

- Keep `data/raw/` under version control so CI and local builds stay deterministic.
- Rebuild generated assets after any use-case or visual-style change.
- Keep `data/assayatlas.db` out of version control; it is runtime state, not a source artifact.
- Capture fresh screenshots after UI changes so the tutorial remains truthful.

## Rollback

To return to the current public baseline:

```bash
cd /srv/assayatlas
git fetch --tags origin
git checkout v0.1.0
./.venv/bin/python scripts/build_examples.py
./.venv/bin/python run.py
```
