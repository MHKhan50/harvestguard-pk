"""Tables and figures from a finished run (reads test_predictions.csv and metrics.json).

Error is reported on the log-yield scale, as in the main metrics, so crops with
very different yields (sugarcane versus pulses) can be compared.
"""
from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Sequence, Union

FORECASTERS = (
    ("persistence", "persistence_yield_t_per_ha"),
    ("rolling_median", "rolling_median_yield_t_per_ha"),
    ("pooled_ridge", "ridge_yield_t_per_ha"),
)
MIN_ROWS_PER_CROP = 30


def _rmse_log(rows: Sequence[Dict[str, str]], column: str) -> float:
    errors = [math.log(float(r["actual_yield_t_per_ha"])) - math.log(float(r[column])) for r in rows]
    return math.sqrt(sum(e * e for e in errors) / len(errors))


def _breakdown(rows: Sequence[Dict[str, str]], key: str, min_rows: int) -> List[Dict[str, object]]:
    grouped: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row[key]].append(row)
    table: List[Dict[str, object]] = []
    for name, members in grouped.items():
        if len(members) < min_rows:
            continue
        entry: Dict[str, object] = {key: name, "rows": len(members),
                                    "shock_rate": round(sum(int(r["actual_shock"]) for r in members) / len(members), 4)}
        for label, column in FORECASTERS:
            entry["rmse_log_" + label] = round(_rmse_log(members, column), 4)
        table.append(entry)
    return table


def build_report(run_dir: Union[str, Path]) -> Dict[str, object]:
    run = Path(run_dir)
    with (run / "test_predictions.csv").open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("test_predictions.csv is empty")
    metrics = json.loads((run / "metrics.json").read_text(encoding="utf-8"))
    by_crop = sorted(_breakdown(rows, "crop", MIN_ROWS_PER_CROP), key=lambda e: -int(e["rows"]))
    by_year = sorted(_breakdown(rows, "target_year", 1), key=lambda e: int(str(e["target_year"])))
    ridge_wins = sum(1 for e in by_crop if float(e["rmse_log_pooled_ridge"]) < float(e["rmse_log_rolling_median"]))
    report: Dict[str, object] = {
        "test_rows": len(rows),
        "crops_with_at_least_{}_test_rows".format(MIN_ROWS_PER_CROP): len(by_crop),
        "crops_where_ridge_beats_rolling_median": ridge_wins,
        "by_crop": by_crop,
        "by_year": by_year,
    }
    (run / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (run / "report.md").write_text(_markdown(metrics, report), encoding="utf-8")
    _plot(by_year, by_crop, run / "figures")
    return report


def _markdown(metrics: Dict[str, object], report: Dict[str, object]) -> str:
    f = metrics["forecast_log_scale"]  # type: ignore[index]
    counts = metrics["sample_counts"]  # type: ignore[index]
    ci = metrics["ridge_minus_rolling_median_rmse_group_bootstrap_95pct"]  # type: ignore[index]
    conf = metrics["conformal_interval"]  # type: ignore[index]
    shock = metrics["yield_shock"]  # type: ignore[index]
    pers = metrics.get("yield_shock_persistence_alert", {})  # type: ignore[union-attr]
    lines = [
        "# Run report", "",
        "Examples: train {train}, calibration {calibration}, test {test}.".format(**counts), "",
        "| Forecaster | RMSE (log yield) | MAE (log yield) |", "|---|---|---|",
    ]
    for label, _ in FORECASTERS:
        lines.append("| {} | {:.4f} | {:.4f} |".format(label, f[label]["rmse"], f[label]["mae"]))
    lines += [
        "",
        "Ridge minus rolling-median RMSE, group bootstrap 95% CI: {} to {}.".format(
            _fmt(ci.get("ci95_low")), _fmt(ci.get("ci95_high"))),
        "Conformal interval: nominal {:.0%}, test coverage {:.1%}, width {:.4f} (log scale).".format(
            conf["nominal_coverage"], conf["empirical_test_coverage"], conf["mean_width_log_scale"]),
        "Yield shocks (15% below previous three-year median): test rate {:.1%}.".format(shock["positive_rate"]),
        "Ridge alerts: precision {:.3f}, recall {:.3f}, F1 {:.3f}.".format(shock["precision"], shock["recall"], shock["f1"]),
    ]
    if pers:
        lines.append("Persistence alerts: precision {:.3f}, recall {:.3f}, F1 {:.3f}.".format(
            pers["precision"], pers["recall"], pers["f1"]))
    lines += ["", "## By crop (at least {} test rows)".format(MIN_ROWS_PER_CROP), "",
              "| Crop | Test rows | Shock rate | Persistence | Rolling median | Pooled ridge |", "|---|---|---|---|---|---|"]
    for e in report["by_crop"]:  # type: ignore[union-attr]
        lines.append("| {crop} | {rows} | {shock_rate:.3f} | {rmse_log_persistence:.4f} | "
                     "{rmse_log_rolling_median:.4f} | {rmse_log_pooled_ridge:.4f} |".format(**e))
    lines += ["", "## By target year", "", "| Year | Test rows | Shock rate | Persistence | Rolling median | Pooled ridge |",
              "|---|---|---|---|---|---|"]
    for e in report["by_year"]:  # type: ignore[union-attr]
        lines.append("| {target_year} | {rows} | {shock_rate:.3f} | {rmse_log_persistence:.4f} | "
                     "{rmse_log_rolling_median:.4f} | {rmse_log_pooled_ridge:.4f} |".format(**e))
    return "\n".join(lines) + "\n"


def _fmt(value: object) -> str:
    return "n/a" if value is None else "{:.4f}".format(float(value))  # type: ignore[arg-type]


def _plot(by_year: Sequence[Dict[str, object]], by_crop: Sequence[Dict[str, object]], out: Path) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed; skipping figures (pip install -r requirements.txt)")
        return
    out.mkdir(parents=True, exist_ok=True)
    colours = {"persistence": "#8a94a8", "rolling_median": "#E3A800", "pooled_ridge": "#1F4E9C"}
    fig, ax = plt.subplots(figsize=(7, 4))
    years = [int(str(e["target_year"])) for e in by_year]
    for label, _ in FORECASTERS:
        ax.plot(years, [e["rmse_log_" + label] for e in by_year], marker="o", color=colours[label], label=label)
    ax.set_xlabel("Target fiscal year (start)")
    ax.set_ylabel("RMSE, log yield")
    ax.set_title("Test error by year")
    ax.set_xticks(years)
    ax.grid(alpha=0.3)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(out / "rmse_by_year.png", dpi=150)
    plt.close(fig)

    top = list(by_crop[:12])
    if top:
        fig, ax = plt.subplots(figsize=(8, 0.45 * len(top) + 1.4))
        positions = list(range(len(top)))
        height = 0.26
        for offset, (label, _) in zip((-height, 0.0, height), FORECASTERS):
            ax.barh([p + offset for p in positions], [e["rmse_log_" + label] for e in top], height=height,
                    color=colours[label], label=label)
        ax.set_yticks(positions)
        ax.set_yticklabels(["{} (n={})".format(e["crop"], e["rows"]) for e in top])
        ax.invert_yaxis()
        ax.set_xlabel("RMSE, log yield (test 2020-2024)")
        ax.set_title("Test error for the crops with most test rows")
        ax.grid(axis="x", alpha=0.3)
        ax.legend(frameon=False, fontsize=8)
        fig.tight_layout()
        fig.savefig(out / "rmse_by_crop.png", dpi=150)
        plt.close(fig)
