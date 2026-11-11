"""Conformal coverage under temporal shift: cleaning, recalibration methods and reports.

The main ``run`` command keeps the fixed protocol (train <= 2015, calibrate
2016-2019, test 2020-2024). This module asks what happens to the 90% interval
year by year, and whether simple recalibration restores it. Every method uses
only data from years before the target year, as it would be available when the
forecast is made.

Methods (all on the log-yield scale, symmetric absolute-residual intervals):

* ``fixed``: ridge trained on <= 2015, radius from 2016-2019 residuals.
* ``rolling4``: same model, radius from the four years before the target year.
* ``expanding``: same model, radius from 2016 up to the year before the target.
* ``refit_rolling4``: ridge refitted on years <= t-5, radius from t-4..t-1.
* ``aci_g0.1`` / ``aci_g0.5``: fixed calibration set with the miscoverage level
  updated once per year, alpha_{t+1} = alpha_t + gamma * (alpha - miss_t), in
  the spirit of adaptive conformal inference (Gibbs and Candes, 2021,
  arXiv:2106.00170). Both gamma values are fixed in advance and both are reported.
"""
from __future__ import annotations

import json
import math
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

from .data import read_panel_csv
from .features import build_supervised_rows
from .metrics import classification_metrics, regression_metrics
from .model import RidgeRegressor

TEST_YEARS: Tuple[int, ...] = (2020, 2021, 2022, 2023, 2024)
TRAIN_MAX = 2015
CALIBRATION_YEARS: Tuple[int, ...] = (2016, 2017, 2018, 2019)
WINDOW = 4
ACI_GAMMAS: Tuple[float, ...] = (0.1, 0.5)
METHODS: Tuple[str, ...] = ("fixed", "rolling4", "expanding", "refit_rolling4") + tuple(
    "aci_g{:g}".format(g) for g in ACI_GAMMAS)
AGGREGATE_PATTERN = re.compile(r"\btotal\b|^other\b", re.IGNORECASE)
BOOTSTRAP_REPLICATES = 500


# ---------------------------------------------------------------- cleaning
def clean_panel(rows: Sequence[Dict[str, object]]) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    """Drop aggregate labels and merge crop labels that differ only by case or spacing.

    When two crop ids share a normalised label, every row takes the id and label of
    the id with most rows. If both ids report the same district and year, the row
    of the dominant id is kept and the other is dropped.
    """
    excluded = Counter(str(r["crop"]) for r in rows if AGGREGATE_PATTERN.search(str(r["crop"])))
    kept = [r for r in rows if not AGGREGATE_PATTERN.search(str(r["crop"]))]

    def norm(label: object) -> str:
        return " ".join(str(label).lower().split())

    ids_by_label: Dict[str, Counter] = defaultdict(Counter)
    label_of_id: Dict[str, str] = {}
    for r in kept:
        ids_by_label[norm(r["crop"])][str(r["crop_id"])] += 1
        label_of_id.setdefault(str(r["crop_id"]), str(r["crop"]))
    dominant: Dict[str, str] = {}
    merged: List[Dict[str, object]] = []
    for label, counts in ids_by_label.items():
        top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        for crop_id in counts:
            dominant[crop_id] = top
        if len(counts) > 1:
            merged.append({"normalised_label": label, "kept_id": top, "kept_label": label_of_id[top],
                           "merged": {cid: label_of_id[cid] for cid in counts if cid != top},
                           "rows_by_id": dict(counts)})

    out: Dict[Tuple[str, str, int], Dict[str, object]] = {}
    duplicates = 0
    for r in kept:
        cid = str(r["crop_id"])
        key = (str(r["district_code"]), dominant[cid], int(r["year"]))
        new = dict(r)
        new["crop_id"] = dominant[cid]
        new["crop"] = label_of_id[dominant[cid]]
        if key in out:
            duplicates += 1
            if cid != dominant[cid]:
                continue  # keep the dominant id's row
        out[key] = new
    cleaned = sorted(out.values(), key=lambda r: (int(r["year"]), str(r["district_code"]), str(r["crop_id"])))
    summary = {
        "rows_in": len(rows),
        "rows_out": len(cleaned),
        "aggregate_labels_excluded": dict(sorted(excluded.items())),
        "aggregate_rows_excluded": sum(excluded.values()),
        "case_merged_labels": merged,
        "overlapping_rows_dropped": duplicates,
        "crops_out": len({str(r["crop_id"]) for r in cleaned}),
    }
    return cleaned, summary


# ---------------------------------------------------------------- conformal helpers
def quantile_radius(residuals: Sequence[float], alpha: float) -> float:
    """Split-conformal radius; alpha <= 0 returns the largest residual, alpha >= 1 returns 0."""
    if not residuals:
        raise ValueError("no calibration residuals")
    ordered = sorted(residuals)
    if alpha >= 1:
        return 0.0
    rank = math.ceil((len(ordered) + 1) * (1.0 - max(alpha, 0.0)))
    return ordered[min(max(rank - 1, 0), len(ordered) - 1)]


def _fit(examples: Sequence[Dict[str, object]]) -> RidgeRegressor:
    return RidgeRegressor(alpha=1.0).fit([e["features"] for e in examples],  # type: ignore[misc]
                                         [float(e["target_log"]) for e in examples])


def _abs_residuals(model: RidgeRegressor, examples: Sequence[Dict[str, object]]) -> List[float]:
    if not examples:
        return []
    preds = model.predict([e["features"] for e in examples])  # type: ignore[misc]
    return [abs(float(e["target_log"]) - p) for e, p in zip(examples, preds)]


def _years(by_year: Dict[int, List[Dict[str, object]]], years: Sequence[int]) -> List[Dict[str, object]]:
    return [e for y in years for e in by_year.get(y, [])]


def group_bootstrap_mean(values: Sequence[float], groups: Sequence[str], seed: int,
                         replicates: int = BOOTSTRAP_REPLICATES) -> Tuple[float, float]:
    """95% percentile interval for a mean, resampling whole district-crop groups."""
    by_group: Dict[str, List[float]] = defaultdict(list)
    for v, g in zip(values, groups):
        by_group[g].append(v)
    keys = sorted(by_group)
    sums = [sum(by_group[k]) for k in keys]
    counts = [len(by_group[k]) for k in keys]
    rng = random.Random(seed)
    stats = []
    for _ in range(replicates):
        s = n = 0.0
        for _ in keys:
            i = rng.randrange(len(keys))
            s += sums[i]
            n += counts[i]
        stats.append(s / n)
    stats.sort()
    return stats[int(0.025 * (replicates - 1))], stats[int(0.975 * (replicates - 1))]


# ---------------------------------------------------------------- experiment
def evaluate_shift(examples: Sequence[Dict[str, object]], alpha: float = 0.10,
                   seed: int = 17) -> Tuple[Dict[str, object], List[Dict[str, object]]]:
    by_year: Dict[int, List[Dict[str, object]]] = defaultdict(list)
    for e in examples:
        by_year[int(e["target_year"])].append(e)
    if not all(by_year.get(y) for y in CALIBRATION_YEARS + TEST_YEARS):
        raise ValueError("every calibration and test year 2016-2024 needs examples")

    base = _fit([e for e in examples if int(e["target_year"]) <= TRAIN_MAX])
    base_res = {y: _abs_residuals(base, by_year.get(y, [])) for y in sorted(by_year) if y > TRAIN_MAX}
    fixed_cal = [r for y in CALIBRATION_YEARS for r in base_res[y]]
    aci_alpha = {g: alpha for g in ACI_GAMMAS}

    per_year: List[Dict[str, object]] = []
    hits: Dict[str, List[float]] = {m: [] for m in METHODS}
    widths: Dict[str, List[float]] = {m: [] for m in METHODS}
    groups: List[str] = []
    provinces: List[str] = []
    for t in TEST_YEARS:
        test = by_year[t]
        window = list(range(t - WINDOW, t))
        radii: Dict[str, float] = {
            "fixed": quantile_radius(fixed_cal, alpha),
            "rolling4": quantile_radius([r for y in window for r in base_res[y]], alpha),
            "expanding": quantile_radius([r for y in range(CALIBRATION_YEARS[0], t) for r in base_res[y]], alpha),
        }
        refit = _fit([e for e in examples if int(e["target_year"]) <= t - WINDOW - 1])
        refit_radius = quantile_radius(_abs_residuals(refit, _years(by_year, window)), alpha)
        for g in ACI_GAMMAS:
            radii["aci_g{:g}".format(g)] = quantile_radius(fixed_cal, aci_alpha[g])
        base_res_t = base_res[t]
        refit_res_t = _abs_residuals(refit, test)
        row: Dict[str, object] = {"target_year": t, "examples": len(test)}
        for m in METHODS:
            residuals = refit_res_t if m == "refit_rolling4" else base_res_t
            radius = refit_radius if m == "refit_rolling4" else radii[m]
            covered = [1.0 if r <= radius else 0.0 for r in residuals]
            hits[m].extend(covered)
            widths[m].extend([2.0 * radius] * len(covered))
            row[m] = {"coverage": round(sum(covered) / len(covered), 4), "width": round(2.0 * radius, 4)}
        for g in ACI_GAMMAS:
            name = "aci_g{:g}".format(g)
            row[name]["alpha_used"] = round(aci_alpha[g], 4)  # type: ignore[index]
            miss = 1.0 - row[name]["coverage"]  # type: ignore[index]
            aci_alpha[g] = aci_alpha[g] + g * (alpha - miss)
        groups.extend(str(e["group_id"]) for e in test)
        provinces.extend(str(e["province"]) for e in test)
        per_year.append(row)

    overall: Dict[str, Dict[str, float]] = {}
    for i, m in enumerate(METHODS):
        low, high = group_bootstrap_mean(hits[m], groups, seed + i)
        overall[m] = {"coverage": round(sum(hits[m]) / len(hits[m]), 4), "ci95_low": round(low, 4),
                      "ci95_high": round(high, 4), "mean_width": round(sum(widths[m]) / len(widths[m]), 4)}
    by_province: Dict[str, Dict[str, float]] = {}
    for p in sorted(set(provinces)):
        idx = [i for i, q in enumerate(provinces) if q == p]
        by_province[p] = {"examples": len(idx), **{m: round(sum(hits[m][i] for i in idx) / len(idx), 4)
                                                   for m in ("fixed", "rolling4", "refit_rolling4")}}
    return {"nominal_coverage": 1.0 - alpha, "test_examples": len(groups), "overall": overall,
            "by_province": by_province}, per_year


def forecast_table(examples: Sequence[Dict[str, object]]) -> Dict[str, object]:
    """Point-forecast and shock metrics for the fixed protocol (for the cleaned panel)."""
    train = [e for e in examples if int(e["target_year"]) <= TRAIN_MAX]
    test = [e for e in examples if int(e["target_year"]) in TEST_YEARS]
    ridge = _fit(train).predict([e["features"] for e in test])  # type: ignore[misc]
    actual = [float(e["target_log"]) for e in test]
    persistence = [float(e["features"][0]) for e in test]  # type: ignore[index]
    rolling = [float(e["features"][2]) for e in test]  # type: ignore[index]
    shock = [float(e["target_yield"]) <= 0.85 * float(e["previous_median_yield"]) for e in test]

    def alerts(pred_log: Sequence[float]) -> Dict[str, float]:
        return classification_metrics(shock, [math.exp(p) <= 0.85 * float(e["previous_median_yield"])
                                              for p, e in zip(pred_log, test)])

    return {"test_examples": len(test), "shock_rate": round(sum(shock) / len(shock), 4),
            "persistence": regression_metrics(actual, persistence),
            "rolling_median": regression_metrics(actual, rolling),
            "pooled_ridge": regression_metrics(actual, ridge),
            "shock_alerts_persistence": alerts(persistence), "shock_alerts_ridge": alerts(ridge)}


def markdown(cleaning: Optional[Dict[str, object]], forecast: Dict[str, object],
             overall: Dict[str, object], per_year: Sequence[Dict[str, object]]) -> str:
    lines = ["# Coverage under temporal shift", ""]
    if cleaning:
        lines += ["Cleaning: {rows_in} rows in, {rows_out} out; {aggregate_rows_excluded} aggregate rows excluded; "
                  "{overlapping_rows_dropped} overlapping rows dropped; {crops_out} crops.".format(**cleaning), ""]
    lines += ["## Point forecasts (train <= 2015, test 2020-2024, {} examples)".format(forecast["test_examples"]), "",
              "| Forecaster | RMSE (log) | MAE (log) |", "|---|---|---|"]
    for k in ("persistence", "rolling_median", "pooled_ridge"):
        lines.append("| {} | {:.4f} | {:.4f} |".format(k, forecast[k]["rmse"], forecast[k]["mae"]))  # type: ignore[index]
    sp, sr = forecast["shock_alerts_persistence"], forecast["shock_alerts_ridge"]
    lines += ["", "Shock rate {:.1%}. Alerts F1: persistence {:.3f} (P {:.3f}, R {:.3f}); ridge {:.3f} (P {:.3f}, R {:.3f}).".format(
        forecast["shock_rate"], sp["f1"], sp["precision"], sp["recall"], sr["f1"], sr["precision"], sr["recall"]),  # type: ignore[index]
        "", "## Interval coverage, nominal {:.0%}".format(overall["nominal_coverage"]), "",
        "| Method | Coverage | 95% CI (group bootstrap) | Mean width (log) |", "|---|---|---|---|"]
    for m in METHODS:
        o = overall["overall"][m]  # type: ignore[index]
        lines.append("| {} | {:.3f} | {:.3f} to {:.3f} | {:.3f} |".format(m, o["coverage"], o["ci95_low"], o["ci95_high"], o["mean_width"]))
    lines += ["", "## Coverage by target year", "", "| Year | n | " + " | ".join(METHODS) + " |",
              "|---|---|" + "---|" * len(METHODS)]
    for r in per_year:
        lines.append("| {} | {} | ".format(r["target_year"], r["examples"]) +
                     " | ".join("{:.3f}".format(r[m]["coverage"]) for m in METHODS) + " |")  # type: ignore[index]
    lines += ["", "## Coverage by province", "", "| Province | n | fixed | rolling4 | refit_rolling4 |", "|---|---|---|---|---|"]
    for p, v in overall["by_province"].items():  # type: ignore[union-attr]
        lines.append("| {} | {} | {:.3f} | {:.3f} | {:.3f} |".format(p, v["examples"], v["fixed"], v["rolling4"], v["refit_rolling4"]))
    return "\n".join(lines) + "\n"


def _plot(per_year: Sequence[Dict[str, object]], nominal: float, path: Path) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed; skipping the figure")
        return
    colours = {"fixed": "#8a94a8", "rolling4": "#2b5ce6", "expanding": "#7aa0f0", "refit_rolling4": "#0f1932",
               "aci_g0.1": "#c48a2a", "aci_g0.5": "#e0b04a"}
    years = [int(r["target_year"]) for r in per_year]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for m in METHODS:
        ax.plot(years, [r[m]["coverage"] for r in per_year], marker="o", color=colours.get(m), label=m)  # type: ignore[index]
    ax.axhline(nominal, color="#b33", linestyle="--", linewidth=1, label="nominal {:.0%}".format(nominal))
    ax.set_xticks(years)
    ax.set_xticklabels(["{}-{:02d}".format(y, (y + 1) % 100) for y in years])
    ax.set_ylabel("Share of test yields inside the interval")
    ax.set_title("Interval coverage by target year")
    ax.grid(alpha=0.3)
    ax.legend(frameon=False, fontsize=8, ncol=2)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def run_shift(input_csv: Union[str, Path], output_dir: Union[str, Path], alpha: float = 0.10,
              clean: bool = True, seed: int = 17) -> Dict[str, object]:
    panel = read_panel_csv(input_csv)
    cleaning: Optional[Dict[str, object]] = None
    if clean:
        panel, cleaning = clean_panel(panel)
    examples = build_supervised_rows(panel)
    overall, per_year = evaluate_shift(examples, alpha, seed)
    forecast = forecast_table(examples)
    result = {"input_csv": str(input_csv), "cleaned": clean, "alpha": alpha, "seed": seed,
              "methods": list(METHODS), "window_years": WINDOW, "aci_gammas": list(ACI_GAMMAS),
              "cleaning": cleaning, "forecast": forecast, "coverage": overall, "coverage_by_year": per_year}
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "shift_results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (out / "shift_report.md").write_text(markdown(cleaning, forecast, overall, per_year), encoding="utf-8")
    _plot(per_year, 1.0 - alpha, out / "figures" / "coverage_by_year.png")
    return result
