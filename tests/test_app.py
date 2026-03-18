from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from app import create_app

ROOT = Path(__file__).resolve().parents[1]


class AppRoutesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, "scripts/build_examples.py"], cwd=ROOT, check=True)
        cls.client = create_app().test_client()

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

    def test_use_case_renders(self) -> None:
        response = self.client.get("/use-cases/two-group-supplement-comparison")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Two-Group Supplement Comparison", response.data)
        self.assertIn(b"Open Figure Draft", response.data)

    def test_project_route_renders(self) -> None:
        response = self.client.get("/projects/nutrient-response-atlas")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Nutrient Response Atlas", response.data)
        self.assertIn(b"Figure Workbench", response.data)

    def test_dataset_route_renders(self) -> None:
        response = self.client.get("/datasets/toothgrowth")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ToothGrowth.csv", response.data)
        self.assertIn(b"Linked projects", response.data)

    def test_manuscript_route_renders(self) -> None:
        response = self.client.get("/manuscripts/nutrient-response-atlas-manuscript")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Dietary Supplementation Reshapes Growth Response Dynamics", response.data)
        self.assertIn(b"Section checklist", response.data)

    def test_figure_route_renders(self) -> None:
        response = self.client.get("/figures/publication-figure-board")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Publication Figure Board", response.data)
        self.assertIn(b"Open Tutorial Recipe", response.data)

    def test_healthz(self) -> None:
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'"ok":true', response.data.replace(b" ", b""))


if __name__ == "__main__":
    unittest.main()
