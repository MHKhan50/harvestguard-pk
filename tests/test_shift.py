import json
import tempfile
import unittest
from pathlib import Path

from harvestguard_pk.data import read_panel_csv
from harvestguard_pk.experiment import run_experiment
from harvestguard_pk.shift import METHODS, clean_panel, quantile_radius, run_shift
from harvestguard_pk.synthetic import generate_synthetic_panel


def _row(code, crop_id, crop, year, y=2.0):
    return {"district_code": code, "district": code, "province": "Punjab", "crop_id": crop_id, "crop": crop,
            "fy": "{}-{:02d}".format(year, (year + 1) % 100), "year": year,
            "area_000ha": 10.0, "production_000t": 10.0 * y, "yield_t_per_ha": y}


class CleaningTests(unittest.TestCase):
    def test_case_merge_and_aggregate_exclusion(self):
        rows = [_row("001", "1", "Potato", 2000), _row("001", "1", "Potato", 2001),
                _row("002", "9", "potato", 2000),
                _row("001", "9", "potato", 2001, y=3.0),       # overlaps dominant id 1
                _row("001", "5", "Fodders Total", 2000), _row("001", "6", "Other Rabi Vegetables", 2000)]
        cleaned, summary = clean_panel(rows)
        self.assertEqual(summary["aggregate_rows_excluded"], 2)
        self.assertEqual(summary["overlapping_rows_dropped"], 1)
        self.assertEqual({r["crop_id"] for r in cleaned}, {"1"})
        self.assertEqual(len(cleaned), 3)
        kept_2001 = [r for r in cleaned if r["district_code"] == "001" and r["year"] == 2001][0]
        self.assertEqual(kept_2001["yield_t_per_ha"], 2.0)

    def test_quantile_radius_edges(self):
        self.assertEqual(quantile_radius([0.1, 0.2, 0.3], 0.0), 0.3)
        self.assertEqual(quantile_radius([0.1, 0.2, 0.3], 1.0), 0.0)
        with self.assertRaises(ValueError):
            quantile_radius([], 0.1)


class ShiftEndToEndTests(unittest.TestCase):
    def test_fixed_method_matches_main_run(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            panel = generate_synthetic_panel(root / "panel.csv", seed=17, districts=8)
            main = run_experiment(panel, root / "main")
            shift = run_shift(panel, root / "shift", clean=False)
            self.assertAlmostEqual(shift["coverage"]["overall"]["fixed"]["coverage"],
                                   main["conformal_interval"]["empirical_test_coverage"], places=3)
            self.assertAlmostEqual(shift["forecast"]["pooled_ridge"]["rmse"],
                                   main["forecast_log_scale"]["pooled_ridge"]["rmse"], places=9)
            self.assertEqual(len(shift["coverage_by_year"]), 5)
            loaded = json.loads((root / "shift" / "shift_results.json").read_text())
            self.assertEqual(loaded["methods"], list(METHODS))
            self.assertTrue((root / "shift" / "shift_report.md").exists())

    def test_cli_shift_with_cleaning(self):
        from harvestguard_pk.cli import main
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            panel = generate_synthetic_panel(root / "panel.csv", seed=3, districts=6)
            main(["shift", "--input", str(panel), "--output-dir", str(root / "out")])
            result = json.loads((root / "out" / "shift_results.json").read_text())
            self.assertTrue(result["cleaned"])
            self.assertEqual(result["cleaning"]["rows_in"], len(read_panel_csv(panel)))


if __name__ == "__main__":
    unittest.main()
