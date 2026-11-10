#!/bin/sh
set -eu
python -m unittest discover -s tests -v
python -m harvestguard_pk.cli generate-synthetic --output data/synthetic_crop_panel.csv --seed 17
python -m harvestguard_pk.cli run --input data/synthetic_crop_panel.csv --output-dir outputs/synthetic --alpha 0.10
