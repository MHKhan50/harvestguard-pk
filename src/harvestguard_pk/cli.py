"""Command-line interface."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .data import fetch_pbs_panel
from .experiment import run_experiment
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
    return parser


def main() -> None:
    args = build_parser().parse_args()
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


if __name__ == "__main__":
    main()
