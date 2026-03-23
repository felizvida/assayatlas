# Modernization Plan

Reviewed on March 23, 2026.

## Document review summary

The current docs are internally consistent, but they describe a product shell rather than a fully modern application:

- [README.md](../README.md) positions AssayAtlas as a SaaS-style workspace.
- [ARCHITECTURE.md](./ARCHITECTURE.md) correctly admits that the runtime is still a single shared workspace backed by generated manifest content.
- [DEPLOYMENT.md](./DEPLOYMENT.md) documents local and Docker startup, but not persistent application state, migrations, background jobs, or multi-user operations.
- [PUBLICATION_WORKFLOW.md](./PUBLICATION_WORKFLOW.md) is strong on manuscript/export UX, which confirms that publication-grade figure flow should remain the product center of gravity.
- [PRISM_ALTERNATIVE_PLAN.md](../PRISM_ALTERNATIVE_PLAN.md) and [PRISM_DELIGHT_REQUIREMENTS.md](../PRISM_DELIGHT_REQUIREMENTS.md) make the strategic target clear: exceed Prism on figure polish, clarity, and workflow trust, not just on statistics.

## Main modernization gap

The project currently behaves like this:

- tutorial content, workspace content, and exports are generated from one manifest build,
- the workspace is still effectively seeded/shared rather than persisted per project or user,
- the app layer is cleaner than before, but analysis and export behavior still lean heavily on generator-time structures,
- and the test suite still leans too much on broad smoke coverage instead of isolated module contracts.

That means the next step should not be a frontend rewrite or more tutorial cases.

The next step should be:

## Phase 1: Persistent Application Core

Turn AssayAtlas from a generated product shell into a persisted application with a stable domain model, testable analysis modules, and a clean runtime boundary between tutorial seeds and live user work.

## Why this is the right next move

This phase unlocks almost every later modernization goal:

- real projects instead of a shared seeded workspace,
- user-specific drafts and manuscript packets,
- background export/render jobs,
- more isolated feature development,
- and the ability to evolve the UI without rewriting the whole backend every time.

Without this step, new features mostly deepen the shell instead of modernizing the platform.

## Goals

1. Separate tutorial/demo seed content from live workspace data.
2. Add persistent storage for projects, datasets, figures, manuscripts, and export jobs.
3. Define typed runtime models and service boundaries that do not depend on the generated manifest shape.
4. Make analysis and export modules independently testable.
5. Preserve the existing publication-grade export workflow while moving it onto a modern runtime foundation.

## Recommended technical direction

### Keep

- Flask for the next phase, to avoid a framework rewrite before the data model is stable.
- The existing publication/export pipeline as the visual quality baseline.
- `ManifestBuilder` as a bridge for seeding tutorial content and regression fixtures.

### Add

- SQLAlchemy + Alembic for persisted runtime entities and migrations.
- A small API layer inside the Flask app for workspace/project/dataset/export operations.
- Background job execution for figure rendering and manuscript bundle creation.
- Pydantic or dataclass-based schemas for runtime request/response payloads.
- A seed loader that imports tutorial/sample content into the database without making it the runtime source of truth.

### Defer

- Full React or FastAPI rewrite.
- Real-time collaboration.
- Multi-tenant billing/admin systems.
- Advanced plugin architecture.

## Workstreams

### 1. Domain and persistence

Create first-class models for:

- `Project`
- `Dataset`
- `FigureDraft`
- `ManuscriptPacket`
- `ExportJob`
- `TutorialCase`

Deliverables:

- `app/models/`
- `app/repositories/`
- `app/services/`
- database config and migrations
- seed import path from existing generated artifacts

Success condition:

- the workspace can render from persisted records rather than directly from `use_cases.json`

### 2. Tutorial/runtime separation

Keep the twenty tutorial cases, but move them into a seed/content lane instead of treating them as the application data model.

Deliverables:

- tutorial seed importer
- separate tutorial repository/service
- runtime workspace repository/service

Success condition:

- removing or changing tutorial content does not change the live workspace schema

### 3. Analysis and export modularization

Break the current generator logic into isolated modules with typed contracts.

Target module groups:

- analysis inputs and transforms
- chart rendering
- publication/export packaging
- seed generation

Success condition:

- a single analysis or export module can be replaced and tested without regenerating the full corpus

### 4. Test modernization

Replace the current over-reliance on route-level smoke coverage with layered tests:

- unit tests for analysis modules
- unit tests for export packaging
- repository/service tests for persisted entities
- API integration tests for workspace flows
- a small route smoke suite for top-level page rendering

Success condition:

- most refactors are validated by focused tests first, with smoke tests as the final safety net

### 5. UI modernization on stable data contracts

Once the runtime boundary is stable:

- move page data to typed view models,
- introduce a reusable component vocabulary for cards, tables, timelines, and export actions,
- and make the workspace feel like a living application rather than a generated catalog.

Success condition:

- UI work no longer requires manifest-shape edits in multiple layers

## Concrete next sprint

The first sprint should be narrow and architectural:

1. Add database plumbing and migrations.
2. Define persisted models for `Project`, `Dataset`, `FigureDraft`, and `ManuscriptPacket`.
3. Create repository/service layers for those models.
4. Implement a one-time seed importer from the current generated manifest.
5. Switch `/workspace` to read from the persisted workspace service instead of directly from generated manifest content.
6. Add repository/service tests for the new workspace path.

Do not rewrite the figure engine or frontend framework in this sprint.

## Suggested 6-week plan

### Weeks 1-2

- database and migration setup
- persisted models
- seed importer
- repository tests

### Weeks 3-4

- workspace service reads from persisted models
- dataset/project/manuscript detail routes move to the new service
- route smoke tests shrink
- focused service tests expand

### Weeks 5-6

- export jobs become explicit runtime entities
- background job path for bundle generation
- API endpoints for workspace actions
- deployment docs updated for persistent runtime state

## Exit criteria for Phase 1

- live workspace pages no longer depend on tutorial manifest shape
- at least one figure/export flow runs through persisted runtime entities
- analysis/export/service modules have focused tests
- route smoke tests are a minority of the total suite
- deployment docs include migrations and persistent state handling

## What to do after Phase 1

Once the persistent core exists, the best next modernization step is:

- a richer API and job system,
- then a more dynamic frontend,
- then collaboration/auth/versioning features.

That order keeps the product modernizing from the inside out instead of from the paint layer inward.
