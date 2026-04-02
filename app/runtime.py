from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.runtime_models import (
    ActivityItemRecord,
    DatasetRecord,
    ExportJobRecord,
    FigureDraftRecord,
    ManuscriptPacketRecord,
    ProjectRecord,
    RuntimePayloadModel,
    WorkspaceEventRecord,
)

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_DB_PATH = ROOT / "data" / "assayatlas.db"
SCHEMA_VERSION = 2


@dataclass(frozen=True)
class EntitySpec:
    table: str
    key_column: str
    key_field: str
    model_cls: type[RuntimePayloadModel]
    fallback_key_fields: tuple[str, ...] = ()


PROJECT_SPEC = EntitySpec("projects", "slug", "slug", ProjectRecord)
DATASET_SPEC = EntitySpec("datasets", "slug", "slug", DatasetRecord)
FIGURE_SPEC = EntitySpec("figure_drafts", "slug", "slug", FigureDraftRecord)
MANUSCRIPT_SPEC = EntitySpec("manuscripts", "slug", "slug", ManuscriptPacketRecord)
EXPORT_JOB_SPEC = EntitySpec(
    "export_jobs",
    "job_key",
    "job_key",
    ExportJobRecord,
    fallback_key_fields=("title", "path"),
)
ACTIVITY_FEED_SPEC = EntitySpec(
    "activity_feed",
    "feed_key",
    "feed_key",
    ActivityItemRecord,
    fallback_key_fields=("title", "path"),
)
REQUIRED_WORKSPACE_META_KEYS = ("quick_actions", "pinned_tasks", "tutorial_library")
REQUIRED_SEEDED_TABLES = (
    PROJECT_SPEC.table,
    DATASET_SPEC.table,
    FIGURE_SPEC.table,
    MANUSCRIPT_SPEC.table,
)
SEED_STATE_META_KEY = "seed_state"


class PersistedWorkspaceRepository:
    def __init__(self, db_path: Path = WORKSPACE_DB_PATH) -> None:
        self.db_path = db_path

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection:
            self._apply_migrations(connection)

    def ensure_seeded(self, workspace: dict[str, Any]) -> None:
        self.initialize()
        with closing(self._connect()) as connection:
            if self._workspace_seed_is_complete(connection):
                if not self._load_meta(connection, SEED_STATE_META_KEY, None):
                    self._store_seed_state(connection, status="complete", source="legacy-detected")
                    connection.commit()
                return
            if self._workspace_has_any_data(connection):
                self._seed_workspace(connection, workspace, source="partial-recovery")
                return
            self._seed_workspace(connection, workspace)

    def workspace_snapshot(self) -> dict[str, Any]:
        self.initialize()
        with closing(self._connect()) as connection:
            projects = self._list_records(connection, PROJECT_SPEC)
            figure_drafts = self._list_records(connection, FIGURE_SPEC)
            manuscripts = self._list_records(connection, MANUSCRIPT_SPEC)
            datasets = self._list_records(connection, DATASET_SPEC)
            export_queue = self._list_records(connection, EXPORT_JOB_SPEC)
            activity_feed = self._list_records(connection, ACTIVITY_FEED_SPEC)
            quick_actions = self._load_meta(connection, "quick_actions", [])
            pinned_tasks = self._load_meta(connection, "pinned_tasks", [])
            tutorial_library = self._load_meta(
                connection,
                "tutorial_library",
                {"count": 0, "summary": "", "path": "/tutorial"},
            )
            workspace_events = self._list_event_records(connection, limit=20)

        metrics = [
            {"value": str(len(projects)), "label": "active projects"},
            {"value": str(len(figure_drafts)), "label": "figure drafts"},
            {"value": str(len(manuscripts)), "label": "manuscript packets"},
            {"value": str(len(datasets)), "label": "shared datasets"},
        ]

        return {
            "metrics": metrics,
            "quick_actions": quick_actions,
            "pinned_tasks": pinned_tasks,
            "projects": self._serialize_records(projects),
            "manuscripts": self._serialize_records(manuscripts),
            "figure_drafts": self._serialize_records(figure_drafts),
            "datasets": self._serialize_records(datasets),
            "export_queue": self._serialize_records(export_queue),
            "activity_feed": self._serialize_records(activity_feed),
            "tutorial_library": tutorial_library,
            "workspace_events": self._serialize_records(workspace_events),
        }

    def schema_version(self) -> int:
        self.initialize()
        with closing(self._connect()) as connection:
            return self._current_schema_version(connection)

    def get_project(self, slug: str) -> dict[str, Any] | None:
        record = self._get_record(PROJECT_SPEC, slug)
        return record.to_payload() if record else None

    def get_dataset(self, slug: str) -> dict[str, Any] | None:
        record = self._get_record(DATASET_SPEC, slug)
        return record.to_payload() if record else None

    def get_figure(self, slug: str) -> dict[str, Any] | None:
        record = self._get_record(FIGURE_SPEC, slug)
        return record.to_payload() if record else None

    def get_manuscript(self, slug: str) -> dict[str, Any] | None:
        record = self._get_record(MANUSCRIPT_SPEC, slug)
        return record.to_payload() if record else None

    def list_export_jobs(self) -> list[dict[str, Any]]:
        self.initialize()
        with closing(self._connect()) as connection:
            return self._serialize_records(self._list_records(connection, EXPORT_JOB_SPEC))

    def list_workspace_events(self, limit: int = 20) -> list[dict[str, Any]]:
        self.initialize()
        with closing(self._connect()) as connection:
            return self._serialize_records(self._list_event_records(connection, limit))

    def update_project(self, slug: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        allowed_fields = {
            "name",
            "status",
            "tone",
            "summary",
            "next_review",
            "due_date",
            "completion",
            "owner",
            "target_journal",
            "export_preset",
            "tasks",
            "milestones",
            "team",
        }
        sanitized_changes = {key: value for key, value in changes.items() if key in allowed_fields}
        if not sanitized_changes:
            return self.get_project(slug)
        normalized_changes = self._normalize_required_string_fields(
            sanitized_changes,
            {
                "name": "Project name",
                "status": "Project status",
                "tone": "Project tone",
                "summary": "Project summary",
                "next_review": "Project next_review",
                "due_date": "Project due_date",
                "owner": "Project owner",
                "target_journal": "Project target_journal",
                "export_preset": "Project export_preset",
            },
        )
        normalized_changes = self._normalize_project_structured_fields(normalized_changes)

        self.initialize()
        with closing(self._connect()) as connection:
            record = self._update_record(connection, PROJECT_SPEC, slug, normalized_changes)
            if not isinstance(record, ProjectRecord):
                return None
            event_time = self._timestamp()
            self._append_activity_item(
                connection,
                ActivityItemRecord(
                    title=f"{record.name} updated",
                    meta=event_time,
                    path=f"/projects/{slug}",
                    kind="Project",
                ),
            )
            self._append_workspace_event(
                connection,
                WorkspaceEventRecord(
                    event_type="project.updated",
                    subject_key=slug,
                    created_at=event_time,
                    payload={"changes": normalized_changes, "project_name": record.name},
                ),
            )
            connection.commit()
            return record.to_payload()

    def create_project(self, payload: dict[str, Any]) -> dict[str, Any]:
        allowed_fields = {
            "slug",
            "name",
            "status",
            "tone",
            "summary",
            "hero_chart_path",
            "completion",
            "figure_count",
            "dataset_count",
            "next_review",
            "team",
            "due_date",
            "target_journal",
            "owner",
            "export_preset",
            "tasks",
            "milestones",
            "figures",
            "datasets",
            "manuscript_slug",
            "primary_figure_slug",
        }
        sanitized_payload = {key: value for key, value in payload.items() if key in allowed_fields}
        normalized_payload = dict(sanitized_payload)
        normalized_payload["name"] = self._require_non_empty_string(
            normalized_payload.get("name"),
            field_label="Project name",
        )
        for field in (
            "slug",
            "status",
            "tone",
            "summary",
            "hero_chart_path",
            "next_review",
            "due_date",
            "target_journal",
            "owner",
            "export_preset",
        ):
            if field in normalized_payload:
                normalized_value = self._normalize_optional_string(
                    normalized_payload[field],
                    field_label=f"Project {field}",
                )
                if normalized_value is None:
                    normalized_payload.pop(field)
                else:
                    normalized_payload[field] = normalized_value
        normalized_payload = self._normalize_project_structured_fields(normalized_payload)

        self.initialize()
        with closing(self._connect()) as connection:
            sort_order = self._next_sort_order(connection, PROJECT_SPEC.table)
            base_slug = normalized_payload.get("slug") or self._slugify(normalized_payload["name"])
            project_slug = self._ensure_unique_key(connection, PROJECT_SPEC, base_slug)
            project_payload = {
                "slug": project_slug,
                "name": normalized_payload["name"],
                "status": normalized_payload.get("status", "Draft setup"),
                "tone": normalized_payload.get("tone", "progress"),
                "summary": normalized_payload.get("summary", "New project workspace ready for figures, datasets, and manuscript planning."),
                "hero_chart_path": normalized_payload.get("hero_chart_path", "generated/charts/20-publication-figure-board.png"),
                "completion": normalized_payload.get("completion", 0),
                "figure_count": normalized_payload.get("figure_count", 0),
                "dataset_count": normalized_payload.get("dataset_count", 0),
                "next_review": normalized_payload.get("next_review", "Not scheduled"),
                "team": normalized_payload.get("team", []),
                "due_date": normalized_payload.get("due_date", "TBD"),
                "target_journal": normalized_payload.get("target_journal", "Unassigned"),
                "owner": normalized_payload.get("owner", "Unassigned"),
                "export_preset": normalized_payload.get("export_preset", "General submission"),
                "tasks": normalized_payload.get("tasks", ["Define the first figure draft"]),
                "milestones": normalized_payload.get("milestones", [{"label": "Project shell created", "state": "complete"}]),
                "figures": normalized_payload.get("figures", []),
                "datasets": normalized_payload.get("datasets", []),
                "manuscript_slug": normalized_payload.get("manuscript_slug"),
                "primary_figure_slug": normalized_payload.get("primary_figure_slug"),
            }
            record = ProjectRecord.from_payload(project_payload)
            connection.execute(
                "INSERT INTO projects(slug, sort_order, payload_json) VALUES (?, ?, ?)",
                (record.slug, sort_order, json.dumps(record.to_payload())),
            )
            event_time = self._timestamp()
            self._append_activity_item(
                connection,
                ActivityItemRecord(
                    title=f"{record.name} created",
                    meta=event_time,
                    path=f"/projects/{record.slug}",
                    kind="Project",
                ),
            )
            self._append_workspace_event(
                connection,
                WorkspaceEventRecord(
                    event_type="project.created",
                    subject_key=record.slug,
                    created_at=event_time,
                    payload=record.to_payload(),
                ),
            )
            connection.commit()
            return record.to_payload()

    def update_dataset(self, slug: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        allowed_fields = {
            "name",
            "kind",
            "source",
            "description",
            "updated_at",
        }
        sanitized_changes = {key: value for key, value in changes.items() if key in allowed_fields}
        if not sanitized_changes:
            return self.get_dataset(slug)
        normalized_changes = self._normalize_required_string_fields(
            sanitized_changes,
            {
                "name": "Dataset name",
                "kind": "Dataset kind",
                "source": "Dataset source",
                "description": "Dataset description",
                "updated_at": "Dataset updated_at",
            },
        )

        self.initialize()
        with closing(self._connect()) as connection:
            record = self._update_record(connection, DATASET_SPEC, slug, normalized_changes)
            if not isinstance(record, DatasetRecord):
                return None
            event_time = self._timestamp()
            self._append_activity_item(
                connection,
                ActivityItemRecord(
                    title=f"{record.name} updated",
                    meta=event_time,
                    path=f"/datasets/{slug}",
                    kind="Dataset",
                ),
            )
            self._append_workspace_event(
                connection,
                WorkspaceEventRecord(
                    event_type="dataset.updated",
                    subject_key=slug,
                    created_at=event_time,
                    payload={"changes": normalized_changes, "dataset_name": record.name},
                ),
            )
            connection.commit()
            return record.to_payload()

    def update_figure(self, slug: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        allowed_fields = {
            "title",
            "status",
            "tone",
            "version",
            "summary",
            "what_to_notice",
            "key_metrics",
            "caption_text",
            "methods_text",
            "results_text",
            "next_action",
            "owner",
        }
        sanitized_changes = {key: value for key, value in changes.items() if key in allowed_fields}
        if not sanitized_changes:
            return self.get_figure(slug)
        normalized_changes = self._normalize_required_string_fields(
            sanitized_changes,
            {
                "title": "Figure title",
                "status": "Figure status",
                "tone": "Figure tone",
                "version": "Figure version",
                "summary": "Figure summary",
                "what_to_notice": "Figure what_to_notice",
                "caption_text": "Figure caption_text",
                "methods_text": "Figure methods_text",
                "results_text": "Figure results_text",
                "next_action": "Figure next_action",
                "owner": "Figure owner",
            },
        )
        normalized_changes = self._normalize_figure_structured_fields(normalized_changes)

        self.initialize()
        with closing(self._connect()) as connection:
            record = self._update_record(connection, FIGURE_SPEC, slug, normalized_changes)
            if not isinstance(record, FigureDraftRecord):
                return None
            event_time = self._timestamp()
            self._append_activity_item(
                connection,
                ActivityItemRecord(
                    title=f"{record.title} updated",
                    meta=event_time,
                    path=f"/figures/{slug}",
                    kind="Figure",
                ),
            )
            self._append_workspace_event(
                connection,
                WorkspaceEventRecord(
                    event_type="figure.updated",
                    subject_key=slug,
                    created_at=event_time,
                    payload={"changes": normalized_changes, "figure_title": record.title},
                ),
            )
            connection.commit()
            return record.to_payload()

    def update_manuscript(self, slug: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        allowed_fields = {
            "title",
            "status",
            "tone",
            "narrative",
            "submission_preset",
            "target_journal",
            "due_date",
            "sections",
            "deliverables",
            "figure_progress",
        }
        sanitized_changes = {key: value for key, value in changes.items() if key in allowed_fields}
        if not sanitized_changes:
            return self.get_manuscript(slug)
        normalized_changes = self._normalize_required_string_fields(
            sanitized_changes,
            {
                "title": "Manuscript title",
                "status": "Manuscript status",
                "tone": "Manuscript tone",
                "narrative": "Manuscript narrative",
                "submission_preset": "Manuscript submission_preset",
                "target_journal": "Manuscript target_journal",
                "due_date": "Manuscript due_date",
                "figure_progress": "Manuscript figure_progress",
            },
        )
        normalized_changes = self._normalize_manuscript_structured_fields(normalized_changes)

        self.initialize()
        with closing(self._connect()) as connection:
            record = self._update_record(connection, MANUSCRIPT_SPEC, slug, normalized_changes)
            if not isinstance(record, ManuscriptPacketRecord):
                return None
            event_time = self._timestamp()
            self._append_activity_item(
                connection,
                ActivityItemRecord(
                    title=f"{record.title} updated",
                    meta=event_time,
                    path=f"/manuscripts/{slug}",
                    kind="Manuscript",
                ),
            )
            self._append_workspace_event(
                connection,
                WorkspaceEventRecord(
                    event_type="manuscript.updated",
                    subject_key=slug,
                    created_at=event_time,
                    payload={"changes": normalized_changes, "manuscript_title": record.title},
                ),
            )
            connection.commit()
            return record.to_payload()

    def create_export_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        required = {"title", "detail", "path"}
        missing = sorted(required - payload.keys())
        if missing:
            raise ValueError(f"Missing required export job fields: {', '.join(missing)}")

        normalized_payload = dict(payload)
        for field in ("title", "detail", "path", "status", "tone", "job_key"):
            if field in normalized_payload:
                normalized_payload[field] = self._require_non_empty_string(
                    normalized_payload[field],
                    field_label=f"Export job {field}",
                )

        self.initialize()
        with closing(self._connect()) as connection:
            sort_order = self._next_sort_order(connection, EXPORT_JOB_SPEC.table)
            job_key = normalized_payload.get("job_key") or f"export-{sort_order}-{self._slugify(normalized_payload['title'])}"
            job = ExportJobRecord.from_payload({**normalized_payload, "job_key": job_key})
            connection.execute(
                "INSERT INTO export_jobs(job_key, sort_order, payload_json) VALUES (?, ?, ?)",
                (job.job_key, sort_order, json.dumps(job.to_payload())),
            )
            event_time = self._timestamp()
            self._append_activity_item(
                connection,
                ActivityItemRecord(
                    title=f"{job.title} queued",
                    meta=event_time,
                    path=job.path,
                    kind="Export",
                ),
            )
            self._append_workspace_event(
                connection,
                WorkspaceEventRecord(
                    event_type="export_job.created",
                    subject_key=job.job_key,
                    created_at=event_time,
                    payload=job.to_payload(),
                ),
            )
            connection.commit()
            return job.to_payload()

    def update_export_job(self, job_key: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        allowed_fields = {"title", "status", "tone", "detail", "path"}
        sanitized_changes = {key: value for key, value in changes.items() if key in allowed_fields}
        if not sanitized_changes:
            jobs = {job["job_key"]: job for job in self.list_export_jobs() if job.get("job_key")}
            return jobs.get(job_key)
        normalized_changes = {
            key: self._require_non_empty_string(value, field_label=f"Export job {key}")
            for key, value in sanitized_changes.items()
        }

        self.initialize()
        with closing(self._connect()) as connection:
            record = self._update_record(connection, EXPORT_JOB_SPEC, job_key, normalized_changes)
            if not isinstance(record, ExportJobRecord):
                return None
            event_time = self._timestamp()
            self._append_activity_item(
                connection,
                ActivityItemRecord(
                    title=f"{record.title} marked {record.status}",
                    meta=event_time,
                    path=record.path,
                    kind="Export",
                ),
            )
            self._append_workspace_event(
                connection,
                WorkspaceEventRecord(
                    event_type="export_job.updated",
                    subject_key=job_key,
                    created_at=event_time,
                    payload={"changes": normalized_changes, "job": record.to_payload()},
                ),
            )
            connection.commit()
            return record.to_payload()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _apply_migrations(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        current_version = self._current_schema_version(connection)
        for version in range(current_version + 1, SCHEMA_VERSION + 1):
            migration = getattr(self, f"_migrate_to_v{version}")
            migration(connection)
            connection.execute(
                "INSERT OR REPLACE INTO schema_meta(key, value) VALUES (?, ?)",
                ("schema_version", str(version)),
            )
        connection.commit()

    def _current_schema_version(self, connection: sqlite3.Connection) -> int:
        row = connection.execute(
            "SELECT value FROM schema_meta WHERE key = ?",
            ("schema_version",),
        ).fetchone()
        return int(row["value"]) if row else 0

    def _migrate_to_v1(self, connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS workspace_meta (
                key TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS projects (
                slug TEXT PRIMARY KEY,
                sort_order INTEGER NOT NULL,
                payload_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS datasets (
                slug TEXT PRIMARY KEY,
                sort_order INTEGER NOT NULL,
                payload_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS figure_drafts (
                slug TEXT PRIMARY KEY,
                sort_order INTEGER NOT NULL,
                payload_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS manuscripts (
                slug TEXT PRIMARY KEY,
                sort_order INTEGER NOT NULL,
                payload_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS export_jobs (
                job_key TEXT PRIMARY KEY,
                sort_order INTEGER NOT NULL,
                payload_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS activity_feed (
                feed_key TEXT PRIMARY KEY,
                sort_order INTEGER NOT NULL,
                payload_json TEXT NOT NULL
            );
            """
        )

    def _migrate_to_v2(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS workspace_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                subject_key TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

    def _seed_workspace(self, connection: sqlite3.Connection, workspace: dict[str, Any], source: str = "manifest") -> None:
        connection.execute("DELETE FROM workspace_meta")
        for table in (
            PROJECT_SPEC.table,
            DATASET_SPEC.table,
            FIGURE_SPEC.table,
            MANUSCRIPT_SPEC.table,
            EXPORT_JOB_SPEC.table,
            ACTIVITY_FEED_SPEC.table,
            "workspace_events",
        ):
            connection.execute(f"DELETE FROM {table}")

        self._store_meta(connection, "quick_actions", workspace.get("quick_actions", []))
        self._store_meta(connection, "pinned_tasks", workspace.get("pinned_tasks", []))
        self._store_meta(connection, "tutorial_library", workspace.get("tutorial_library", {}))

        self._insert_records(connection, PROJECT_SPEC, workspace.get("projects", []))
        self._insert_records(connection, DATASET_SPEC, workspace.get("datasets", []))
        self._insert_records(connection, FIGURE_SPEC, workspace.get("figure_drafts", []))
        self._insert_records(connection, MANUSCRIPT_SPEC, workspace.get("manuscripts", []))
        self._insert_records(connection, EXPORT_JOB_SPEC, workspace.get("export_queue", []))
        self._insert_records(connection, ACTIVITY_FEED_SPEC, workspace.get("activity_feed", []))
        self._store_seed_state(connection, status="complete", source=source)
        connection.commit()

    def _insert_records(
        self,
        connection: sqlite3.Connection,
        spec: EntitySpec,
        rows: list[dict[str, Any]],
    ) -> None:
        for index, item in enumerate(rows):
            record = spec.model_cls.from_payload(item)
            payload = record.to_payload()
            key = self._resolve_record_key(spec, payload, index)
            if spec.key_field and not payload.get(spec.key_field):
                payload[spec.key_field] = key
                record = spec.model_cls.from_payload(payload)
                payload = record.to_payload()
            connection.execute(
                f"INSERT INTO {spec.table}({spec.key_column}, sort_order, payload_json) VALUES (?, ?, ?)",
                (key, index, json.dumps(payload)),
            )

    def _resolve_record_key(self, spec: EntitySpec, payload: dict[str, Any], index: int) -> str:
        candidate = payload.get(spec.key_field)
        if candidate:
            return str(candidate)
        for fallback_field in spec.fallback_key_fields:
            fallback_value = payload.get(fallback_field)
            if fallback_value:
                return f"{spec.table}-{index}-{self._slugify(str(fallback_value))}"
        return f"{spec.table}-{index}"

    def _store_meta(self, connection: sqlite3.Connection, key: str, payload: object) -> None:
        connection.execute(
            "INSERT OR REPLACE INTO workspace_meta(key, payload_json) VALUES (?, ?)",
            (key, json.dumps(payload)),
        )

    def _load_meta(self, connection: sqlite3.Connection, key: str, default: object) -> Any:
        row = connection.execute(
            "SELECT payload_json FROM workspace_meta WHERE key = ?",
            (key,),
        ).fetchone()
        if not row:
            return default
        return json.loads(row["payload_json"])

    def _workspace_seed_is_complete(self, connection: sqlite3.Connection) -> bool:
        for key in REQUIRED_WORKSPACE_META_KEYS:
            if connection.execute(
                "SELECT 1 FROM workspace_meta WHERE key = ?",
                (key,),
            ).fetchone() is None:
                return False
        for table in REQUIRED_SEEDED_TABLES:
            row = connection.execute(
                f"SELECT COUNT(*) AS row_count FROM {table}"
            ).fetchone()
            if row is None or int(row["row_count"]) == 0:
                return False
        return True

    def _workspace_has_any_data(self, connection: sqlite3.Connection) -> bool:
        for table in (
            PROJECT_SPEC.table,
            DATASET_SPEC.table,
            FIGURE_SPEC.table,
            MANUSCRIPT_SPEC.table,
            EXPORT_JOB_SPEC.table,
            ACTIVITY_FEED_SPEC.table,
            "workspace_events",
        ):
            row = connection.execute(
                f"SELECT COUNT(*) AS row_count FROM {table}"
            ).fetchone()
            if row is not None and int(row["row_count"]) > 0:
                return True
        row = connection.execute(
            "SELECT COUNT(*) AS row_count FROM workspace_meta"
        ).fetchone()
        return row is not None and int(row["row_count"]) > 0

    def _store_seed_state(self, connection: sqlite3.Connection, status: str, source: str) -> None:
        self._store_meta(
            connection,
            SEED_STATE_META_KEY,
            {
                "status": status,
                "source": source,
                "seeded_at": self._timestamp(),
            },
        )

    def _list_records(self, connection: sqlite3.Connection, spec: EntitySpec) -> list[RuntimePayloadModel]:
        rows = connection.execute(
            f"SELECT payload_json FROM {spec.table} ORDER BY sort_order ASC"
        ).fetchall()
        return [spec.model_cls.from_payload(json.loads(row["payload_json"])) for row in rows]

    def _list_event_records(self, connection: sqlite3.Connection, limit: int) -> list[WorkspaceEventRecord]:
        rows = connection.execute(
            """
            SELECT event_type, subject_key, payload_json, created_at
            FROM workspace_events
            ORDER BY event_id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [
            WorkspaceEventRecord(
                event_type=row["event_type"],
                subject_key=row["subject_key"],
                created_at=row["created_at"],
                payload=json.loads(row["payload_json"]),
            )
            for row in rows
        ]

    def _serialize_records(self, records: list[RuntimePayloadModel]) -> list[dict[str, Any]]:
        return [record.to_payload() for record in records]

    def _get_record(self, spec: EntitySpec, key: str) -> RuntimePayloadModel | None:
        self.initialize()
        with closing(self._connect()) as connection:
            row = connection.execute(
                f"SELECT payload_json FROM {spec.table} WHERE {spec.key_column} = ?",
                (key,),
            ).fetchone()
        if not row:
            return None
        return spec.model_cls.from_payload(json.loads(row["payload_json"]))

    def _update_record(
        self,
        connection: sqlite3.Connection,
        spec: EntitySpec,
        key: str,
        changes: dict[str, Any],
    ) -> RuntimePayloadModel | None:
        row = connection.execute(
            f"SELECT payload_json FROM {spec.table} WHERE {spec.key_column} = ?",
            (key,),
        ).fetchone()
        if not row:
            return None
        record = spec.model_cls.from_payload(json.loads(row["payload_json"]))
        updated_record = record.merged(changes)
        connection.execute(
            f"UPDATE {spec.table} SET payload_json = ? WHERE {spec.key_column} = ?",
            (json.dumps(updated_record.to_payload()), key),
        )
        return updated_record

    def _next_sort_order(self, connection: sqlite3.Connection, table: str) -> int:
        row = connection.execute(f"SELECT COALESCE(MAX(sort_order), -1) AS max_sort_order FROM {table}").fetchone()
        return int(row["max_sort_order"]) + 1

    def _ensure_unique_key(self, connection: sqlite3.Connection, spec: EntitySpec, key: str) -> str:
        candidate = key
        suffix = 1
        while connection.execute(
            f"SELECT 1 FROM {spec.table} WHERE {spec.key_column} = ?",
            (candidate,),
        ).fetchone():
            suffix += 1
            candidate = f"{key}-{suffix}"
        return candidate

    def _append_activity_item(self, connection: sqlite3.Connection, item: ActivityItemRecord) -> None:
        sort_order = self._next_sort_order(connection, ACTIVITY_FEED_SPEC.table)
        feed_key = item.feed_key or f"activity-{sort_order}-{self._slugify(item.title)}"
        record = item.merged({"feed_key": feed_key})
        connection.execute(
            "INSERT INTO activity_feed(feed_key, sort_order, payload_json) VALUES (?, ?, ?)",
            (feed_key, sort_order, json.dumps(record.to_payload())),
        )

    def _append_workspace_event(self, connection: sqlite3.Connection, event: WorkspaceEventRecord) -> None:
        connection.execute(
            """
            INSERT INTO workspace_events(event_type, subject_key, payload_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (event.event_type, event.subject_key, json.dumps(event.payload), event.created_at),
        )

    def _slugify(self, value: str) -> str:
        return "-".join("".join(char.lower() if char.isalnum() else " " for char in value).split()) or "item"

    def _require_non_empty_string(self, value: Any, field_label: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_label} must be a non-empty string")
        return value.strip()

    def _normalize_optional_string(self, value: Any, field_label: str) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError(f"{field_label} must be a string")
        stripped = value.strip()
        return stripped or None

    def _normalize_required_string_fields(
        self,
        payload: dict[str, Any],
        field_labels: dict[str, str],
    ) -> dict[str, Any]:
        normalized_payload = dict(payload)
        for field, field_label in field_labels.items():
            if field in normalized_payload:
                normalized_payload[field] = self._require_non_empty_string(
                    normalized_payload[field],
                    field_label=field_label,
                )
        return normalized_payload

    def _normalize_project_structured_fields(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized_payload = dict(payload)
        if "tasks" in normalized_payload:
            normalized_payload["tasks"] = self._normalize_string_list(
                normalized_payload["tasks"],
                field_label="Project tasks",
            )
        if "milestones" in normalized_payload:
            normalized_payload["milestones"] = self._normalize_labeled_state_list(
                normalized_payload["milestones"],
                field_label="Project milestones",
            )
        if "team" in normalized_payload:
            normalized_payload["team"] = self._normalize_team_list(
                normalized_payload["team"],
                field_label="Project team",
            )
        return normalized_payload

    def _normalize_figure_structured_fields(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized_payload = dict(payload)
        if "key_metrics" in normalized_payload:
            normalized_payload["key_metrics"] = self._normalize_string_list(
                normalized_payload["key_metrics"],
                field_label="Figure key_metrics",
            )
        return normalized_payload

    def _normalize_manuscript_structured_fields(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized_payload = dict(payload)
        if "sections" in normalized_payload:
            normalized_payload["sections"] = self._normalize_labeled_state_list(
                normalized_payload["sections"],
                field_label="Manuscript sections",
            )
        if "deliverables" in normalized_payload:
            normalized_payload["deliverables"] = self._normalize_labeled_state_list(
                normalized_payload["deliverables"],
                field_label="Manuscript deliverables",
            )
        return normalized_payload

    def _normalize_string_list(self, value: Any, field_label: str) -> list[str]:
        if not isinstance(value, list):
            raise ValueError(f"{field_label} must be a list of non-empty strings")
        return [self._require_non_empty_string(item, field_label=f"{field_label} item") for item in value]

    def _normalize_labeled_state_list(self, value: Any, field_label: str) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            raise ValueError(f"{field_label} must be a list of objects")
        normalized_items: list[dict[str, Any]] = []
        for item in value:
            if not isinstance(item, dict):
                raise ValueError(f"{field_label} must be a list of objects")
            normalized_item = dict(item)
            normalized_item["label"] = self._require_non_empty_string(
                item.get("label"),
                field_label=f"{field_label} label",
            )
            normalized_item["state"] = self._require_non_empty_string(
                item.get("state"),
                field_label=f"{field_label} state",
            )
            normalized_items.append(normalized_item)
        return normalized_items

    def _normalize_team_list(self, value: Any, field_label: str) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            raise ValueError(f"{field_label} must be a list of objects")
        normalized_items: list[dict[str, Any]] = []
        for item in value:
            if not isinstance(item, dict):
                raise ValueError(f"{field_label} must be a list of objects")
            normalized_item = dict(item)
            normalized_item["name"] = self._require_non_empty_string(
                item.get("name"),
                field_label=f"{field_label} name",
            )
            normalized_item["role"] = self._require_non_empty_string(
                item.get("role"),
                field_label=f"{field_label} role",
            )
            normalized_item["initials"] = self._require_non_empty_string(
                item.get("initials"),
                field_label=f"{field_label} initials",
            )
            normalized_items.append(normalized_item)
        return normalized_items

    def _timestamp(self) -> str:
        return datetime.now(UTC).isoformat(timespec="seconds")


class WorkspaceService:
    def __init__(self, repository: PersistedWorkspaceRepository | None = None) -> None:
        self.repository = repository or PersistedWorkspaceRepository()

    def ensure_seeded(self, workspace: dict[str, Any]) -> None:
        self.repository.ensure_seeded(workspace)

    def workspace_snapshot(self) -> dict[str, Any]:
        return self.repository.workspace_snapshot()

    def get_project(self, slug: str) -> dict[str, Any] | None:
        return self.repository.get_project(slug)

    def get_dataset(self, slug: str) -> dict[str, Any] | None:
        return self.repository.get_dataset(slug)

    def get_figure(self, slug: str) -> dict[str, Any] | None:
        return self.repository.get_figure(slug)

    def get_manuscript(self, slug: str) -> dict[str, Any] | None:
        return self.repository.get_manuscript(slug)

    def schema_version(self) -> int:
        return self.repository.schema_version()

    def list_export_jobs(self) -> list[dict[str, Any]]:
        return self.repository.list_export_jobs()

    def list_workspace_events(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.repository.list_workspace_events(limit)

    def update_project(self, slug: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        return self.repository.update_project(slug, changes)

    def create_project(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.repository.create_project(payload)

    def update_figure(self, slug: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        return self.repository.update_figure(slug, changes)

    def update_dataset(self, slug: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        return self.repository.update_dataset(slug, changes)

    def update_manuscript(self, slug: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        return self.repository.update_manuscript(slug, changes)

    def create_export_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.repository.create_export_job(payload)

    def update_export_job(self, job_key: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        return self.repository.update_export_job(job_key, changes)
