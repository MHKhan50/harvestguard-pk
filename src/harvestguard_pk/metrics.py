"""Forecast, interval and yield-shock evaluation metrics."""
from __future__ import annotations

import math
import random
from collections import defaultdict
from typing import Dict, List, Sequence


def regression_metrics(actual: Sequence[float], predicted: Sequence[float]) -> Dict[str, float]:
    if not actual or len(actual) != len(predicted):
        raise ValueError("actual and predicted must be non-empty and equal length")
    errors = [float(y) - float(yhat) for y, yhat in zip(actual, predicted)]
    return {
        "rmse": math.sqrt(sum(error * error for error in errors) / len(errors)),
        "mae": sum(abs(error) for error in errors) / len(errors),
    }


def classification_metrics(actual: Sequence[bool], predicted: Sequence[bool]) -> Dict[str, float]:
    if not actual or len(actual) != len(predicted):
        raise ValueError("actual and predicted labels must be non-empty and equal length")
    tp = sum(1 for a, p in zip(actual, predicted) if a and p)
    fp = sum(1 for a, p in zip(actual, predicted) if not a and p)
    fn = sum(1 for a, p in zip(actual, predicted) if a and not p)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "alert_rate": sum(bool(value) for value in predicted) / len(predicted),
        "positive_rate": sum(bool(value) for value in actual) / len(actual),
    }


def group_bootstrap_rmse_difference(
    rows: Sequence[Dict[str, object]],
    ridge_predictions: Sequence[float],
    baseline_predictions: Sequence[float],
    seed: int = 17,
    replicates: int = 300,
) -> Dict[str, object]:
    """Percentile interval for RMSE(ridge)-RMSE(baseline), resampling groups."""
    if len(rows) != len(ridge_predictions) or len(rows) != len(baseline_predictions) or not rows:
        raise ValueError("rows and prediction arrays must have equal non-zero length")
    grouped = defaultdict(list)
    for index, row in enumerate(rows):
        grouped[str(row["group_id"])].append(index)
    groups = sorted(grouped)
    if len(groups) < 2:
        return {"groups": len(groups), "replicates": 0, "ci95_low": None, "ci95_high": None}
    rng = random.Random(seed)
    differences = []
    for _ in range(replicates):
        sampled = [rng.choice(groups) for _ in groups]
        indices = [index for group in sampled for index in grouped[group]]
        ridge_rmse = math.sqrt(sum((float(rows[i]["target_log"]) - ridge_predictions[i]) ** 2 for i in indices) / len(indices))
        baseline_rmse = math.sqrt(sum((float(rows[i]["target_log"]) - baseline_predictions[i]) ** 2 for i in indices) / len(indices))
        differences.append(ridge_rmse - baseline_rmse)
    differences.sort()
    low = differences[int(0.025 * (len(differences) - 1))]
    high = differences[int(0.975 * (len(differences) - 1))]
    return {"groups": len(groups), "replicates": replicates, "ci95_low": low, "ci95_high": high}
