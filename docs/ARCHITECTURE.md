# Architecture

## Product-shell architecture

The current implementation is a production-oriented product shell for a single shared workspace, not yet a full multi-tenant platform.

### Runtime pieces

- `scripts/build_examples.py`
  - Defines the twenty workflow specs and the default builder registry.
  - Exposes `ManifestBuilder`, which prepares source datasets, applies tutorial overrides, builds each workflow, and assembles the manifest through injectable collaborators.
  - Writes `data/generated/use_cases.json`.
  - Writes the markdown training tutorial and use-case catalog.
- `app/content.py`
  - Defines the typed manifest snapshot and page-context models.
  - Provides the file-backed repository with mtime-aware reloads for manifests and docs.
  - Centralizes the allowlisted download policy for exported artifacts and tutorial files.
  - Acts as the service boundary between raw generated data and Flask routes.
- `app/runtime.py`
  - Provides the persisted SQLite-backed workspace repository and service.
  - Seeds workspace entities from the generated manifest once, then serves runtime workspace records from the database.
  - Defines the first durable runtime seam between tutorial/generated content and live workspace state.
- `app/__init__.py`
  - Hosts the Flask app factory.
  - Serves the workspace, project, figure, dataset, manuscript, tutorial, and docs pages through the content service.
  - Exposes only allowlisted downloads rather than repo-root file access.
- `app/templates/*`
  - Render the SaaS-style user interface.
- `app/static/generated/charts/*`
  - Hold the generated figure assets used by both the app and docs.

### Data flow

1. Source datasets are stored in `data/raw/`.
2. `ManifestBuilder` prepares the offline-friendly source datasets and dispatches each use case through the registered feature builder.
3. The builder registry returns workflow-specific outputs, which are packaged into publication assets and assembled into a canonical manifest JSON file.
4. The runtime seeds persisted workspace records from the generated manifest when the workspace database is empty.
5. The Flask app reads tutorial/docs content from the file-backed manifest layer and reads workspace, project, dataset, manuscript, and figure pages from the persisted runtime service.
6. Screenshots can then be captured from the real pages and referenced from the training docs.

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

## Current scalability seams

- Feature replacement happens through the manifest builder's injected `builder_registry`, so a workflow can be swapped or added without changing route code.
- Manifest and docs reads are mtime-aware, so regenerated content becomes visible without restarting the process.
- Download access is isolated behind an allowlist, which limits exposure to generated artifacts instead of the whole repository.
- Workspace runtime state now has a persisted repository/service seam, which decouples the workspace path from the generated manifest.
- The test suite now mixes full-stack smoke coverage with focused unit tests for the content layer, runtime workspace repository, and manifest-builder seams.

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
- Maintain both seam-level tests and end-to-end generator coverage so feature swaps stay safe and the tutorial numbers remain trustworthy.
