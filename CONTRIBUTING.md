# Contributing

Thank you for helping improve AssayAtlas.

## Workflow

1. Fork the repository and create a branch from `main`.
2. Install dependencies and regenerate assets before making UI or generator changes.
3. Add or update tests for the behavior you change.
4. Keep documentation in sync with product or export changes.
5. Open a pull request with a concise summary, validation notes, and screenshots if the UI changed.

## Local setup

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python scripts/build_examples.py
./.venv/bin/python -m unittest discover -s tests -v
```

## Pull request expectations

- Explain the user-facing behavior change.
- Call out any data-model or manifest-shape changes.
- Mention whether generated assets were refreshed.
- Include exact validation commands you ran.

## Scope guidance

- Keep publication-quality figure output as a first-class constraint.
- Prefer isolated feature seams and focused tests over broad rewrites.
- Do not commit secrets, private datasets, or proprietary screenshots.
