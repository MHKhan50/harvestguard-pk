# HarvestGuard-PK v0.1.0

**Leakage-safe district-crop yield shock forecasting and uncertainty benchmark for Pakistan**

> Research prototype. No predictive performance on official PBS data is claimed by this release. The bundled CSV is explicitly synthetic and is only for smoke tests and reproducibility checks.

## Research objective

Test whether a pooled, lag-only ridge model can improve one-fiscal-year-ahead crop-yield forecasts over persistence and rolling-median baselines, and whether a calibration-period conformal interval provides useful uncertainty information when evaluating district–crop panels under a strictly forward-in-time split.

The target application is agricultural production risk and food-security planning. This is **not** a commodity-price forecasting project: it models physical crop yield (tonnes/hectare), not retail or wholesale prices.

## Why Pakistan

The Pakistan Bureau of Statistics (PBS) National Accounts crop dashboard describes district-level production, cultivated area and yield for 121 crops. A machine-readable secondary release built from that PBS portal provides 78,425 district–crop–fiscal-year rows for 108 crops, 123 districts and 44 fiscal years (1981–82 to 2024–25). Its catalogue documents coverage gaps and the source pull date; users must retain those caveats when interpreting results.

Pakistan-specific research has also documented relationships between temperature/rainfall variability and cereal productivity, including different responses across agro-ecological zones. Existing wheat-only forecasting literature makes a broad multi-crop, district-panel benchmark a useful complementary question rather than a claim that crop-yield forecasting itself is novel.

## Research questions

1. **RQ1 — Forecast skill:** Does pooled ridge regression reduce out-of-time log-yield RMSE relative to last-observation persistence and the median of the last three observed yields?
2. **RQ2 — Uncertainty:** Does a split-conformal interval calibrated on 2016–2019 achieve empirical 90% coverage on 2020–2024 test targets, and at what interval width?
3. **RQ3 — Shock alerts:** How precisely and sensitively can a forecast flag a yield shock, defined prospectively as a target yield at least 15% below the median of the previous three observed yields?

These are hypotheses to test, not pre-asserted findings.

## Technical contribution

- Strictly lagged feature construction: every predictor for target fiscal year *t* is calculated from observations with fiscal year `< t`.
- District × crop panel formulation across multiple crops, not only wheat.
- Forward temporal protocol: train targets through 2015, calibrate on 2016–2019, test on 2020–2024.
- Lightweight pooled ridge implementation using only the Python standard library.
- Split-conformal absolute-residual interval and group-level bootstrap interval for the difference in test RMSE (ridge minus rolling-median baseline).
- Explicit handling of unlabelled crop placeholders and documented district/crop coverage gaps.

## Repository structure

```text
harvestguard-pk-v0.1.0/
├── data/                  # synthetic smoke-test CSV + data instructions
├── docs/                  # methodology, protocol, data dictionary, limitations, sources
├── examples/              # example experiment command
├── src/harvestguard_pk/   # maintainable Python package
├── tests/                 # standard-library unit tests
├── CITATION.cff
├── LICENSE
└── pyproject.toml
```

## Quick start (Python 3.9+; no mandatory third-party packages)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
python -m harvestguard_pk.cli generate-synthetic --output data/synthetic_crop_panel.csv --seed 17
python -m harvestguard_pk.cli run --input data/synthetic_crop_panel.csv --output-dir outputs/synthetic --alpha 0.10
```

The synthetic experiment is a pipeline smoke test only. Do not cite its metrics as evidence about real Pakistani crop yields.

## Prepare the official-source panel

The PBS dashboard is the primary institutional source. For a reproducible bulk download, this project uses the Data Darbar machine-readable extract, which identifies PBS National Accounts crop statistics as its source and provides a Parquet file. The extract is a secondary packaging of official aggregate statistics, not a new PBS release.

Install the one optional conversion dependency and fetch the Parquet into a normalized CSV:

```bash
python -m pip install -e '.[data]'
python -m harvestguard_pk.cli fetch-pbs --output data/pbs_crop_panel.csv
```

Then run the actual-data experiment:

```bash
python -m harvestguard_pk.cli run --input data/pbs_crop_panel.csv --output-dir outputs/pbs --alpha 0.10
```

`fetch-pbs` downloads the source Parquet and uses optional DuckDB to convert it to CSV. The pipeline excludes rows whose crop label is an unlabelled placeholder, non-positive or non-finite area/yield values, and malformed fiscal-year labels. It does not fill missing district-years with zero.

If the upstream URL or schema changes, the fetch step fails loudly; retain the source file and record its retrieval date/hash before publication. See `docs/SOURCES.md` and `docs/METHODOLOGY.md`.

## Outputs

The experiment writes:

- `metrics.json` — split sizes, forecast metrics, conformal coverage/width and shock classification metrics;
- `test_predictions.csv` — observed yield, baseline/model forecasts, interval and shock labels;
- `run_metadata.json` — source path, run configuration and protocol version.

Metrics are generated from the supplied input only. The repository release does not contain a verified run on the external PBS extract, so no real-data scores are asserted here.

## Reproducibility and resource profile

- Python 3.9+; required runtime dependencies: standard library only.
- The official panel is approximately 747 KB in Parquet form according to the catalogue; optional DuckDB is used only for conversion.
- Fixed default seed: 17.
- No GPU, neural-network framework, database server or external API key required.
- Unit tests use deterministic synthetic fixtures and do not require network access.

## Licensing

- **Code:** MIT License (`LICENSE`).
- **PBS aggregate source data:** follow the current PBS Official Statistics & Data Dissemination Policy and its attribution requirements. The Data Darbar catalogue also labels its derived data CC BY 4.0; cite the PBS original and the Data Darbar packaging, mark modifications, and do not imply derived estimates are official PBS statistics. Check the upstream catalogue and policy at redistribution time.
- **Synthetic panel:** generated by this repository, not official observations; use under the repository's MIT code licence.

## Responsible interpretation

The model estimates district–crop yield from historical statistical panels. It does not identify causal climate effects, provide farm-level advice, forecast market prices, or replace crop-cutting surveys and agronomic expertise. Reporting/measurement changes, administrative boundary changes, crop definitions and missing geographies can bias results. Read `docs/LIMITATIONS.md` before interpreting or publishing results.

## Citation

See `CITATION.cff` and `docs/VERIFICATION.md`. Cite PBS as the original statistical source and the Data Darbar extract as the machine-readable packaging when using that extract. Cite the specific release and retrieval date in any resulting paper or dataset card.
