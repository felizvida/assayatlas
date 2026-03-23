from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from app import create_app
from app.content import ContentService
from app.runtime import PersistedWorkspaceRepository, WorkspaceService

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "generated" / "use_cases.json"


class AppRoutesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not MANIFEST_PATH.exists():
            subprocess.run([sys.executable, "scripts/build_examples.py"], cwd=ROOT, check=True)
        cls.temp_dir = tempfile.TemporaryDirectory()
        workspace_repo = PersistedWorkspaceRepository(Path(cls.temp_dir.name) / "assayatlas-test.db")
        workspace_service = WorkspaceService(repository=workspace_repo)
        content_service = ContentService(workspace_service=workspace_service)
        cls.client = create_app(content_service=content_service).test_client()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_dir.cleanup()

    def test_homepage_renders(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Turn experimental results into publication-ready figures", response.data)

    def test_workspace_renders(self) -> None:
        response = self.client.get("/workspace")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Project command center", response.data)
        self.assertIn(b"Active workspaces, not tutorial cards", response.data)

    def test_tutorial_renders(self) -> None:
        response = self.client.get("/tutorial")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Step-by-step onboarding with real data", response.data)

    def test_docs_render_as_html(self) -> None:
        response = self.client.get("/docs")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Readable docs inside the product", response.data)
        self.assertEqual(response.content_type.split(";")[0], "text/html")

    def test_doc_assets_render(self) -> None:
        response = self.client.get("/assets/screenshots/01-two-group-supplement-comparison.png")
        try:
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.content_type.startswith("image/"))
        finally:
            response.close()

    def test_favicon_route_renders(self) -> None:
        response = self.client.get("/favicon.ico")
        try:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type.split(";")[0], "image/svg+xml")
        finally:
            response.close()

    def test_download_blocks_repo_internal_files(self) -> None:
        response = self.client.get("/download/.git/config")
        self.assertEqual(response.status_code, 404)

    def test_download_allows_generated_manifest(self) -> None:
        response = self.client.get("/download/data/generated/use_cases.json")
        try:
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'"product_name"', response.data)
        finally:
            response.close()

    def test_use_case_renders(self) -> None:
        response = self.client.get("/use-cases/two-group-supplement-comparison")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Low-Dose Mineralization Rescue Assay", response.data)
        self.assertIn(b"Open Figure Draft", response.data)

    def test_project_route_renders(self) -> None:
        response = self.client.get("/projects/nutrient-response-atlas")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Nutrient Response Atlas", response.data)
        self.assertIn(b"Figure Workbench", response.data)
        self.assertIn(b"Project Editor", response.data)

    def test_dataset_route_renders(self) -> None:
        response = self.client.get("/datasets/toothgrowth")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ToothGrowth.csv", response.data)
        self.assertIn(b"Linked projects", response.data)
        self.assertIn(b"Dataset Editor", response.data)

    def test_manuscript_route_renders(self) -> None:
        response = self.client.get("/manuscripts/nutrient-response-atlas-manuscript")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Dietary Supplementation Reshapes Growth Response Dynamics", response.data)
        self.assertIn(b"Section checklist", response.data)
        self.assertIn(b"Packet Editor", response.data)

    def test_figure_route_renders(self) -> None:
        response = self.client.get("/figures/publication-figure-board")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Mechanism-of-Action Manuscript Board", response.data)
        self.assertIn(b"Open Tutorial Recipe", response.data)
        self.assertIn(b"Workspace Editor", response.data)

    def test_healthz(self) -> None:
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        compact = response.data.replace(b" ", b"")
        self.assertIn(b'"ok":true', compact)
        self.assertIn(b'"workspace_schema_version":2', compact)


if __name__ == "__main__":
    unittest.main()
