"""Synthetic-only E6 metadata tests; never opens a real sequence CSV."""
import csv
from datetime import date
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts.e6_snapshot_deployment_geometry import (
    REQUIRED, SOURCES, _year, audit_deployments,
)


class TestE6SnapshotMetadata(unittest.TestCase):
    def test_year_parsing(self):
        self.assertEqual(_year("2022", "2022-09-01"), 2022)
        self.assertEqual(_year("", "2024-10-01"), 2024)

    def test_digest_and_metadata_geometry(self):
        with TemporaryDirectory() as folder:
            file = Path(folder) / "deployments.csv"
            with file.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=sorted(REQUIRED | {"Year"}))
                writer.writeheader()
                for arr, dev, lat, lon in (
                    ("a", "Wild", 38, -90),
                    ("b", "Urban", 39, -91),
                    ("c", "Rural", 42, -82),
                    ("d", "Suburban", 44, -88),
                ):
                    writer.writerow({
                        "Year": 2022, "Camera_Trap_Array": arr,
                        "Deployment_ID": "d-"+arr, "Site_Name": "site-"+arr,
                        "Development_Level": dev,
                        "Latitude": lat, "Longitude": lon,
                        "Start_Date": "2022-09-01", "End_Date": "2022-10-31",
                    })
            digest = hashlib.sha256(file.read_bytes()).hexdigest()
            with patch.dict(SOURCES["history"], {"sha256": digest}):
                summary = audit_deployments(file, "history")
            self.assertEqual(summary["rows"], 4)
            self.assertEqual(summary["qualified_development_groups"], {"high": 2, "low": 2})
            self.assertEqual(summary["latitude_longitude_grid_cells_with_both_groups"], 2)
            self.assertTrue(summary["no_biological_sequence_records_opened"])

    def test_exact_source_digest_is_required(self):
        with TemporaryDirectory() as folder:
            file = Path(folder) / "bad.csv"
            file.write_text("not the official source", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                audit_deployments(file, "history")

    def test_all_required_columns_are_exposed_by_contract(self):
        self.assertIn("Development_Level", REQUIRED)
        self.assertIn("Start_Date", REQUIRED)
        self.assertIn("Camera_Trap_Array", REQUIRED)
        self.assertIn("Site_Name", REQUIRED)
        self.assertNotIn("Species", REQUIRED)
        self.assertNotIn("Sequence_ID", REQUIRED)
        self.assertEqual(SOURCES["history"]["file_id"], 4016828)
        self.assertEqual(SOURCES["holdout_2024"]["file_id"], 4788613)


if __name__ == "__main__":
    unittest.main()
