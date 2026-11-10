"""Small dependency-free ridge regressor and split-conformal calibration."""
from __future__ import annotations

import math
import statistics
from typing import List, Sequence


def _solve_linear_system(matrix: List[List[float]], vector: List[float]) -> List[float]:
    size = len(vector)
    augmented = [list(matrix[row]) + [vector[row]] for row in range(size)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-12:
            raise ValueError("Singular ridge system; increase regularization")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        for index in range(column, size + 1):
            augmented[column][index] /= divisor
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            for index in range(column, size + 1):
                augmented[row][index] -= factor * augmented[column][index]
    return [augmented[row][size] for row in range(size)]


class RidgeRegressor:
    def __init__(self, alpha: float = 1.0) -> None:
        if alpha <= 0:
            raise ValueError("alpha must be positive")
        self.alpha = float(alpha)
        self.means: List[float] = []
        self.scales: List[float] = []
        self.coefficients: List[float] = []

    def fit(self, features: Sequence[Sequence[float]], targets: Sequence[float]) -> "RidgeRegressor":
        if not features or len(features) != len(targets):
            raise ValueError("features and targets must be non-empty and have equal length")
        width = len(features[0])
        if width == 0 or any(len(row) != width for row in features):
            raise ValueError("feature matrix must be rectangular and non-empty")
        self.means = [statistics.mean(float(row[col]) for row in features) for col in range(width)]
        self.scales = []
        for col in range(width):
            variance = statistics.mean((float(row[col]) - self.means[col]) ** 2 for row in features)
            scale = math.sqrt(variance)
            self.scales.append(scale if scale > 1e-12 else 1.0)

        design = [[1.0] + [(float(value) - self.means[col]) / self.scales[col] for col, value in enumerate(row)] for row in features]
        dimension = width + 1
        gram = [[0.0] * dimension for _ in range(dimension)]
        cross = [0.0] * dimension
        for row, target in zip(design, targets):
            for i in range(dimension):
                cross[i] += row[i] * float(target)
                for j in range(dimension):
                    gram[i][j] += row[i] * row[j]
        for index in range(1, dimension):
            gram[index][index] += self.alpha
        self.coefficients = _solve_linear_system(gram, cross)
        return self

    def predict(self, features: Sequence[Sequence[float]]) -> List[float]:
        if not self.coefficients:
            raise RuntimeError("model is not fitted")
        predictions = []
        for row in features:
            if len(row) != len(self.means):
                raise ValueError("feature width does not match fitted model")
            transformed = [1.0] + [(float(value) - self.means[col]) / self.scales[col] for col, value in enumerate(row)]
            predictions.append(sum(weight * value for weight, value in zip(self.coefficients, transformed)))
        return predictions


def conformal_radius(actual: Sequence[float], predicted: Sequence[float], alpha: float = 0.10) -> float:
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    if not actual or len(actual) != len(predicted):
        raise ValueError("actual and predicted must be non-empty and have equal length")
    residuals = sorted(abs(float(y) - float(yhat)) for y, yhat in zip(actual, predicted))
    rank = math.ceil((len(residuals) + 1) * (1.0 - alpha))
    index = min(max(rank - 1, 0), len(residuals) - 1)
    return residuals[index]
