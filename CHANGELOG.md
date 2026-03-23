# Changelog

All notable changes to AssayAtlas will be documented in this file.

## v0.1.1 (release candidate)

Prepared on March 23, 2026.

### Added

- Persisted workspace runtime APIs for workspace reads, project updates, export jobs, and workspace events.
- Persisted runtime APIs for figure-draft and manuscript-packet updates.
- Schema-versioned runtime migrations for the SQLite workspace database.
- Typed runtime record models for persisted workspace entities.
- A lightweight workspace event log to make runtime changes more inspectable.
- Inline editing panels on project, dataset, figure, and manuscript detail pages, backed by the persisted runtime API.
- An actionable workspace export queue manager that can create and update export jobs in place.
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
