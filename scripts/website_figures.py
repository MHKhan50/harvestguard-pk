"""Forecast error and yield-shock rate by target year, from outputs/pbs/report.json.

    python scripts/website_figures.py --out docs/figures
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
# House palette: blue, yellow, red, light green; grey for the naive baseline
BLUE, YELLOW, RED, GREY = "#1F4E9C", "#E3A800", "#C8102E", "#8a94a8"
MODELS = [("persistence", "persistence", GREY), ("rolling_median", "rolling median", YELLOW),
          ("pooled_ridge", "pooled ridge", BLUE)]


def season(year: str) -> str:
    y = int(year)
    return "%d-%02d" % (y, (y + 1) % 100)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/figures")
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    report = json.loads((ROOT / "outputs" / "pbs" / "report.json").read_text())
    by_year = report["by_year"]
    labels = [season(r["target_year"]) for r in by_year]

    fig, (left, right) = plt.subplots(1, 2, figsize=(11, 4.2))
    for key, name, colour in MODELS:
        left.plot(labels, [r["rmse_log_" + key] for r in by_year], marker="o", color=colour, label=name)
    left.set_title("Forecast error by target year")
    left.set_ylabel("RMSE, log yield")
    left.grid(alpha=0.3)
    left.legend(frameon=False)

    rates = [100 * r["shock_rate"] for r in by_year]
    worst = max(range(len(rates)), key=rates.__getitem__)
    colours = [RED if i == worst else GREY for i in range(len(rates))]
    right.bar(labels, rates, color=colours)
    for x, v in zip(labels, rates):
        right.text(x, v + 0.2, "%.1f%%" % v, ha="center", va="bottom", fontsize=9)
    right.set_title("Yield shocks: 15% or more below the previous\nthree-year median")
    right.set_ylabel("% of test rows")
    right.grid(axis="y", alpha=0.3)
    right.set_axisbelow(True)

    fig.text(0.5, 0.01, "Pakistan district crop statistics (PBS, via Data Darbar), test years %s to %s, "
             "{:,} district-crop forecasts".format(report["test_rows"]) % (labels[0], labels[-1]),
             ha="center", fontsize=8, color="#555555")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(out / "error_and_shocks_by_year.png", dpi=150)
    print("wrote", out / "error_and_shocks_by_year.png")


if __name__ == "__main__":
    main()
