# Deployment

## Local run

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python scripts/build_examples.py
./.venv/bin/python run.py
```

The app listens on `127.0.0.1:5000`.

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
{"ok": true, "manifest": true}
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

## Roll-forward notes

- Keep `data/raw/` under version control so CI and local builds stay deterministic.
- Rebuild generated assets after any use-case or visual-style change.
- Capture fresh screenshots after UI changes so the tutorial remains truthful.
