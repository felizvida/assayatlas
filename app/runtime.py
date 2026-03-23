from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_DB_PATH = ROOT / "data" / "assayatlas.db"
SCHEMA_VERSION = 1


class PersistedWorkspaceRepository:
    def __init__(self, db_path: Path = WORKSPACE_DB_PATH) -> None:
        self.db_path = db_path

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection:
            self._apply_schema(connection)

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
        }

    def get_project(self, slug: str) -> dict[str, Any] | None:
        return self._get_payload("projects", "slug", slug)

    def get_dataset(self, slug: str) -> dict[str, Any] | None:
        return self._get_payload("datasets", "slug", slug)

    def get_figure(self, slug: str) -> dict[str, Any] | None:
        return self._get_payload("figure_drafts", "slug", slug)

    def get_manuscript(self, slug: str) -> dict[str, Any] | None:
        return self._get_payload("manuscripts", "slug", slug)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _apply_schema(self, connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

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
        connection.execute(
            "INSERT OR REPLACE INTO schema_meta(key, value) VALUES (?, ?)",
            ("schema_version", str(SCHEMA_VERSION)),
        )
        connection.commit()

    def _seed_workspace(self, connection: sqlite3.Connection, workspace: dict[str, Any]) -> None:
        connection.execute("DELETE FROM workspace_meta")
        for table in ("projects", "datasets", "figure_drafts", "manuscripts", "export_jobs", "activity_feed"):
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
