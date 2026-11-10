import csv
import tempfile
import unittest
from pathlib import Path

from harvestguard_pk.data import parse_fiscal_year, read_panel_csv


class DataTests(unittest.TestCase):
    def test_parse_fiscal_year(self):
        self.assertEqual(parse_fiscal_year("2024-25"), 2024)
        self.assertEqual(parse_fiscal_year("2023-2024"), 2023)

    def test_invalid_fiscal_year(self):
        with self.assertRaises(ValueError):
            parse_fiscal_year("FY24")

    def test_read_panel_filters_unlabelled_and_nonpositive(self):
        fields = ["district_code", "district", "province", "crop_id", "crop", "fy", "area_000ha", "production_000t", "yield_t_per_ha"]
        rows = [
            ["001", "A", "Punjab", "1", "Wheat", "2000-01", "10", "20", "2"],
            ["001", "A", "Punjab", "124", "Unnamed crop (portal id 124)", "2000-01", "10", "20", "2"],
            ["002", "B", "Sindh", "1", "Wheat", "2000-01", "0", "0", "0"],
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "panel.csv"
            with path.open("w", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(fields)
                writer.writerows(rows)
            panel = read_panel_csv(path)
        self.assertEqual(len(panel), 1)
        self.assertEqual(panel[0]["year"], 2000)

    def test_duplicate_panel_key_fails(self):
        fields = ["district_code", "district", "province", "crop_id", "crop", "fy", "area_000ha", "production_000t", "yield_t_per_ha"]
        row = ["001", "A", "Punjab", "1", "Wheat", "2000-01", "10", "20", "2"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "panel.csv"
            with path.open("w", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(fields)
                writer.writerow(row)
                writer.writerow(row)
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                read_panel_csv(path)
