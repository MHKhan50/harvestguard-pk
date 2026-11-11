import tempfile
import unittest
from pathlib import Path

from harvestguard_pk.area import area_trend, run_area
from harvestguard_pk.synthetic import generate_synthetic_panel


def _row(district, province, crop, year, area):
    return {"district": district, "province": province, "crop": crop, "year": year, "area_000ha": area}


class AreaTests(unittest.TestCase):
    def test_change_percent_and_case_merge(self):
        panel = [_row("Bahawalnagar", "Punjab", "Cotton", y, 100.0) for y in range(2011, 2016)]
        panel += [_row("Bahawalnagar", "Punjab", "cotton", y, 50.0) for y in range(2020, 2025)]
        panel += [_row("Multan", "Punjab", "Cotton", y, 10.0) for y in range(2011, 2025)]
        result = area_trend(panel, "bahawal", ["Cotton"])
        self.assertEqual(result["district"], "Bahawalnagar")
        self.assertEqual(result["summary"]["cotton"]["district"]["change_percent"], -50.0)
        self.assertEqual(result["summary"]["cotton"]["province"]["change_percent"], round(100 * (60 - 110) / 110, 1))

    def test_ambiguous_district_rejected(self):
        panel = [_row("Bahawalnagar", "Punjab", "Cotton", 2012, 1.0), _row("Bahawalpur", "Punjab", "Cotton", 2012, 1.0)]
        with self.assertRaises(ValueError):
            area_trend(panel, "bahawal", ["Cotton"])

    def test_end_to_end(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            panel = generate_synthetic_panel(root / "panel.csv", seed=1, districts=4)
            run_area(panel, root / "out", "Synthetic District 01", ["Cotton", "Wheat"])
            self.assertTrue((root / "out" / "area_report.md").exists())


if __name__ == "__main__":
    unittest.main()
