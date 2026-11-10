import unittest

from harvestguard_pk.model import RidgeRegressor, conformal_radius


class ModelTests(unittest.TestCase):
    def test_ridge_fits_linear_signal(self):
        x = [[float(i), float(i % 2)] for i in range(1, 20)]
        y = [2.0 + 3.0 * row[0] - 0.5 * row[1] for row in x]
        model = RidgeRegressor(alpha=1e-6).fit(x, y)
        predictions = model.predict(x)
        self.assertLess(max(abs(a - b) for a, b in zip(y, predictions)), 1e-3)

    def test_predict_before_fit_fails(self):
        with self.assertRaises(RuntimeError):
            RidgeRegressor().predict([[1.0]])

    def test_conformal_radius(self):
        radius = conformal_radius([1, 2, 3, 4], [1, 2, 2, 2], alpha=0.25)
        self.assertEqual(radius, 2.0)

    def test_invalid_alpha_fails(self):
        with self.assertRaises(ValueError):
            conformal_radius([1], [1], alpha=1.0)
