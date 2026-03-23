from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_DB_PATH = ROOT / "data" / "assayatlas.db"
SCHEMA_VERSION = 2


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
            count = connection.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
            if count:
                return
            self._seed_workspace(connection, workspace)

    def workspace_snapshot(self) -> dict[str, Any]:
        self.initialize()
        with closing(self._connect()) as connection:
            projects = self._list_payloads(connection, "projects")
            figure_drafts = self._list_payloads(connection, "figure_drafts")
            manuscripts = self._list_payloads(connection, "manuscripts")
            datasets = self._list_payloads(connection, "datasets")
            export_queue = self._list_payloads(connection, "export_jobs")
            activity_feed = self._list_payloads(connection, "activity_feed")
            quick_actions = self._load_meta(connection, "quick_actions", [])
            pinned_tasks = self._load_meta(connection, "pinned_tasks", [])
            tutorial_library = self._load_meta(
                connection,
                "tutorial_library",
                {"count": 0, "summary": "", "path": "/tutorial"},
            )
            workspace_events = self._list_events(connection, limit=20)

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
            "projects": projects,
            "manuscripts": manuscripts,
            "figure_drafts": figure_drafts,
            "datasets": datasets,
            "export_queue": export_queue,
            "activity_feed": activity_feed,
            "tutorial_library": tutorial_library,
            "workspace_events": workspace_events,
        }

    def schema_version(self) -> int:
        self.initialize()
        with closing(self._connect()) as connection:
            return self._current_schema_version(connection)

    def get_project(self, slug: str) -> dict[str, Any] | None:
        return self._get_payload("projects", "slug", slug)

    def get_dataset(self, slug: str) -> dict[str, Any] | None:
        return self._get_payload("datasets", "slug", slug)

    def get_figure(self, slug: str) -> dict[str, Any] | None:
        return self._get_payload("figure_drafts", "slug", slug)

    def get_manuscript(self, slug: str) -> dict[str, Any] | None:
        return self._get_payload("manuscripts", "slug", slug)

    def list_export_jobs(self) -> list[dict[str, Any]]:
        self.initialize()
        with closing(self._connect()) as connection:
            return self._list_payloads(connection, "export_jobs")

    def list_workspace_events(self, limit: int = 20) -> list[dict[str, Any]]:
        self.initialize()
        with closing(self._connect()) as connection:
            return self._list_events(connection, limit)

    def update_project(self, slug: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        allowed_fields = {
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

        self.initialize()
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT sort_order, payload_json FROM projects WHERE slug = ?",
                (slug,),
            ).fetchone()
            if not row:
                return None
            payload = json.loads(row["payload_json"])
            payload.update(sanitized_changes)
            connection.execute(
                "UPDATE projects SET payload_json = ? WHERE slug = ?",
                (json.dumps(payload), slug),
            )
            event_time = self._timestamp()
            self._append_activity_item(
                connection,
                {
                    "title": f"{payload['name']} updated",
                    "meta": event_time,
                    "path": f"/projects/{slug}",
                    "kind": "Project",
                },
            )
            self._append_workspace_event(
                connection,
                event_type="project.updated",
                subject_key=slug,
                payload={"changes": sanitized_changes, "project_name": payload["name"]},
            )
            connection.commit()
            return payload

    def create_export_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        required = {"title", "detail", "path"}
        missing = sorted(required - payload.keys())
        if missing:
            raise ValueError(f"Missing required export job fields: {', '.join(missing)}")

        self.initialize()
        with closing(self._connect()) as connection:
            sort_order = self._next_sort_order(connection, "export_jobs")
            job_key = payload.get("job_key") or f"export-{sort_order}-{self._slugify(payload['title'])}"
            job = {
                "job_key": job_key,
                "title": payload["title"],
                "status": payload.get("status", "Queued"),
                "tone": payload.get("tone", "warning"),
                "detail": payload["detail"],
                "path": payload["path"],
            }
            connection.execute(
                "INSERT INTO export_jobs(job_key, sort_order, payload_json) VALUES (?, ?, ?)",
                (job_key, sort_order, json.dumps(job)),
            )
            event_time = self._timestamp()
            self._append_activity_item(
                connection,
                {
                    "title": f"{job['title']} queued",
                    "meta": event_time,
                    "path": job["path"],
                    "kind": "Export",
                },
            )
            self._append_workspace_event(
                connection,
                event_type="export_job.created",
                subject_key=job_key,
                payload=job,
            )
            connection.commit()
            return job

    def update_export_job(self, job_key: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        allowed_fields = {"title", "status", "tone", "detail", "path"}
        sanitized_changes = {key: value for key, value in changes.items() if key in allowed_fields}
        if not sanitized_changes:
            with closing(self._connect()) as connection:
                row = connection.execute(
                    "SELECT payload_json FROM export_jobs WHERE job_key = ?",
                    (job_key,),
                ).fetchone()
            return json.loads(row["payload_json"]) if row else None

        self.initialize()
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT payload_json FROM export_jobs WHERE job_key = ?",
                (job_key,),
            ).fetchone()
            if not row:
                return None
            payload = json.loads(row["payload_json"])
            payload.update(sanitized_changes)
            connection.execute(
                "UPDATE export_jobs SET payload_json = ? WHERE job_key = ?",
                (json.dumps(payload), job_key),
            )
            event_time = self._timestamp()
            self._append_activity_item(
                connection,
                {
                    "title": f"{payload['title']} marked {payload['status']}",
                    "meta": event_time,
                    "path": payload["path"],
                    "kind": "Export",
                },
            )
            self._append_workspace_event(
                connection,
                event_type="export_job.updated",
                subject_key=job_key,
                payload={"changes": sanitized_changes, "job": payload},
            )
            connection.commit()
            return payload

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

    def _seed_workspace(self, connection: sqlite3.Connection, workspace: dict[str, Any]) -> None:
        connection.execute("DELETE FROM workspace_meta")
        for table in ("projects", "datasets", "figure_drafts", "manuscripts", "export_jobs", "activity_feed", "workspace_events"):
            connection.execute(f"DELETE FROM {table}")

        self._store_meta(connection, "quick_actions", workspace.get("quick_actions", []))
        self._store_meta(connection, "pinned_tasks", workspace.get("pinned_tasks", []))
        self._store_meta(connection, "tutorial_library", workspace.get("tutorial_library", {}))

        self._insert_slugged_rows(connection, "projects", workspace.get("projects", []))
        self._insert_slugged_rows(connection, "datasets", workspace.get("datasets", []))
        self._insert_slugged_rows(connection, "figure_drafts", workspace.get("figure_drafts", []))
        self._insert_slugged_rows(connection, "manuscripts", workspace.get("manuscripts", []))
        self._insert_keyed_rows(connection, "export_jobs", "job_key", workspace.get("export_queue", []))
        self._insert_keyed_rows(connection, "activity_feed", "feed_key", workspace.get("activity_feed", []))
        connection.commit()

    def _insert_slugged_rows(
        self,
        connection: sqlite3.Connection,
        table: str,
        rows: list[dict[str, Any]],
    ) -> None:
        for index, item in enumerate(rows):
            connection.execute(
                f"INSERT INTO {table}(slug, sort_order, payload_json) VALUES (?, ?, ?)",
                (item["slug"], index, json.dumps(item)),
            )

    def _insert_keyed_rows(
        self,
        connection: sqlite3.Connection,
        table: str,
        key_column: str,
        rows: list[dict[str, Any]],
    ) -> None:
        for index, item in enumerate(rows):
            key = item.get("path") or item.get("title") or f"{table}-{index}"
            connection.execute(
                f"INSERT INTO {table}({key_column}, sort_order, payload_json) VALUES (?, ?, ?)",
                (key, index, json.dumps(item)),
            )

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

    def _list_payloads(self, connection: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
        rows = connection.execute(
            f"SELECT payload_json FROM {table} ORDER BY sort_order ASC"
        ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def _list_events(self, connection: sqlite3.Connection, limit: int) -> list[dict[str, Any]]:
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
            {
                "event_type": row["event_type"],
                "subject_key": row["subject_key"],
                "created_at": row["created_at"],
                "payload": json.loads(row["payload_json"]),
            }
            for row in rows
        ]

    def _get_payload(self, table: str, key_column: str, key: str) -> dict[str, Any] | None:
        self.initialize()
        with closing(self._connect()) as connection:
            row = connection.execute(
                f"SELECT payload_json FROM {table} WHERE {key_column} = ?",
                (key,),
            ).fetchone()
        if not row:
            return None
        return json.loads(row["payload_json"])

    def _next_sort_order(self, connection: sqlite3.Connection, table: str) -> int:
        row = connection.execute(f"SELECT COALESCE(MAX(sort_order), -1) AS max_sort_order FROM {table}").fetchone()
        return int(row["max_sort_order"]) + 1

    def _append_activity_item(self, connection: sqlite3.Connection, item: dict[str, Any]) -> None:
        sort_order = self._next_sort_order(connection, "activity_feed")
        feed_key = f"activity-{sort_order}-{self._slugify(item['title'])}"
        connection.execute(
            "INSERT INTO activity_feed(feed_key, sort_order, payload_json) VALUES (?, ?, ?)",
            (feed_key, sort_order, json.dumps(item)),
        )

    def _append_workspace_event(
        self,
        connection: sqlite3.Connection,
        *,
        event_type: str,
        subject_key: str,
        payload: dict[str, Any],
    ) -> None:
        connection.execute(
            """
            INSERT INTO workspace_events(event_type, subject_key, payload_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (event_type, subject_key, json.dumps(payload), self._timestamp()),
        )

    def _slugify(self, value: str) -> str:
        return "-".join("".join(char.lower() if char.isalnum() else " " for char in value).split()) or "item"

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

    def create_export_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.repository.create_export_job(payload)

    def update_export_job(self, job_key: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        return self.repository.update_export_job(job_key, changes)
