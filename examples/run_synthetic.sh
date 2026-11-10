#!/bin/sh
set -eu
python -m pytest -q
python -m harvestguard_pk.cli run --input data/synthetic_crop_panel.csv --output-dir outputs/synthetic --alpha 0.10
python -m harvestguard_pk.cli report --run-dir outputs/synthetic
