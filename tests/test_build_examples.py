from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "generated" / "use_cases.json"


class BuildExamplesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, "scripts/build_examples.py"], cwd=ROOT, check=True)

    def test_manifest_contains_twenty_use_cases(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(manifest["product_name"], "AssayAtlas")
        self.assertEqual(len(manifest["use_cases"]), 20)

    def test_expected_chart_assets_exist(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        for item in manifest["use_cases"]:
            chart_path = ROOT / "app" / "static" / item["chart_path"]
            self.assertTrue(chart_path.exists(), msg=f"Missing chart asset for {item['slug']}")
            for rel_path in item["publication_assets"].values():
                self.assertTrue((ROOT / rel_path).exists(), msg=f"Missing publication asset for {item['slug']}: {rel_path}")


if __name__ == "__main__":
    unittest.main()
