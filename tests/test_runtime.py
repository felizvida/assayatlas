from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.runtime import PersistedWorkspaceRepository, WorkspaceService


def make_workspace_payload() -> dict:
    return {
        "metrics": [],
        "quick_actions": [{"label": "Open Projects", "path": "/workspace#projects", "variant": "primary"}],
        "pinned_tasks": [{"label": "Review assay board", "path": "/projects/demo-project", "tone": "progress"}],
        "projects": [
            {
                "slug": "demo-project",
                "name": "Demo Project",
                "status": "In review",
                "tone": "progress",
                "summary": "Primary seeded workspace project.",
                "hero_chart_path": "generated/charts/01-two-group-supplement-comparison.png",
                "completion": 72,
                "figure_count": 1,
                "dataset_count": 1,
                "next_review": "Tomorrow",
                "team": [{"name": "Alex Doe", "role": "PI", "initials": "AD"}],
                "due_date": "Apr 04",
                "target_journal": "Nature Methods",
                "owner": "Alex Doe",
                "export_preset": "Nature",
                "tasks": ["Confirm caption wording"],
                "milestones": [{"label": "Draft figures", "state": "complete"}],
                "figures": [
                    {
                        "slug": "demo-figure",
                        "title": "Demo Figure",
                        "chart_path": "generated/charts/01-two-group-supplement-comparison.png",
                        "status": "Ready",
                        "tone": "success",
                        "version": "v3",
                        "next_action": "Export SVG",
                        "owner": "Alex Doe",
                    }
                ],
                "datasets": [
                    {
                        "slug": "demo-dataset",
                        "name": "Demo Dataset",
                        "kind": "Raw dataset",
                        "rows": 12,
                        "columns": 3,
                    }
                ],
                "manuscript_slug": "demo-manuscript",
                "primary_figure_slug": "demo-figure",
            }
        ],
        "manuscripts": [
            {
                "slug": "demo-manuscript",
                "title": "Demo Manuscript",
                "status": "Draft ready",
                "tone": "progress",
                "narrative": "Seeded manuscript packet.",
                "submission_preset": "Nature",
                "target_journal": "Nature Methods",
                "due_date": "Apr 04",
                "project_slug": "demo-project",
                "project_name": "Demo Project",
                "figures": [
                    {
                        "slug": "demo-figure",
                        "title": "Demo Figure",
                        "chart_path": "generated/charts/01-two-group-supplement-comparison.png",
                        "status": "Ready",
                        "tone": "success",
                        "version": "v3",
                        "next_action": "Export SVG",
                        "owner": "Alex Doe",
                    }
                ],
                "datasets": [{"slug": "demo-dataset", "name": "Demo Dataset"}],
                "sections": [{"label": "Results", "state": "complete"}],
                "deliverables": [{"label": "Figure bundle", "state": "ready"}],
                "figure_progress": "1/1 figures locked",
            }
        ],
        "figure_drafts": [
            {
                "slug": "demo-figure",
                "title": "Demo Figure",
                "chart_path": "generated/charts/01-two-group-supplement-comparison.png",
                "status": "Ready",
                "tone": "success",
                "version": "v3",
                "summary": "Seeded draft",
                "project_name": "Demo Project",
                "project_slug": "demo-project",
                "manuscript_slug": "demo-manuscript",
                "what_to_notice": "Notice this figure.",
                "analysis": "Welch t test",
                "key_metrics": ["Metric 1"],
                "publication_assets": {"bundle": "data/generated/publication/demo.zip", "svg": "data/generated/publication/demo.svg"},
                "source_note": "Demo source",
                "caption_text": "Caption",
                "methods_text": "Methods",
                "results_text": "Results",
                "data_preview": [{"value": 1}],
                "next_action": "Export SVG",
                "owner": "Alex Doe",
            }
        ],
        "datasets": [
            {
                "slug": "demo-dataset",
                "name": "Demo Dataset",
                "path": "data/raw/demo.csv",
                "kind": "Raw dataset",
                "source": "Shared public dataset",
                "description": "Seeded dataset.",
                "rows": 12,
                "columns": 3,
                "updated_at": "Mar 23, 2026",
                "preview": [{"value": 1}],
                "linked_figures": [{"slug": "demo-figure", "title": "Demo Figure", "analysis": "Welch t test"}],
                "linked_projects": [{"slug": "demo-project", "name": "Demo Project"}],
                "project_count": 1,
                "figure_count": 1,
            }
        ],
        "export_queue": [{"title": "Demo export", "status": "Ready", "tone": "success", "detail": "SVG bundle", "path": "/figures/demo-figure"}],
        "activity_feed": [{"title": "Demo export finished", "meta": "Today", "path": "/figures/demo-figure", "kind": "Figure"}],
        "tutorial_library": {"count": 20, "summary": "Seeded tutorial library.", "path": "/tutorial"},
    }


class PersistedWorkspaceRepositoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "workspace.db"
        self.repository = PersistedWorkspaceRepository(self.db_path)
        self.workspace = make_workspace_payload()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_repository_seeds_and_builds_snapshot(self) -> None:
        self.repository.ensure_seeded(self.workspace)

        snapshot = self.repository.workspace_snapshot()

        self.assertEqual(self.repository.schema_version(), 2)
        self.assertEqual(snapshot["metrics"][0]["value"], "1")
        self.assertEqual(snapshot["projects"][0]["slug"], "demo-project")
        self.assertEqual(snapshot["datasets"][0]["slug"], "demo-dataset")
        self.assertEqual(snapshot["tutorial_library"]["count"], 20)

    def test_service_reads_persisted_entities(self) -> None:
        self.repository.ensure_seeded(self.workspace)
        service = WorkspaceService(repository=self.repository)

        self.assertEqual(service.get_project("demo-project")["name"], "Demo Project")
        self.assertEqual(service.get_dataset("demo-dataset")["name"], "Demo Dataset")
        self.assertEqual(service.get_figure("demo-figure")["title"], "Demo Figure")
        self.assertEqual(service.get_manuscript("demo-manuscript")["title"], "Demo Manuscript")

    def test_seed_is_one_time_and_does_not_overwrite_existing_workspace(self) -> None:
        self.repository.ensure_seeded(self.workspace)
        changed_workspace = make_workspace_payload()
        changed_workspace["projects"][0]["name"] = "Changed Project Name"
        changed_workspace["tutorial_library"]["summary"] = "Changed summary"

        self.repository.ensure_seeded(changed_workspace)

        snapshot = self.repository.workspace_snapshot()
        self.assertEqual(snapshot["projects"][0]["name"], "Demo Project")
        self.assertEqual(snapshot["tutorial_library"]["summary"], "Seeded tutorial library.")

    def test_legacy_complete_workspace_gets_marked_without_reseed(self) -> None:
        self.repository.ensure_seeded(self.workspace)

        with sqlite3.connect(self.db_path) as connection:
            connection.execute("DELETE FROM workspace_meta WHERE key = ?", ("seed_state",))
            connection.execute(
                "UPDATE projects SET payload_json = ? WHERE slug = ?",
                (
                    json.dumps(
                        {
                            **self.repository.get_project("demo-project"),
                            "name": "Legacy Edited Project",
                        }
                    ),
                    "demo-project",
                ),
            )
            connection.commit()

        self.repository.ensure_seeded(self.workspace)

        snapshot = self.repository.workspace_snapshot()
        self.assertEqual(snapshot["projects"][0]["name"], "Legacy Edited Project")
        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT payload_json FROM workspace_meta WHERE key = ?",
                ("seed_state",),
            ).fetchone()
        self.assertIsNotNone(row)

    def test_partial_workspace_is_reseeded(self) -> None:
        self.repository.initialize()
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                "INSERT INTO projects(slug, sort_order, payload_json) VALUES (?, ?, ?)",
                ("orphan", 0, json.dumps({"slug": "orphan", "name": "Orphan"})),
            )
            connection.commit()

        self.repository.ensure_seeded(self.workspace)

        snapshot = self.repository.workspace_snapshot()
        self.assertEqual(snapshot["projects"][0]["slug"], "demo-project")
        self.assertEqual(snapshot["datasets"][0]["slug"], "demo-dataset")
        self.assertEqual(snapshot["tutorial_library"]["count"], 20)

    def test_project_update_persists_and_emits_event(self) -> None:
        self.repository.ensure_seeded(self.workspace)

        updated = self.repository.update_project(
            "demo-project",
            {"name": "Demo Project Updated", "status": "Ready for submission", "completion": 95, "summary": "Updated summary"},
        )

        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertEqual(updated["name"], "Demo Project Updated")
        self.assertEqual(updated["status"], "Ready for submission")
        self.assertEqual(updated["completion"], 95)

        snapshot = self.repository.workspace_snapshot()
        self.assertEqual(snapshot["projects"][0]["name"], "Demo Project Updated")
        self.assertEqual(snapshot["projects"][0]["status"], "Ready for submission")
        self.assertEqual(snapshot["activity_feed"][-1]["kind"], "Project")
        self.assertEqual(snapshot["workspace_events"][0]["event_type"], "project.updated")

    def test_project_create_persists_and_emits_event(self) -> None:
        self.repository.ensure_seeded(self.workspace)

        created = self.repository.create_project(
            {
                "name": "Immune Signaling Atlas",
                "owner": "Maya Singh",
                "target_journal": "Nature Immunology",
                "summary": "A fresh project shell for a cytokine signaling study.",
            }
        )

        self.assertEqual(created["slug"], "immune-signaling-atlas")
        self.assertEqual(created["status"], "Draft setup")
        self.assertEqual(created["figure_count"], 0)

        snapshot = self.repository.workspace_snapshot()
        self.assertEqual(snapshot["projects"][-1]["slug"], "immune-signaling-atlas")
        self.assertEqual(snapshot["workspace_events"][0]["event_type"], "project.created")

    def test_project_create_rejects_blank_name(self) -> None:
        self.repository.ensure_seeded(self.workspace)

        with self.assertRaisesRegex(ValueError, "Project name must be a non-empty string"):
            self.repository.create_project(
                {
                    "name": "   ",
                    "owner": "Maya Singh",
                }
            )

    def test_project_create_rejects_malformed_tasks(self) -> None:
        self.repository.ensure_seeded(self.workspace)

        with self.assertRaisesRegex(ValueError, "Project tasks item must be a non-empty string"):
            self.repository.create_project(
                {
                    "name": "Immune Signaling Atlas",
                    "tasks": ["Prepare legend", "   "],
                }
            )

    def test_export_job_create_and_update_persist(self) -> None:
        self.repository.ensure_seeded(self.workspace)

        created = self.repository.create_export_job(
            {
                "title": "Fresh TIFF export",
                "detail": "Journal-ready raster package",
                "path": "/figures/demo-figure",
            }
        )
        updated = self.repository.update_export_job(
            created["job_key"],
            {"status": "Ready", "tone": "success"},
        )

        self.assertEqual(created["status"], "Queued")
        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertEqual(updated["status"], "Ready")

        export_jobs = self.repository.list_export_jobs()
        self.assertEqual(len(export_jobs), 2)
        self.assertTrue(export_jobs[0]["job_key"].startswith("export_jobs-0-"))
        self.assertEqual(export_jobs[-1]["title"], "Fresh TIFF export")
        self.assertEqual(self.repository.list_workspace_events()[0]["event_type"], "export_job.updated")

    def test_export_job_create_rejects_blank_required_fields(self) -> None:
        self.repository.ensure_seeded(self.workspace)

        with self.assertRaisesRegex(ValueError, "Export job title must be a non-empty string"):
            self.repository.create_export_job(
                {
                    "title": "   ",
                    "detail": "High-resolution raster package",
                    "path": "/figures/demo-figure",
                }
            )

    def test_export_job_update_rejects_blank_fields(self) -> None:
        self.repository.ensure_seeded(self.workspace)

        with self.assertRaisesRegex(ValueError, "Export job detail must be a non-empty string"):
            self.repository.update_export_job("export_jobs-0-demo-export", {"detail": "   "})

    def test_figure_update_persists_and_emits_event(self) -> None:
        self.repository.ensure_seeded(self.workspace)

        updated = self.repository.update_figure(
            "demo-figure",
            {
                "status": "Ready for journal upload",
                "version": "v4",
                "summary": "Updated figure summary.",
                "next_action": "Lock panel labels",
            },
        )

        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertEqual(updated["status"], "Ready for journal upload")
        self.assertEqual(updated["version"], "v4")

        figure = self.repository.get_figure("demo-figure")
        self.assertIsNotNone(figure)
        assert figure is not None
        self.assertEqual(figure["next_action"], "Lock panel labels")
        self.assertEqual(self.repository.list_workspace_events()[0]["event_type"], "figure.updated")

    def test_project_update_rejects_malformed_team(self) -> None:
        self.repository.ensure_seeded(self.workspace)

        with self.assertRaisesRegex(ValueError, "Project team initials must be a non-empty string"):
            self.repository.update_project(
                "demo-project",
                {
                    "team": [{"name": "Alex Doe", "role": "PI", "initials": "   "}],
                },
            )

    def test_project_update_rejects_blank_name(self) -> None:
        self.repository.ensure_seeded(self.workspace)

        with self.assertRaisesRegex(ValueError, "Project name must be a non-empty string"):
            self.repository.update_project(
                "demo-project",
                {
                    "name": "   ",
                },
            )

    def test_figure_update_rejects_malformed_key_metrics(self) -> None:
        self.repository.ensure_seeded(self.workspace)

        with self.assertRaisesRegex(ValueError, "Figure key_metrics item must be a non-empty string"):
            self.repository.update_figure(
                "demo-figure",
                {
                    "key_metrics": ["Metric 1", "   "],
                },
            )

    def test_figure_update_rejects_blank_summary(self) -> None:
        self.repository.ensure_seeded(self.workspace)

        with self.assertRaisesRegex(ValueError, "Figure summary must be a non-empty string"):
            self.repository.update_figure(
                "demo-figure",
                {
                    "summary": "   ",
                },
            )

    def test_dataset_update_persists_and_emits_event(self) -> None:
        self.repository.ensure_seeded(self.workspace)

        updated = self.repository.update_dataset(
            "demo-dataset",
            {
                "name": "Demo Dataset Updated",
                "kind": "Curated assay table",
                "source": "Updated source note",
                "description": "Updated dataset description.",
                "updated_at": "Mar 24, 2026",
            },
        )

        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertEqual(updated["name"], "Demo Dataset Updated")
        self.assertEqual(updated["kind"], "Curated assay table")

        dataset = self.repository.get_dataset("demo-dataset")
        self.assertIsNotNone(dataset)
        assert dataset is not None
        self.assertEqual(dataset["description"], "Updated dataset description.")
        self.assertEqual(self.repository.list_workspace_events()[0]["event_type"], "dataset.updated")

    def test_dataset_update_rejects_blank_description(self) -> None:
        self.repository.ensure_seeded(self.workspace)

        with self.assertRaisesRegex(ValueError, "Dataset description must be a non-empty string"):
            self.repository.update_dataset(
                "demo-dataset",
                {
                    "description": "   ",
                },
            )

    def test_manuscript_update_persists_and_emits_event(self) -> None:
        self.repository.ensure_seeded(self.workspace)

        updated = self.repository.update_manuscript(
            "demo-manuscript",
            {
                "status": "Submission packet ready",
                "figure_progress": "1/1 figures approved",
                "narrative": "Updated manuscript narrative.",
            },
        )

        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertEqual(updated["status"], "Submission packet ready")
        self.assertEqual(updated["figure_progress"], "1/1 figures approved")

        manuscript = self.repository.get_manuscript("demo-manuscript")
        self.assertIsNotNone(manuscript)
        assert manuscript is not None
        self.assertEqual(manuscript["narrative"], "Updated manuscript narrative.")
        self.assertEqual(self.repository.list_workspace_events()[0]["event_type"], "manuscript.updated")

    def test_manuscript_update_rejects_malformed_sections(self) -> None:
        self.repository.ensure_seeded(self.workspace)

        with self.assertRaisesRegex(ValueError, "Manuscript sections state must be a non-empty string"):
            self.repository.update_manuscript(
                "demo-manuscript",
                {
                    "sections": [{"label": "Results", "state": "   "}],
                },
            )

    def test_manuscript_update_rejects_blank_narrative(self) -> None:
        self.repository.ensure_seeded(self.workspace)

        with self.assertRaisesRegex(ValueError, "Manuscript narrative must be a non-empty string"):
            self.repository.update_manuscript(
                "demo-manuscript",
                {
                    "narrative": "   ",
                },
            )


if __name__ == "__main__":
    unittest.main()
