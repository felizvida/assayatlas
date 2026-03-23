from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.content import ContentService, DocDescriptor, DownloadPolicy, FileBackedContentRepository
from app.runtime import PersistedWorkspaceRepository, WorkspaceService


def make_manifest(product_name: str = "AssayAtlas") -> dict:
    use_cases = [
        {
            "order": 1,
            "slug": "alpha",
            "title": "Alpha",
            "category": "Cat",
            "analysis": "A",
            "goal": "Goal",
            "steps": ["1", "2", "3", "4", "5"],
            "what_to_notice": "Notice",
            "source_note": "Source",
            "data_files": ["data/raw/alpha.csv"],
            "screenshot_path": "/assets/screenshots/alpha.png",
            "summary": "Summary",
            "key_metrics": ["m1"],
            "chart_path": "generated/charts/alpha.png",
            "data_preview": [{"value": 1}],
            "input_files": ["data/raw/alpha.csv"],
            "generated_file": None,
            "publication_assets": {
                "bundle": "data/generated/publication/alpha.zip",
                "svg": "data/generated/publication/alpha.svg",
                "pdf": "data/generated/publication/alpha.pdf",
                "png": "data/generated/publication/alpha.png",
                "tiff": "data/generated/publication/alpha.tiff",
                "caption": "data/generated/publication/alpha-caption.md",
                "methods": "data/generated/publication/alpha-methods.md",
                "results": "data/generated/publication/alpha-results.md",
                "checklist": "data/generated/publication/alpha-checklist.md",
            },
            "caption_text": "Caption",
            "methods_text": "Methods",
            "results_text": "Results",
            "submission_checklist": ["check"],
        },
        {
            "order": 2,
            "slug": "beta",
            "title": "Beta",
            "category": "Cat",
            "analysis": "B",
            "goal": "Goal",
            "steps": ["1", "2", "3", "4", "5"],
            "what_to_notice": "Notice",
            "source_note": "Source",
            "data_files": ["data/raw/beta.csv"],
            "screenshot_path": "/assets/screenshots/beta.png",
            "summary": "Summary",
            "key_metrics": ["m1"],
            "chart_path": "generated/charts/beta.png",
            "data_preview": [{"value": 2}],
            "input_files": ["data/raw/beta.csv"],
            "generated_file": None,
            "publication_assets": {
                "bundle": "data/generated/publication/beta.zip",
                "svg": "data/generated/publication/beta.svg",
                "pdf": "data/generated/publication/beta.pdf",
                "png": "data/generated/publication/beta.png",
                "tiff": "data/generated/publication/beta.tiff",
                "caption": "data/generated/publication/beta-caption.md",
                "methods": "data/generated/publication/beta-methods.md",
                "results": "data/generated/publication/beta-results.md",
                "checklist": "data/generated/publication/beta-checklist.md",
            },
            "caption_text": "Caption",
            "methods_text": "Methods",
            "results_text": "Results",
            "submission_checklist": ["check"],
        },
    ]
    workspace = {
        "metrics": [],
        "quick_actions": [],
        "pinned_tasks": [],
        "projects": [
            {
                "slug": "proj",
                "name": "Project",
                "manuscript_slug": "ms",
                "primary_figure_slug": "alpha",
                "datasets": [],
            }
        ],
        "manuscripts": [
            {
                "slug": "ms",
                "project_slug": "proj",
                "title": "Manuscript",
                "figures": [],
            }
        ],
        "figure_drafts": [
            {
                "slug": "alpha",
                "project_slug": "proj",
                "manuscript_slug": "ms",
                "title": "Alpha",
            }
        ],
        "datasets": [
            {
                "slug": "dataset",
                "name": "Dataset",
                "path": "data/raw/alpha.csv",
            }
        ],
        "export_queue": [],
        "activity_feed": [],
        "tutorial_library": {"count": 2, "summary": "Summary", "path": "/tutorial"},
    }
    return {
        "product_name": product_name,
        "summary": "Manifest summary",
        "generated_at": "2026-03-18T00:00:00Z",
        "use_cases": use_cases,
        "workspace": workspace,
    }


class ContentLayerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.manifest_path = self.root / "use_cases.json"
        self.training_doc = self.root / "training.md"
        self.workspace_db_path = self.root / "workspace.db"
        self.manifest_path.write_text(json.dumps(make_manifest()), encoding="utf-8")
        self.training_doc.write_text("# Training\n\nVersion one", encoding="utf-8")
        self.repo = FileBackedContentRepository(
            manifest_path=self.manifest_path,
            doc_page_config={
                "training": DocDescriptor(
                    slug="training",
                    title="Training",
                    description="Guide",
                    path=self.training_doc,
                )
            },
        )
        self.workspace_service = WorkspaceService(repository=PersistedWorkspaceRepository(self.workspace_db_path))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_manifest_reloads_when_file_changes(self) -> None:
        first = self.repo.manifest()
        updated = make_manifest(product_name="AtlasNext")
        self.manifest_path.write_text(json.dumps(updated), encoding="utf-8")
        second = self.repo.manifest()
        self.assertEqual(first.product_name, "AssayAtlas")
        self.assertEqual(second.product_name, "AtlasNext")

    def test_doc_page_reloads_when_markdown_changes(self) -> None:
        first = self.repo.doc_page("training")
        self.training_doc.write_text("# Training\n\nVersion two", encoding="utf-8")
        second = self.repo.doc_page("training")
        self.assertIn("Version one", str(first.html))
        self.assertIn("Version two", str(second.html))

    def test_download_policy_allows_only_whitelisted_paths(self) -> None:
        generated_dir = self.root / "data" / "generated"
        raw_dir = self.root / "data" / "raw"
        docs_dir = self.root / "docs" / "tutorial"
        secret_dir = self.root / ".git"
        assets_dir = self.root / "assets"
        generated_dir.mkdir(parents=True)
        raw_dir.mkdir(parents=True)
        docs_dir.mkdir(parents=True)
        secret_dir.mkdir(parents=True)
        assets_dir.mkdir(parents=True)

        allowed_generated = generated_dir / "artifact.json"
        allowed_generated.write_text("{}", encoding="utf-8")
        allowed_doc = docs_dir / "USE_CASE_CATALOG.md"
        allowed_doc.write_text("# Catalog", encoding="utf-8")
        blocked = secret_dir / "config"
        blocked.write_text("[core]", encoding="utf-8")
        asset = assets_dir / "image.png"
        asset.write_text("png", encoding="utf-8")

        policy = DownloadPolicy(
            root=self.root,
            allowed_roots=(generated_dir, raw_dir),
            allowed_files=(allowed_doc,),
        )

        self.assertEqual(policy.resolve_download("data/generated/artifact.json"), allowed_generated.resolve())
        self.assertEqual(policy.resolve_download("docs/tutorial/USE_CASE_CATALOG.md"), allowed_doc.resolve())
        self.assertEqual(policy.resolve_asset("image.png"), asset.resolve())
        with self.assertRaises(PermissionError):
            policy.resolve_download(".git/config")

    def test_content_service_builds_use_case_navigation(self) -> None:
        service = ContentService(repository=self.repo, workspace_service=self.workspace_service)
        page = service.use_case_page("beta")
        self.assertIsNotNone(page)
        assert page is not None
        self.assertEqual(page.item["slug"], "beta")
        self.assertEqual(page.previous_item["slug"], "alpha")
        self.assertIsNone(page.next_item)
        self.assertEqual(service.site_globals().product_name, "AssayAtlas")

    def test_workspace_pages_keep_working_after_manifest_workspace_changes(self) -> None:
        service = ContentService(repository=self.repo, workspace_service=self.workspace_service)

        seeded_project_page = service.project_page("proj")
        self.assertIsNotNone(seeded_project_page)
        assert seeded_project_page is not None
        self.assertEqual(seeded_project_page.project["name"], "Project")

        updated = make_manifest()
        updated["workspace"] = {
            "metrics": [],
            "quick_actions": [],
            "pinned_tasks": [],
            "projects": [],
            "manuscripts": [],
            "figure_drafts": [],
            "datasets": [],
            "export_queue": [],
            "activity_feed": [],
            "tutorial_library": {"count": 2, "summary": "Summary", "path": "/tutorial"},
        }
        self.manifest_path.write_text(json.dumps(updated), encoding="utf-8")

        workspace_page = service.workspace_page()
        self.assertEqual(workspace_page.workspace["projects"][0]["slug"], "proj")

        persisted_project_page = service.project_page("proj")
        self.assertIsNotNone(persisted_project_page)
        assert persisted_project_page is not None
        self.assertEqual(persisted_project_page.project["name"], "Project")
        self.assertEqual(persisted_project_page.manuscript["slug"], "ms")


if __name__ == "__main__":
    unittest.main()
