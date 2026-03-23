from __future__ import annotations

import unittest

from app.runtime_models import FigureDraftRecord, ProjectRecord


class RuntimeModelTest(unittest.TestCase):
    def test_record_round_trip_preserves_declared_and_extra_fields(self) -> None:
        record = ProjectRecord.from_payload(
            {
                "slug": "demo-project",
                "name": "Demo Project",
                "status": "In review",
                "summary": "Seeded summary.",
                "custom_flag": "kept",
            }
        )

        payload = record.to_payload()

        self.assertEqual(payload["slug"], "demo-project")
        self.assertEqual(payload["custom_flag"], "kept")

    def test_record_merge_updates_payload_without_losing_extras(self) -> None:
        figure = FigureDraftRecord.from_payload(
            {
                "slug": "demo-figure",
                "title": "Demo Figure",
                "status": "Ready",
                "version": "v3",
                "analysis_notes": "Keep me",
            }
        )

        updated = figure.merged({"status": "Locked", "version": "v4"})
        payload = updated.to_payload()

        self.assertEqual(payload["status"], "Locked")
        self.assertEqual(payload["version"], "v4")
        self.assertEqual(payload["analysis_notes"], "Keep me")


if __name__ == "__main__":
    unittest.main()
