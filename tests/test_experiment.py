import json
import tempfile
import unittest
from pathlib import Path

from harvestguard_pk.experiment import run_experiment
from harvestguard_pk.synthetic import generate_synthetic_panel


class ExperimentTests(unittest.TestCase):
    def test_end_to_end_synthetic_smoke(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            panel = generate_synthetic_panel(root / "panel.csv", seed=17, districts=8)
            metrics = run_experiment(panel, root / "out", alpha=0.10, seed=17)
            self.assertGreater(metrics["sample_counts"]["train"], 0)
            self.assertGreater(metrics["sample_counts"]["calibration"], 0)
            self.assertGreater(metrics["sample_counts"]["test"], 0)
            self.assertTrue((root / "out" / "metrics.json").exists())
            self.assertTrue((root / "out" / "test_predictions.csv").exists())
            loaded = json.loads((root / "out" / "metrics.json").read_text())
            self.assertIn("conformal_interval", loaded)
            self.assertIn("yield_shock", loaded)
