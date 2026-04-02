# Changelog

All notable changes to AssayAtlas will be documented in this file.

## v0.1.2

Released on April 2, 2026.

### Added

- A dedicated runtime validation layer in `app/runtime_validation.py`, with focused unit coverage for validator behavior.

### Changed

- Flask write endpoints now share the same allowed-field definitions as the persisted runtime layer.
- Runtime write normalization for projects, datasets, figures, manuscripts, and export jobs now flows through a single validation seam instead of being duplicated inside the repository implementation.

### Fixed

- Export job creation and update now reject blank `title`, `detail`, and `path` payloads server-side.
- Project, dataset, figure, and manuscript write paths now reject whitespace-only values for required editable text fields instead of persisting degraded records.
- SQLite test connections are now closed explicitly, which removes the noisy resource warnings seen during API-focused test runs.

## v0.1.1

Released on March 23, 2026.

### Added

- Persisted workspace runtime APIs for workspace reads, project updates, export jobs, and workspace events.
- Persisted runtime APIs for figure-draft and manuscript-packet updates.
- Schema-versioned runtime migrations for the SQLite workspace database.
- Typed runtime record models for persisted workspace entities.
- A lightweight workspace event log to make runtime changes more inspectable.
- Inline editing panels on project, dataset, figure, and manuscript detail pages, backed by the persisted runtime API.
- An actionable workspace export queue manager that can create and update export jobs in place.
- A workspace project-creation flow backed by the persisted runtime API, so new study shells can be created without touching the tutorial manifest.
- Focused runtime and API tests so feature-level refactors no longer depend only on full-page smoke coverage.

### Changed

- Workspace, project, dataset, manuscript, and figure pages now read through the persisted runtime/service seam instead of leaning directly on the generated manifest.
- Deployment guidance now documents runtime state, health reporting, release pull commands, and rollback flow.
- Repository docs now include dedicated release notes for the next patch release.

### Fixed

- Standard browser requests to `/favicon.ico` now resolve successfully instead of producing a visible 404 during page load.

## v0.1.0

Released previously.

### Added

- The first public AssayAtlas release, including the publication-first SaaS shell, tutorial library, persisted content layer hardening, and architecture/test-seam improvements.
