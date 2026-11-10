import unittest

from harvestguard_pk.features import FEATURE_NAMES, build_supervised_rows


class FeatureTests(unittest.TestCase):
    def _rows(self):
        rows = []
        for year, value in [(2000, 2.0), (2001, 2.2), (2002, 2.1), (2003, 99.0)]:
            rows.append({
                "district_code": "001", "district": "A", "province": "Punjab",
                "crop_id": "1", "crop": "Wheat", "fy": "{}-{:02d}".format(year, (year + 1) % 100),
                "year": year, "area_000ha": 10.0, "production_000t": 10.0 * value,
                "yield_t_per_ha": value,
            })
        return rows

    def test_features_are_lagged(self):
        examples = build_supervised_rows(self._rows())
        self.assertEqual(len(examples), 1)
        self.assertEqual(examples[0]["target_year"], 2003)
        # The 2003 target of 99 cannot appear in any feature.
        self.assertAlmostEqual(examples[0]["features"][0], __import__("math").log(2.1))
        self.assertEqual(len(examples[0]["features"]), len(FEATURE_NAMES))

    def test_same_year_rows_do_not_leak_into_aggregate(self):
        rows = self._rows()[:3]
        district_b_history = []
        for original in rows:
            copy = dict(original)
            copy["district_code"] = "002"
            copy["district"] = "B"
            copy["yield_t_per_ha"] = float(original["yield_t_per_ha"]) * 1.1
            copy["production_000t"] = 10.0 * copy["yield_t_per_ha"]
            district_b_history.append(copy)
        rows.extend(district_b_history)
        target_a = dict(self._rows()[-1])
        target_b = dict(target_a)
        target_b["district_code"] = "002"
        target_b["district"] = "B"
        target_b["yield_t_per_ha"] = 100.0
        target_b["production_000t"] = 1000.0
        rows.extend([target_a, target_b])
        # Need the first district's 2003 sample to use only prior years; same-year
        # values from either district must not alter its province-crop feature.
        examples = build_supervised_rows(rows)
        self.assertEqual(len(examples), 2)
        self.assertAlmostEqual(examples[0]["features"][5], examples[1]["features"][5])
