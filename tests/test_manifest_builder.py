from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_examples import (  # noqa: E402
    CHART_DIR,
    GENERATED_DIR,
    ManifestBuilder,
    UseCaseSpec,
    apply_style,
    build_two_group_supplement,
    ensure_dirs,
    vendor_rdataset,
)


def fake_publication_assets(item: dict) -> dict:
    base = item["slug"]
    return {
        "publication_assets": {
            "bundle": f"data/generated/publication/{base}.zip",
            "svg": f"data/generated/publication/{base}.svg",
            "pdf": f"data/generated/publication/{base}.pdf",
            "png": f"data/generated/publication/{base}.png",
            "tiff": f"data/generated/publication/{base}.tiff",
            "caption": f"data/generated/publication/{base}-caption.md",
            "methods": f"data/generated/publication/{base}-methods.md",
            "results": f"data/generated/publication/{base}-results.md",
            "checklist": f"data/generated/publication/{base}-checklist.md",
        },
        "caption_text": "Caption",
        "methods_text": "Methods",
        "results_text": "Results",
        "submission_checklist": ["Check"],
    }


class ManifestBuilderUnitTest(unittest.TestCase):
    def test_manifest_builder_supports_injected_registry(self) -> None:
        spec = UseCaseSpec(
            1,
            "synthetic-case",
            "Synthetic Case",
            "Synthetic",
            "Fake analysis",
            "Goal",
            ["Step 1", "Step 2", "Step 3", "Step 4", "Step 5"],
            "Notice",
            ["data/raw/synthetic.csv"],
            "Source",
            "fake_builder",
        )

        seen_titles: list[str] = []

        def fake_builder(item_spec: UseCaseSpec) -> dict:
            seen_titles.append(item_spec.title)
            return {
                "summary": "Synthetic summary",
                "key_metrics": ["Metric 1", "Metric 2"],
                "chart_path": "generated/charts/synthetic.png",
                "data_preview": [{"value": 1}],
                "input_files": item_spec.data_files,
                "generated_file": None,
            }

        builder = ManifestBuilder(
            specs=[spec],
            builder_registry={"fake_builder": fake_builder},
            tutorial_overrides={"synthetic-case": {"title": "Overridden Synthetic Case"}},
            dataset_vendors=(),
            environment_preparer=lambda vendors: None,
            publication_packager=fake_publication_assets,
            dataset_library_builder=lambda use_cases: [{"slug": "dataset", "path": use_cases[0]["data_files"][0]}],
            workspace_builder=lambda use_cases, datasets: {"projects": [], "datasets": datasets, "figure_drafts": use_cases},
        )

        manifest = builder.build_manifest()

        self.assertEqual(seen_titles, ["Overridden Synthetic Case"])
        self.assertEqual(manifest["product_name"], "AssayAtlas")
        self.assertEqual(manifest["use_cases"][0]["title"], "Overridden Synthetic Case")
        self.assertEqual(manifest["use_cases"][0]["publication_assets"]["bundle"], "data/generated/publication/synthetic-case.zip")
        self.assertEqual(manifest["workspace"]["datasets"][0]["slug"], "dataset")

    def test_real_builder_can_be_tested_without_full_manifest_generation(self) -> None:
        apply_style()
        ensure_dirs()
        vendor_rdataset("ToothGrowth")

        spec = UseCaseSpec(
            1,
            "two-group-supplement-comparison",
            "Two-Group Supplement Comparison",
            "Hypothesis Testing",
            "Welch t test + raw-point estimation plot",
            "Compare low-dose tooth growth by supplement and show every replicate.",
            ["1", "2", "3", "4", "5"],
            "Notice",
            ["data/raw/ToothGrowth.csv"],
            "ToothGrowth from the R datasets collection.",
            "build_two_group_supplement",
        )

        result = build_two_group_supplement(spec)

        self.assertIn("summary", result)
        self.assertGreaterEqual(len(result["key_metrics"]), 3)
        self.assertEqual(result["input_files"], ["data/raw/ToothGrowth.csv"])
        self.assertEqual(result["generated_file"], "data/generated/two-group-supplement-comparison.csv")
        self.assertTrue((CHART_DIR / "01-two-group-supplement-comparison.png").exists())
        self.assertTrue((GENERATED_DIR / "two-group-supplement-comparison.csv").exists())


if __name__ == "__main__":
    unittest.main()
