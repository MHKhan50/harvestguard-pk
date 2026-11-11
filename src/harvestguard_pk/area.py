"""Crop area trends for one district against its province (checks a local observation).

Reads the same panel as the forecasts. Area is in thousand hectares, as published.
Labels are matched case-insensitively, so "Cotton" and "cotton" are the same crop.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

from .data import read_panel_csv

EARLY: Tuple[int, int] = (2011, 2015)
LATE: Tuple[int, int] = (2020, 2024)


def _mean(values: Sequence[float]) -> Optional[float]:
    return sum(values) / len(values) if values else None


def area_trend(panel: Sequence[Dict[str, object]], district: str, crops: Sequence[str],
               first_year: int = 2005) -> Dict[str, object]:
    wanted = {c.strip().lower() for c in crops}
    def squash(text: object) -> str:
        return "".join(str(text).lower().split())

    exact = sorted({str(r["district"]) for r in panel if squash(r["district"]) == squash(district)})
    matches = exact or sorted({str(r["district"]) for r in panel if squash(district) in squash(r["district"])})
    if len(matches) != 1:
        raise ValueError("district '{}' matched {}; give a more exact name".format(district, matches or "nothing"))
    name = matches[0]
    province = next(str(r["province"]) for r in panel if r["district"] == name)
    series: Dict[str, Dict[str, Dict[int, float]]] = {"district": defaultdict(dict), "province": defaultdict(dict)}
    for r in panel:
        crop = str(r["crop"]).strip().lower()
        year = int(r["year"])
        if crop not in wanted or year < first_year:
            continue
        area = float(r["area_000ha"])
        if r["district"] == name:
            series["district"][crop][year] = series["district"][crop].get(year, 0.0) + area
        if r["province"] == province:
            series["province"][crop][year] = series["province"][crop].get(year, 0.0) + area
    summary: Dict[str, Dict[str, object]] = {}
    for level in ("district", "province"):
        for crop in sorted(wanted):
            years = series[level].get(crop, {})
            early = _mean([v for y, v in years.items() if EARLY[0] <= y <= EARLY[1]])
            late = _mean([v for y, v in years.items() if LATE[0] <= y <= LATE[1]])
            change = None if not early or late is None else round(100.0 * (late - early) / early, 1)
            summary.setdefault(crop, {})[level] = {
                "mean_area_{}_{}".format(*EARLY): None if early is None else round(early, 2),
                "mean_area_{}_{}".format(*LATE): None if late is None else round(late, 2),
                "change_percent": change,
                "years_available": len(years),
            }
    by_year = {crop: {str(y): round(v, 2) for y, v in sorted(series["district"].get(crop, {}).items())}
               for crop in sorted(wanted)}
    return {"district": name, "province": province, "crops": sorted(wanted), "early_years": list(EARLY),
            "late_years": list(LATE), "summary": summary, "district_area_by_year": by_year}


def _markdown(result: Dict[str, object]) -> str:
    e, l = result["early_years"], result["late_years"]  # type: ignore[index]
    lines = ["# Crop area in {} ({}), thousand hectares".format(result["district"], result["province"]), "",
             "Mean area {}-{} vs {}-{} (fiscal-year start).".format(e[0], e[1], l[0], l[1]), "",
             "| Crop | District early | District late | District change | Province change |", "|---|---|---|---|---|"]
    for crop, s in result["summary"].items():  # type: ignore[union-attr]
        d, p = s["district"], s["province"]
        k1, k2 = "mean_area_{}_{}".format(*e), "mean_area_{}_{}".format(*l)
        lines.append("| {} | {} | {} | {} | {} |".format(crop, _v(d[k1]), _v(d[k2]), _pct(d["change_percent"]), _pct(p["change_percent"])))
    lines += ["", "## District area by year", ""]
    crops = list(result["district_area_by_year"])  # type: ignore[arg-type]
    years = sorted({int(y) for c in crops for y in result["district_area_by_year"][c]}, reverse=False)  # type: ignore[index]
    lines += ["| Year | " + " | ".join(crops) + " |", "|---|" + "---|" * len(crops)]
    for y in years:
        lines.append("| {} | ".format(y) + " | ".join(_v(result["district_area_by_year"][c].get(str(y))) for c in crops) + " |")  # type: ignore[index]
    return "\n".join(lines) + "\n"


def _v(x: object) -> str:
    return "-" if x is None else "{:.1f}".format(float(x))  # type: ignore[arg-type]


def _pct(x: object) -> str:
    return "-" if x is None else "{:+.1f}%".format(float(x))  # type: ignore[arg-type]


def _plot(result: Dict[str, object], path: Path) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed; skipping the figure")
        return
    colours = ["#0f1932", "#2b5ce6", "#c48a2a", "#8a94a8", "#7aa0f0", "#b33"]
    fig, ax = plt.subplots(figsize=(7.5, 4))
    for colour, (crop, years) in zip(colours, result["district_area_by_year"].items()):  # type: ignore[union-attr]
        xs = sorted(int(y) for y in years)
        ax.plot(xs, [years[str(x)] for x in xs], marker="o", ms=3, color=colour, label=crop)
    ax.set_title("Crop area in {}".format(result["district"]))
    ax.set_xlabel("Fiscal year (start)")
    ax.set_ylabel("Area, thousand hectares")
    ax.grid(alpha=0.3)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def run_area(input_csv: Union[str, Path], output_dir: Union[str, Path], district: str,
             crops: Sequence[str]) -> Dict[str, object]:
    result = area_trend(read_panel_csv(input_csv), district, crops)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "area_results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (out / "area_report.md").write_text(_markdown(result), encoding="utf-8")
    _plot(result, out / "figures" / "area_by_year.png")
    return result
