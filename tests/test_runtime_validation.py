from __future__ import annotations

import unittest

from app.runtime_validation import (
    filter_allowed_fields,
    normalize_export_job_create_payload,
    normalize_figure_update_payload,
    normalize_project_create_payload,
    normalize_project_update_payload,
)


class RuntimeValidationTest(unittest.TestCase):
    def test_filter_allowed_fields_drops_unknown_keys(self) -> None:
        filtered = filter_allowed_fields(
            {"name": "Atlas", "status": "Draft", "ignore": "x"},
            {"name", "status"},
        )

        self.assertEqual(filtered, {"name": "Atlas", "status": "Draft"})

    def test_project_create_normalizes_optional_strings(self) -> None:
        payload = normalize_project_create_payload(
            {
                "name": " Immune Signaling Atlas ",
                "owner": " Maya Singh ",
                "status": " Draft setup ",
                "summary": "   ",
            }
        )

        self.assertEqual(payload["name"], "Immune Signaling Atlas")
        self.assertEqual(payload["owner"], "Maya Singh")
        self.assertEqual(payload["status"], "Draft setup")
        self.assertNotIn("summary", payload)

    def test_project_update_rejects_blank_name(self) -> None:
        with self.assertRaisesRegex(ValueError, "Project name must be a non-empty string"):
            normalize_project_update_payload({"name": "   "})

    def test_figure_update_rejects_blank_summary(self) -> None:
        with self.assertRaisesRegex(ValueError, "Figure summary must be a non-empty string"):
            normalize_figure_update_payload({"summary": "   "})

    def test_export_job_create_rejects_blank_required_field(self) -> None:
        with self.assertRaisesRegex(ValueError, "Export job title must be a non-empty string"):
            normalize_export_job_create_payload(
                {"title": "   ", "detail": "TIFF bundle", "path": "/figures/demo-figure"}
            )


if __name__ == "__main__":
    unittest.main()
