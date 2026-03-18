# Architecture

## Product-shell architecture

The current implementation is a production-oriented product shell for a single shared workspace, not yet a full multi-tenant platform.

### Runtime pieces

- `scripts/build_examples.py`
  - Loads real public datasets.
  - Computes the twenty tutorial analyses.
  - Generates workspace entities for projects, figure drafts, manuscripts, datasets, activity, and exports.
  - Generates polished chart assets.
  - Writes `data/generated/use_cases.json`.
  - Writes the markdown training tutorial and use-case catalog.
- `app/__init__.py`
  - Loads the generated manifest.
  - Serves the Flask routes for the workspace, project, figure, dataset, manuscript, tutorial, and docs pages.
  - Exposes dataset and document downloads.
- `app/templates/*`
  - Render the SaaS-style user interface.
- `app/static/generated/charts/*`
  - Hold the generated figure assets used by both the app and docs.

### Data flow

1. Source datasets are stored in `data/raw/`.
2. The generator processes those datasets into charts, summaries, preview tables, and workspace objects.
3. The generator writes a canonical manifest JSON file.
4. The Flask app reads that manifest and renders both the SaaS workspace and the tutorial library from it.
5. Screenshots can then be captured from the real pages and referenced from the training docs.

## Why the generator matters

The generator is the source of truth for:

- workspace project metadata,
- figure draft metadata,
- manuscript packet status,
- dataset library previews,
- tutorial sequence,
- numeric results,
- chart assets,
- documentation content,
- and the app cards themselves.

That keeps the repo aligned. If a use case changes, the app and docs change together after one rebuild.

## Suggested production SaaS evolution

If this prototype grows into a true multi-user service, the next architecture step should be:

- Flask or FastAPI API tier behind Gunicorn.
- Postgres for projects, users, comments, audit history, and exports.
- Object storage for uploaded datasets and rendered export bundles.
- Background jobs for heavier analysis and export tasks.
- Authentication with workspace-level roles.
- Durable version history for project states and figure revisions.

## Product-critical technical priorities

- Keep the graph pipeline vector-first.
- Preserve WYSIWYG export behavior.
- Treat multi-panel composition as a first-class feature.
- Keep analysis specs transparent enough to regenerate outside the GUI.
- Maintain test coverage around the generator so the tutorial numbers stay trustworthy.
