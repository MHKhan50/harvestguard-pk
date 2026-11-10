"""End-to-end temporal experiment runner."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Dict, List, Sequence, Union

from .data import read_panel_csv
from .features import FEATURE_NAMES, build_supervised_rows
from .metrics import classification_metrics, group_bootstrap_rmse_difference, regression_metrics
from .model import RidgeRegressor, conformal_radius


def _write_csv(path: Path, rows: Sequence[Dict[str, object]], fieldnames: Sequence[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        writer.writerows(rows)


def run_experiment(input_csv: Union[str, Path], output_dir: Union[str, Path], alpha: float = 0.10, seed: int = 17) -> Dict[str, object]:
    panel = read_panel_csv(input_csv)
    examples = build_supervised_rows(panel)
    train = [row for row in examples if int(row["target_year"]) <= 2015]
    calibration = [row for row in examples if 2016 <= int(row["target_year"]) <= 2019]
    test = [row for row in examples if 2020 <= int(row["target_year"]) <= 2024]
    if min(len(train), len(calibration), len(test)) == 0:
        raise ValueError(
            "Insufficient temporal coverage for fixed protocol: train<=2015 ({}), calibration=2016-2019 ({}), test=2020-2024 ({})."
            .format(len(train), len(calibration), len(test))
        )

    model = RidgeRegressor(alpha=1.0).fit(
        [row["features"] for row in train],  # type: ignore[list-item]
        [float(row["target_log"]) for row in train],
    )
    calibration_predictions = model.predict([row["features"] for row in calibration])  # type: ignore[list-item]
    radius = conformal_radius(
        [float(row["target_log"]) for row in calibration], calibration_predictions, alpha=alpha
    )
    ridge_predictions = model.predict([row["features"] for row in test])  # type: ignore[list-item]
    actual_log = [float(row["target_log"]) for row in test]
    persistence_log = [float(row["features"][0]) for row in test]  # type: ignore[index]
    rolling_median_log = [float(row["features"][2]) for row in test]  # type: ignore[index]
    actual_yield = [float(row["target_yield"]) for row in test]
    ridge_yield = [math.exp(value) for value in ridge_predictions]

    shock_actual = []
    shock_predicted = []
    prediction_rows = []
    for index, row in enumerate(test):
        threshold = 0.85 * float(row["previous_median_yield"])
        actual_shock = float(row["target_yield"]) <= threshold
        predicted_shock = ridge_yield[index] <= threshold
        shock_actual.append(actual_shock)
        shock_predicted.append(predicted_shock)
        prediction_rows.append({
            "district_code": row["district_code"],
            "district": row["district"],
            "province": row["province"],
            "crop_id": row["crop_id"],
            "crop": row["crop"],
            "fy": row["fy"],
            "target_year": row["target_year"],
            "actual_yield_t_per_ha": "{:.8f}".format(float(row["target_yield"])),
            "persistence_yield_t_per_ha": "{:.8f}".format(math.exp(persistence_log[index])),
            "rolling_median_yield_t_per_ha": "{:.8f}".format(math.exp(rolling_median_log[index])),
            "ridge_yield_t_per_ha": "{:.8f}".format(ridge_yield[index]),
            "conformal_lower_t_per_ha": "{:.8f}".format(math.exp(ridge_predictions[index] - radius)),
            "conformal_upper_t_per_ha": "{:.8f}".format(math.exp(ridge_predictions[index] + radius)),
            "shock_threshold_t_per_ha": "{:.8f}".format(threshold),
            "actual_shock": int(actual_shock),
            "predicted_shock": int(predicted_shock),
        })

    ridge_log_metrics = regression_metrics(actual_log, ridge_predictions)
    persistence_metrics = regression_metrics(actual_log, persistence_log)
    rolling_metrics = regression_metrics(actual_log, rolling_median_log)
    coverage = sum(abs(actual_log[i] - ridge_predictions[i]) <= radius for i in range(len(test))) / len(test)
    interval = {
        "nominal_coverage": 1.0 - alpha,
        "empirical_test_coverage": coverage,
        "mean_width_log_scale": 2.0 * radius,
        "calibration_radius_log_scale": radius,
    }
    metrics: Dict[str, object] = {
        "protocol": "train<=2015; calibration=2016-2019; test=2020-2024",
        "alpha": alpha,
        "sample_counts": {"panel_rows_after_validation": len(panel), "supervised_examples": len(examples), "train": len(train), "calibration": len(calibration), "test": len(test)},
        "forecast_log_scale": {
            "persistence": persistence_metrics,
            "rolling_median": rolling_metrics,
            "pooled_ridge": ridge_log_metrics,
        },
        "pooled_ridge_yield_scale_rmse_t_per_ha": regression_metrics(actual_yield, ridge_yield)["rmse"],
        "conformal_interval": interval,
        "yield_shock": classification_metrics(shock_actual, shock_predicted),
        "ridge_minus_rolling_median_rmse_group_bootstrap_95pct": group_bootstrap_rmse_difference(test, ridge_predictions, rolling_median_log, seed=seed),
        "feature_names": FEATURE_NAMES,
        "interpretation": "Scores depend on the supplied input. Synthetic-input results are software smoke tests only, not empirical Pakistan findings.",
    }

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "metrics.json").open("w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2, sort_keys=True)
        handle.write("\n")
    prediction_fields = list(prediction_rows[0].keys())
    _write_csv(output / "test_predictions.csv", prediction_rows, prediction_fields)
    metadata = {
        "input_csv": str(Path(input_csv)),
        "alpha": alpha,
        "seed": seed,
        "protocol": metrics["protocol"],
        "feature_names": FEATURE_NAMES,
        "data_status": "input-dependent; inspect source provenance before treating results as official-data evidence",
    }
    with (output / "run_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return metrics
