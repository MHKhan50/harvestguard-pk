"""Exploratory follow-up to the shift analysis (added after seeing its results).

Two questions:

1. Why does the fixed interval already under-cover in 2020-21, the first test
   year? Checked by comparing the calibration (2016-2019) and test (2020-2024)
   sets: share of examples by province and by series age (number of earlier
   observed years for that district-crop), and fixed-interval coverage within
   each of those groups.
2. Does a province-wise (Mondrian) conformal radius fix the province gap seen
   in the shift results? Compared with the pooled radius, for the fixed and the
   rolling four-year calibration. A province with fewer than ``MIN_GROUP``
   calibration residuals falls back to the pooled radius.

Same ridge model as the shift analysis (trained on target years <= 2015).
"""
from __future__ import annotations

import bisect
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Sequence, Tuple, Union

from .data import read_panel_csv
from .features import build_supervised_rows
from .shift import CALIBRATION_YEARS, TEST_YEARS, TRAIN_MAX, WINDOW, _abs_residuals, _fit, clean_panel, \
    group_bootstrap_mean, quantile_radius

AGE_BUCKETS: Tuple[Tuple[str, int, int], ...] = (("3-5", 3, 5), ("6-10", 6, 10), ("11-20", 11, 20), ("21+", 21, 10 ** 6))
MIN_GROUP = 50


def _age_bucket(age: int) -> str:
    for name, low, high in AGE_BUCKETS:
        if low <= age <= high:
            return name
    return "<3"


def series_age(panel: Sequence[Dict[str, object]], examples: Sequence[Dict[str, object]]) -> List[int]:
    """Number of observed years before the target year for each example's district-crop."""
    years: Dict[str, List[int]] = defaultdict(list)
    for r in panel:
        years["{}|{}".format(r["district_code"], r["crop_id"])].append(int(r["year"]))
    for v in years.values():
        v.sort()
    return [bisect.bisect_left(years[str(e["group_id"])], int(e["target_year"])) for e in examples]


def _share_and_cover(keys: Sequence[str], covered: Sequence[float]) -> Dict[str, Dict[str, float]]:
    n: Dict[str, int] = defaultdict(int)
    hit: Dict[str, float] = defaultdict(float)
    for k, c in zip(keys, covered):
        n[k] += 1
        hit[k] += c
    total = len(keys)
    return {k: {"examples": n[k], "share": round(n[k] / total, 4), "fixed_coverage": round(hit[k] / n[k], 4)}
            for k in sorted(n)}


def run_diagnose(input_csv: Union[str, Path], output_dir: Union[str, Path], alpha: float = 0.10,
                 seed: int = 17) -> Dict[str, object]:
    panel, _ = clean_panel(read_panel_csv(input_csv))
    examples = build_supervised_rows(panel)
    ages = series_age(panel, examples)
    for e, a in zip(examples, ages):
        e["series_age"] = a
    model = _fit([e for e in examples if int(e["target_year"]) <= TRAIN_MAX])
    later = [e for e in examples if int(e["target_year"]) > TRAIN_MAX]
    for e, r in zip(later, _abs_residuals(model, later)):
        e["abs_residual"] = r
    cal = [e for e in later if int(e["target_year"]) in CALIBRATION_YEARS]
    test = [e for e in later if int(e["target_year"]) in TEST_YEARS]
    pooled_fixed = quantile_radius([float(e["abs_residual"]) for e in cal], alpha)

    def covered(rows: Sequence[Dict[str, object]], radius: float) -> List[float]:
        return [1.0 if float(e["abs_residual"]) <= radius else 0.0 for e in rows]

    composition = {}
    for name, rows in (("calibration_2016_2019", cal), ("test_2020_2024", test)):
        hits = covered(rows, pooled_fixed)
        composition[name] = {
            "by_province": _share_and_cover([str(e["province"]) for e in rows], hits),
            "by_series_age": _share_and_cover([_age_bucket(int(e["series_age"])) for e in rows], hits),
        }

    # Mondrian (province-wise) radii
    by_year: Dict[int, List[Dict[str, object]]] = defaultdict(list)
    for e in later:
        by_year[int(e["target_year"])].append(e)

    def province_radii(calib: Sequence[Dict[str, object]], pooled: float) -> Dict[str, Tuple[float, bool]]:
        res: Dict[str, List[float]] = defaultdict(list)
        for e in calib:
            res[str(e["province"])].append(float(e["abs_residual"]))
        return {p: ((quantile_radius(v, alpha), False) if len(v) >= MIN_GROUP else (pooled, True))
                for p, v in res.items()}

    fixed_by_province = province_radii(cal, pooled_fixed)

    methods = ("pooled_fixed", "mondrian_fixed", "pooled_rolling4", "mondrian_rolling4")
    hits: Dict[str, List[float]] = {m: [] for m in methods}
    widths: Dict[str, List[float]] = {m: [] for m in methods}
    groups: List[str] = []
    provinces: List[str] = []
    fallbacks: List[Dict[str, object]] = []
    per_year: List[Dict[str, object]] = []
    for t in TEST_YEARS:
        window_rows = [e for y in range(t - WINDOW, t) for e in by_year[y]]
        pooled_roll = quantile_radius([float(e["abs_residual"]) for e in window_rows], alpha)
        rolling_by_province = province_radii(window_rows, pooled_roll)
        year_hits: Dict[str, List[float]] = {m: [] for m in methods}
        for e in by_year[t]:
            p = str(e["province"])
            mf, fb1 = fixed_by_province.get(p, (pooled_fixed, True))
            mr, fb2 = rolling_by_province.get(p, (pooled_roll, True))
            if fb1 or fb2:
                fallbacks.append({"year": t, "province": p})
            for m, radius in zip(methods, (pooled_fixed, mf, pooled_roll, mr)):
                c = 1.0 if float(e["abs_residual"]) <= radius else 0.0
                hits[m].append(c)
                year_hits[m].append(c)
                widths[m].append(2.0 * radius)
            groups.append(str(e["group_id"]))
            provinces.append(p)
        per_year.append({"target_year": t, **{m: round(sum(v) / len(v), 4) for m, v in year_hits.items()}})

    overall = {}
    for i, m in enumerate(methods):
        low, high = group_bootstrap_mean(hits[m], groups, seed + 100 + i)
        overall[m] = {"coverage": round(sum(hits[m]) / len(hits[m]), 4), "ci95_low": round(low, 4),
                      "ci95_high": round(high, 4), "mean_width": round(sum(widths[m]) / len(widths[m]), 4)}
    by_province: Dict[str, Dict[str, float]] = {}
    for p in sorted(set(provinces)):
        idx = [i for i, q in enumerate(provinces) if q == p]
        by_province[p] = {"examples": len(idx)}
        for m in methods:
            by_province[p][m] = round(sum(hits[m][i] for i in idx) / len(idx), 4)
            by_province[p][m + "_width"] = round(sum(widths[m][i] for i in idx) / len(idx), 4)
    fallback_provinces = sorted({str(f["province"]) for f in fallbacks})
    result = {"exploratory": True, "alpha": alpha, "min_group": MIN_GROUP, "composition": composition,
              "mondrian": {"overall": overall, "by_year": per_year, "by_province": by_province,
                           "fallback_to_pooled_provinces": fallback_provinces}}
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "diagnose_results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (out / "diagnose_report.md").write_text(_markdown(result, methods), encoding="utf-8")
    return result


def _markdown(result: Dict[str, object], methods: Sequence[str]) -> str:
    comp = result["composition"]  # type: ignore[index]
    lines = ["# Exploratory diagnosis (added after the shift results)", "",
             "## Calibration vs test composition, with fixed-interval coverage", ""]
    for key, title in (("by_province", "Province"), ("by_series_age", "Years of history")):
        lines += ["| {} | Cal. share | Cal. coverage | Test share | Test coverage |".format(title), "|---|---|---|---|---|"]
        cal, test = comp["calibration_2016_2019"][key], comp["test_2020_2024"][key]
        for k in sorted(set(cal) | set(test)):
            c, t = cal.get(k, {}), test.get(k, {})
            lines.append("| {} | {} | {} | {} | {} |".format(
                k, _f(c.get("share")), _f(c.get("fixed_coverage")), _f(t.get("share")), _f(t.get("fixed_coverage"))))
        lines.append("")
    mon = result["mondrian"]  # type: ignore[index]
    lines += ["## Province-wise (Mondrian) vs pooled radius", "",
              "| Method | Coverage | 95% CI | Mean width (log) |", "|---|---|---|---|"]
    for m in methods:
        o = mon["overall"][m]
        lines.append("| {} | {:.3f} | {:.3f} to {:.3f} | {:.3f} |".format(m, o["coverage"], o["ci95_low"], o["ci95_high"], o["mean_width"]))
    lines += ["", "| Year | " + " | ".join(methods) + " |", "|---|" + "---|" * len(methods)]
    for r in mon["by_year"]:
        lines.append("| {} | ".format(r["target_year"]) + " | ".join("{:.3f}".format(r[m]) for m in methods) + " |")
    lines += ["", "| Province | n | " + " | ".join(methods) + " |", "|---|---|" + "---|" * len(methods)]
    for p, v in mon["by_province"].items():
        lines.append("| {} | {} | ".format(p, v["examples"]) +
                     " | ".join("{:.3f} (w {:.2f})".format(v[m], v[m + "_width"]) for m in methods) + " |")
    lines += ["", "Provinces using the pooled radius (fewer than {} calibration residuals): {}".format(
        result["min_group"], ", ".join(mon["fallback_to_pooled_provinces"]) or "none")]
    return "\n".join(lines) + "\n"


def _f(value: object) -> str:
    return "-" if value is None else "{:.3f}".format(float(value))  # type: ignore[arg-type]
