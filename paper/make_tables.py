"""Build the paper's LaTeX tables and figures from the committed result files.

Run from the repository root: python paper/make_tables.py
Reads outputs/pbs_shift/shift_results.json, outputs/pbs_shift_raw/shift_results.json
and outputs/pbs_diagnose/diagnose_results.json; writes paper/tables/*.tex and
paper/figures/*.pdf.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
OUT_T = ROOT / "paper" / "tables"
OUT_F = ROOT / "paper" / "figures"
LABEL = {"fixed": "Fixed (2016--19)", "rolling4": "Rolling, 4 years", "expanding": "Expanding",
         "refit_rolling4": "Refit + rolling, 4 years", "aci_g0.1": r"ACI, $\gamma=0.1$", "aci_g0.5": r"ACI, $\gamma=0.5$",
         "pooled_fixed": "Pooled, fixed", "mondrian_fixed": "By province, fixed",
         "pooled_rolling4": "Pooled, rolling 4 years", "mondrian_rolling4": "By province, rolling 4 years"}
FY = {2020: "2020--21", 2021: "2021--22", 2022: "2022--23", 2023: "2023--24", 2024: "2024--25"}


def load(path: str) -> Dict[str, object]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write(name: str, lines: List[str]) -> None:
    OUT_T.mkdir(parents=True, exist_ok=True)
    (OUT_T / name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _reweighted(comp: Dict[str, object], key: str) -> float:
    """Test coverage if test groups had the calibration-period shares."""
    cal, test = comp["calibration_2016_2019"][key], comp["test_2020_2024"][key]  # type: ignore[index]
    return sum(cal[k]["share"] * test[k]["fixed_coverage"] for k in cal if k in test) / sum(
        cal[k]["share"] for k in cal if k in test)


def main() -> None:
    shift = load("outputs/pbs_shift/shift_results.json")
    raw = load("outputs/pbs_shift_raw/shift_results.json")
    diag = load("outputs/pbs_diagnose/diagnose_results.json")
    f = shift["forecast"]

    rows = [r"\begin{tabular}{lrr}", r"\toprule", r"Forecaster & RMSE & MAE \\", r"\midrule"]
    for k, name in (("persistence", "Persistence (last year)"), ("rolling_median", "Median of last 3 years"),
                    ("pooled_ridge", "Pooled ridge")):
        rows.append(r"{} & {:.3f} & {:.3f} \\".format(name, f[k]["rmse"], f[k]["mae"]))
    rows += [r"\bottomrule", r"\end{tabular}"]
    write("forecast.tex", rows)

    cov = shift["coverage"]["overall"]
    rows = [r"\begin{tabular}{lccc}", r"\toprule",
            r"Method & Coverage & 95\% CI & Mean width \\", r"\midrule"]
    for m in shift["methods"]:
        o = cov[m]
        rows.append(r"{} & {:.3f} & {:.3f}--{:.3f} & {:.3f} \\".format(LABEL[m], o["coverage"], o["ci95_low"], o["ci95_high"], o["mean_width"]))
    rows += [r"\midrule", r"\multicolumn{4}{l}{\emph{Exploratory, added after the results above}} \\"]
    for m in ("mondrian_fixed", "mondrian_rolling4"):
        o = diag["mondrian"]["overall"][m]
        rows.append(r"{} & {:.3f} & {:.3f}--{:.3f} & {:.3f} \\".format(LABEL[m], o["coverage"], o["ci95_low"], o["ci95_high"], o["mean_width"]))
    rows += [r"\bottomrule", r"\end{tabular}"]
    write("coverage.tex", rows)

    methods = shift["methods"]
    rows = [r"\begin{tabular}{l" + "c" * len(methods) + "}", r"\toprule",
            "Target year & " + " & ".join(LABEL[m] for m in methods) + r" \\", r"\midrule"]
    for r in shift["coverage_by_year"]:
        rows.append(FY[r["target_year"]] + " & " + " & ".join("{:.3f}".format(r[m]["coverage"]) for m in methods) + r" \\")
    rows += [r"\midrule", "Width 2021--22 & " + " & ".join("{:.2f}".format(shift["coverage_by_year"][1][m]["width"]) for m in methods) + r" \\",
             "Width 2023--24 & " + " & ".join("{:.2f}".format(shift["coverage_by_year"][3][m]["width"]) for m in methods) + r" \\",
             r"\bottomrule", r"\end{tabular}"]
    write("by_year.tex", rows)

    comp = diag["composition"]
    rows = [r"\begin{tabular}{lcccc}", r"\toprule",
            r" & \multicolumn{2}{c}{Calibration 2016--19} & \multicolumn{2}{c}{Test 2020--24} \\",
            r" & Share & Coverage & Share & Coverage \\", r"\midrule", r"\emph{Province} \\"]
    for key, buckets in (("by_province", None), ("by_series_age", ["3-5", "6-10", "11-20", "21+"])):
        cal, test = comp["calibration_2016_2019"][key], comp["test_2020_2024"][key]
        keys = buckets or sorted(set(cal) | set(test))
        if buckets:
            rows.append(r"\emph{Years of history} \\")
        for k in keys:
            name = k.title() if not buckets else k.replace("-", "--")
            rows.append(r"\quad {} & {:.3f} & {:.3f} & {:.3f} & {:.3f} \\".format(
                name, cal[k]["share"], cal[k]["fixed_coverage"], test[k]["share"], test[k]["fixed_coverage"]))
    rows += [r"\bottomrule", r"\end{tabular}"]
    write("composition.tex", rows)

    prov = diag["mondrian"]["by_province"]
    pm = ("pooled_fixed", "pooled_rolling4", "mondrian_rolling4")
    rows = [r"\begin{tabular}{lrccc}", r"\toprule",
            "Province & $n$ & " + " & ".join(LABEL[m] for m in pm) + r" \\", r"\midrule"]
    for p, v in prov.items():
        rows.append(r"{} & {} & ".format(p.title(), v["examples"]) +
                    " & ".join("{:.3f} ({:.2f})".format(v[m], v[m + "_width"]) for m in pm) + r" \\")
    rows += [r"\bottomrule", r"\end{tabular}"]
    write("province.tex", rows)

    cl = shift["cleaning"]
    macros = {
        "RowsIn": "{:,}".format(cl["rows_in"]), "RowsOut": "{:,}".format(cl["rows_out"]),
        "AggRows": "{:,}".format(cl["aggregate_rows_excluded"]), "OverlapRows": cl["overlapping_rows_dropped"],
        "Crops": cl["crops_out"], "TestN": "{:,}".format(f["test_examples"]),
        "ShockRate": "{:.1f}".format(100 * f["shock_rate"]),
        "FixedCov": "{:.3f}".format(cov["fixed"]["coverage"]), "RawFixedCov": "{:.3f}".format(raw["coverage"]["overall"]["fixed"]["coverage"]),
        "RollCov": "{:.3f}".format(cov["rolling4"]["coverage"]),
        "ReweightAge": "{:.3f}".format(_reweighted(comp, "by_series_age")),
        "ReweightProv": "{:.3f}".format(_reweighted(comp, "by_province")),
        "MonRollCov": "{:.3f}".format(diag["mondrian"]["overall"]["mondrian_rolling4"]["coverage"]),
    }
    write("numbers.tex", [r"\newcommand{\%s}{%s}" % (k, v) for k, v in macros.items()])

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    OUT_F.mkdir(parents=True, exist_ok=True)
    years = [r["target_year"] for r in shift["coverage_by_year"]]
    series = [("fixed", shift, "#8a94a8", "-"), ("rolling4", shift, "#2b5ce6", "-"),
              ("aci_g0.5", shift, "#c48a2a", ":")]
    fig, ax = plt.subplots(figsize=(6.2, 3.9))
    for m, _, c, ls in series:
        ax.plot(years, [r[m]["coverage"] for r in shift["coverage_by_year"]], ls, marker="o", color=c, label=LABEL[m].replace("$", "").replace("\\gamma", "gamma"))
    ax.plot(years, [r["mondrian_rolling4"] for r in diag["mondrian"]["by_year"]], "--", marker="s", color="#0f1932", label="By province, rolling 4 years")
    ax.axhline(0.9, color="#b33", lw=1, ls="--", label="Nominal 0.90")
    ax.set_xticks(years)
    ax.set_xticklabels([FY[y].replace("--", "-") for y in years])
    ax.set_ylabel("Test coverage")
    ax.set_ylim(0.65, 1.0)
    ax.grid(alpha=0.3)
    ax.legend(frameon=False, fontsize=7, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.14))
    fig.tight_layout()
    fig.savefig(OUT_F / "coverage_by_year.pdf")
    plt.close(fig)
    print("tables and figure written")


if __name__ == "__main__":
    main()
