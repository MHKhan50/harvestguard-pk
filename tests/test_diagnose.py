import json
import tempfile
import unittest
from pathlib import Path

from harvestguard_pk.diagnose import _age_bucket, run_diagnose, series_age
from harvestguard_pk.shift import run_shift
from harvestguard_pk.synthetic import generate_synthetic_panel


class DiagnoseTests(unittest.TestCase):
    def test_series_age_counts_only_earlier_years(self):
        panel = [{"district_code": "1", "crop_id": "2", "year": y} for y in (2000, 2001, 2003)]
        examples = [{"group_id": "1|2", "target_year": 2003}, {"group_id": "1|2", "target_year": 2001}]
        self.assertEqual(series_age(panel, examples), [2, 1])
        self.assertEqual(_age_bucket(4), "3-5")
        self.assertEqual(_age_bucket(30), "21+")

    def test_pooled_methods_match_shift_and_outputs_written(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            panel = generate_synthetic_panel(root / "panel.csv", seed=17, districts=8)
            shift = run_shift(panel, root / "shift")
            diag = run_diagnose(panel, root / "diag")
            overall = diag["mondrian"]["overall"]
            self.assertAlmostEqual(overall["pooled_fixed"]["coverage"], shift["coverage"]["overall"]["fixed"]["coverage"], places=3)
            self.assertAlmostEqual(overall["pooled_rolling4"]["coverage"], shift["coverage"]["overall"]["rolling4"]["coverage"], places=3)
            self.assertTrue(json.loads((root / "diag" / "diagnose_results.json").read_text())["exploratory"])
            self.assertTrue((root / "diag" / "diagnose_report.md").exists())


if __name__ == "__main__":
    unittest.main()
