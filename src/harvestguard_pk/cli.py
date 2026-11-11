"""Command-line interface."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional, Sequence

from .data import fetch_pbs_panel
from .experiment import run_experiment
from .report import build_report
from .shift import run_shift
from .synthetic import generate_synthetic_panel


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="harvestguard", description="Pakistan district-crop yield shock benchmark")
    subparsers = parser.add_subparsers(dest="command", required=True)

    synthetic = subparsers.add_parser("generate-synthetic", help="generate clearly labelled synthetic smoke-test data")
    synthetic.add_argument("--output", required=True)
    synthetic.add_argument("--seed", type=int, default=17)
    synthetic.add_argument("--districts", type=int, default=24)

    fetch = subparsers.add_parser("fetch-pbs", help="download PBS-derived Parquet extract and convert it to CSV")
    fetch.add_argument("--output", required=True)

    run = subparsers.add_parser("run", help="run the fixed temporal benchmark")
    run.add_argument("--input", required=True)
    run.add_argument("--output-dir", required=True)
    run.add_argument("--alpha", type=float, default=0.10)
    run.add_argument("--seed", type=int, default=17)

    shift = subparsers.add_parser("shift", help="interval coverage by year with recalibration methods")
    shift.add_argument("--input", required=True)
    shift.add_argument("--output-dir", required=True)
    shift.add_argument("--alpha", type=float, default=0.10)
    shift.add_argument("--no-clean", action="store_true", help="skip label cleaning (sensitivity run)")
    shift.add_argument("--seed", type=int, default=17)

    report = subparsers.add_parser("report", help="per-crop and per-year tables and figures for a finished run")
    report.add_argument("--run-dir", required=True)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "generate-synthetic":
        path = generate_synthetic_panel(args.output, seed=args.seed, districts=args.districts)
        print("Synthetic smoke-test panel written: {}".format(path))
        print("NOTICE: these are simulated rows, not official Pakistan observations.")
    elif args.command == "fetch-pbs":
        path = fetch_pbs_panel(args.output)
        print("PBS-derived source panel converted and validated: {}".format(path))
    elif args.command == "run":
        metrics = run_experiment(args.input, args.output_dir, alpha=args.alpha, seed=args.seed)
        print(json.dumps(metrics, indent=2, sort_keys=True))
        print("Outputs written to {}".format(Path(args.output_dir)))
    elif args.command == "shift":
        run_shift(args.input, args.output_dir, alpha=args.alpha, clean=not args.no_clean, seed=args.seed)
        print((Path(args.output_dir) / "shift_report.md").read_text(encoding="utf-8"))
    elif args.command == "report":
        build_report(args.run_dir)
        print((Path(args.run_dir) / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
