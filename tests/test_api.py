from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app import create_app
from app.content import ContentService, FileBackedContentRepository
from app.runtime import PersistedWorkspaceRepository, WorkspaceService


def make_api_manifest() -> dict:
    return {
        "product_name": "AssayAtlas",
        "summary": "API test manifest",
        "generated_at": "2026-03-23T00:00:00Z",
        "use_cases": [
            {
                "order": 1,
                "slug": "demo-figure",
                "title": "Demo Figure",
                "category": "Cat",
                "analysis": "Welch t test",
                "goal": "Goal",
                "steps": ["1", "2", "3", "4", "5"],
                "what_to_notice": "Notice",
                "source_note": "Source",
                "data_files": ["data/raw/demo.csv"],
                "screenshot_path": "/assets/screenshots/demo.png",
                "summary": "Summary",
                "key_metrics": ["m1"],
                "chart_path": "generated/charts/01-two-group-supplement-comparison.png",
                "data_preview": [{"value": 1}],
                "input_files": ["data/raw/demo.csv"],
                "generated_file": None,
                "publication_assets": {
                    "bundle": "data/generated/publication/demo.zip",
                    "svg": "data/generated/publication/demo.svg",
                    "pdf": "data/generated/publication/demo.pdf",
                    "png": "data/generated/publication/demo.png",
                    "tiff": "data/generated/publication/demo.tiff",
                    "caption": "data/generated/publication/demo-caption.md",
                    "methods": "data/generated/publication/demo-methods.md",
                    "results": "data/generated/publication/demo-results.md",
                    "checklist": "data/generated/publication/demo-checklist.md",
                },
                "caption_text": "Caption",
                "methods_text": "Methods",
                "results_text": "Results",
                "submission_checklist": ["check"],
            }
        ],
        "workspace": {
            "metrics": [],
            "quick_actions": [{"label": "Open Projects", "path": "/workspace#projects", "variant": "primary"}],
            "pinned_tasks": [{"label": "Review seeded project", "path": "/projects/demo-project", "tone": "progress"}],
            "projects": [
                {
                    "slug": "demo-project",
                    "name": "Demo Project",
                    "status": "In review",
                    "tone": "progress",
                    "summary": "Seeded project summary.",
                    "hero_chart_path": "generated/charts/01-two-group-supplement-comparison.png",
                    "completion": 70,
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
                    "datasets": [{"slug": "demo-dataset", "name": "Demo Dataset", "kind": "Raw dataset", "rows": 12, "columns": 3}],
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
            "export_queue": [{"title": "Demo export", "status": "Queued", "tone": "warning", "detail": "SVG bundle", "path": "/figures/demo-figure"}],
            "activity_feed": [{"title": "Demo export finished", "meta": "Today", "path": "/figures/demo-figure", "kind": "Figure"}],
            "tutorial_library": {"count": 20, "summary": "Seeded tutorial library.", "path": "/tutorial"},
        },
    }


class WorkspaceApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        manifest_path = root / "use_cases.json"
        manifest_path.write_text(json.dumps(make_api_manifest()), encoding="utf-8")
        content_service = ContentService(
            repository=FileBackedContentRepository(manifest_path=manifest_path),
            workspace_service=WorkspaceService(repository=PersistedWorkspaceRepository(root / "workspace.db")),
        )
        self.client = create_app(content_service=content_service).test_client()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_workspace_api_returns_seeded_runtime_snapshot(self) -> None:
        response = self.client.get("/api/workspace")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["projects"][0]["slug"], "demo-project")
        self.assertEqual(payload["metrics"][0]["value"], "1")

    def test_project_patch_updates_persisted_runtime_project(self) -> None:
        response = self.client.patch(
            "/api/projects/demo-project",
            json={"name": "Demo Project Updated", "status": "Ready for submission", "completion": 95},
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["project"]["name"], "Demo Project Updated")
        self.assertEqual(payload["project"]["status"], "Ready for submission")
        self.assertEqual(payload["project"]["completion"], 95)

        read_back = self.client.get("/api/projects/demo-project").get_json()
        self.assertEqual(read_back["project"]["name"], "Demo Project Updated")
        self.assertEqual(read_back["project"]["status"], "Ready for submission")

    def test_project_post_creates_persisted_runtime_project(self) -> None:
        response = self.client.post(
            "/api/projects",
            json={
                "name": "Immune Signaling Atlas",
                "owner": "Maya Singh",
                "target_journal": "Nature Immunology",
                "summary": "A fresh project shell for a cytokine signaling study.",
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(payload["project"]["slug"], "immune-signaling-atlas")
        self.assertEqual(payload["location"], "/projects/immune-signaling-atlas")

        read_back = self.client.get("/api/projects/immune-signaling-atlas").get_json()
        self.assertEqual(read_back["project"]["owner"], "Maya Singh")
        self.assertIsNone(read_back["manuscript"])

        html_response = self.client.get("/projects/immune-signaling-atlas")
        self.assertEqual(html_response.status_code, 200)
        self.assertIn(b"No figure drafts linked yet.", html_response.data)

    def test_project_post_rejects_blank_name(self) -> None:
        response = self.client.post(
            "/api/projects",
            json={
                "name": "   ",
                "owner": "Maya Singh",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Project name must be a non-empty string")

    def test_project_post_rejects_malformed_tasks(self) -> None:
        response = self.client.post(
            "/api/projects",
            json={
                "name": "Immune Signaling Atlas",
                "tasks": ["Draft caption", "   "],
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Project tasks item must be a non-empty string")

    def test_export_job_api_creates_and_updates_job(self) -> None:
        create_response = self.client.post(
            "/api/export-jobs",
            json={
                "title": "Fresh TIFF export",
                "detail": "High-resolution raster package",
                "path": "/figures/demo-figure",
            },
        )
        created = create_response.get_json()["export_job"]

        update_response = self.client.patch(
            f"/api/export-jobs/{created['job_key']}",
            json={"status": "Ready", "tone": "success"},
        )
        updated = update_response.get_json()["export_job"]
        events = self.client.get("/api/workspace-events").get_json()["events"]

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(updated["status"], "Ready")
        self.assertEqual(events[0]["event_type"], "export_job.updated")
        self.assertEqual(self.client.get("/api/export-jobs").get_json()["export_jobs"][-1]["title"], "Fresh TIFF export")

    def test_export_job_api_rejects_blank_create_fields(self) -> None:
        response = self.client.post(
            "/api/export-jobs",
            json={"title": "   ", "detail": "   ", "path": "   "},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Export job title must be a non-empty string")

    def test_export_job_api_rejects_blank_update_fields(self) -> None:
        response = self.client.patch(
            "/api/export-jobs/export_jobs-0-demo-export",
            json={"detail": "   "},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Export job detail must be a non-empty string")

    def test_figure_patch_updates_persisted_runtime_figure(self) -> None:
        response = self.client.patch(
            "/api/figures/demo-figure",
            json={"status": "Ready for journal upload", "version": "v4", "next_action": "Lock panel labels"},
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["figure"]["status"], "Ready for journal upload")
        self.assertEqual(payload["figure"]["version"], "v4")

        read_back = self.client.get("/api/figures/demo-figure").get_json()
        self.assertEqual(read_back["figure"]["next_action"], "Lock panel labels")

    def test_figure_patch_rejects_malformed_key_metrics(self) -> None:
        response = self.client.patch(
            "/api/figures/demo-figure",
            json={"key_metrics": ["Metric 1", "   "]},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Figure key_metrics item must be a non-empty string")

    def test_figure_patch_rejects_blank_summary(self) -> None:
        response = self.client.patch(
            "/api/figures/demo-figure",
            json={"summary": "   "},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Figure summary must be a non-empty string")

    def test_dataset_patch_updates_persisted_runtime_dataset(self) -> None:
        response = self.client.patch(
            "/api/datasets/demo-dataset",
            json={
                "name": "Demo Dataset Updated",
                "kind": "Curated assay table",
                "source": "Updated source note",
                "description": "Updated dataset description.",
                "updated_at": "Mar 24, 2026",
            },
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["dataset"]["name"], "Demo Dataset Updated")
        self.assertEqual(payload["dataset"]["kind"], "Curated assay table")

        read_back = self.client.get("/api/datasets/demo-dataset").get_json()
        self.assertEqual(read_back["dataset"]["updated_at"], "Mar 24, 2026")

    def test_dataset_patch_rejects_blank_description(self) -> None:
        response = self.client.patch(
            "/api/datasets/demo-dataset",
            json={"description": "   "},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Dataset description must be a non-empty string")

    def test_manuscript_patch_updates_persisted_runtime_packet(self) -> None:
        response = self.client.patch(
            "/api/manuscripts/demo-manuscript",
            json={"status": "Submission packet ready", "figure_progress": "1/1 figures approved"},
        )
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["manuscript"]["status"], "Submission packet ready")
        self.assertEqual(payload["manuscript"]["figure_progress"], "1/1 figures approved")

        read_back = self.client.get("/api/manuscripts/demo-manuscript").get_json()
        self.assertEqual(read_back["manuscript"]["status"], "Submission packet ready")

    def test_project_patch_rejects_malformed_team(self) -> None:
        response = self.client.patch(
            "/api/projects/demo-project",
            json={"team": [{"name": "Alex Doe", "role": "PI", "initials": "   "}]},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Project team initials must be a non-empty string")

    def test_project_patch_rejects_blank_name(self) -> None:
        response = self.client.patch(
            "/api/projects/demo-project",
            json={"name": "   "},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Project name must be a non-empty string")

    def test_manuscript_patch_rejects_malformed_sections(self) -> None:
        response = self.client.patch(
            "/api/manuscripts/demo-manuscript",
            json={"sections": [{"label": "Results", "state": "   "}]},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Manuscript sections state must be a non-empty string")

    def test_manuscript_patch_rejects_blank_narrative(self) -> None:
        response = self.client.patch(
            "/api/manuscripts/demo-manuscript",
            json={"narrative": "   "},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Manuscript narrative must be a non-empty string")


if __name__ == "__main__":
    unittest.main()
