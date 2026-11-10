# HarvestGuard-PK

**Leakage-safe district-crop yield shock forecasting and uncertainty benchmark for Pakistan**

> The bundled CSV is synthetic and only for tests. Real-data results will be added below after the run on the PBS-derived panel; none are claimed yet.

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

## Design

- Every predictor for target fiscal year *t* comes from observations with fiscal year < *t*; all rows of a year are featurised before any of them enter the history.
- One pooled model over district x crop panels for all crops, not wheat only.
- Forward split by target year: train up to 2015, calibrate 2016 to 2019, test 2020 to 2024. The test years are not used for fitting or calibration.
- Forecasters: persistence (last observed yield), median of the last three yields, and a pooled ridge regression on nine lagged features (standard library only).
- Uncertainty: split-conformal interval on log yield (nominal 90%), and a bootstrap over district-crop groups for the ridge minus rolling-median RMSE difference.
- Shock alerts: a shock is a yield at least 15% below the median of the previous three yields; ridge and persistence alerts are scored with precision, recall and F1.

Details: [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md), protocol in [`docs/EXPERIMENT_PROTOCOL.json`](docs/EXPERIMENT_PROTOCOL.json), fields in [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md).

## Run it (Python 3.9+)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .
python -m pytest -q
python -m harvestguard_pk.cli fetch-pbs --output data/pbs_crop_panel.csv
python -m harvestguard_pk.cli run --input data/pbs_crop_panel.csv --output-dir outputs/pbs --alpha 0.10
python -m harvestguard_pk.cli report --run-dir outputs/pbs
```

`fetch-pbs` downloads the Data Darbar Parquet extract of PBS crop statistics, converts it with DuckDB, validates it and writes `data/pbs_crop_panel.provenance.json` (URL, retrieval time, SHA-256, row counts). If the upstream schema changes, it stops and lists the columns it found. Rows with missing values or unlabelled crops are skipped; missing district-years are never filled with zero.

`run` writes `metrics.json`, `test_predictions.csv` and `run_metadata.json`; `report` adds `report.md`, `report.json` and `figures/rmse_by_year.png`, `figures/rmse_by_crop.png`.

Synthetic smoke run (no download): `sh examples/run_synthetic.sh`. Its numbers say nothing about Pakistan.

## Results

Pending: the real-data run on the PBS-derived panel has not been done yet. This section will hold the forecast table, conformal coverage, shock alert scores and the two figures from `outputs/pbs/`.

## Limitations

See [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md): coverage gaps (for example AJK and GB districts are absent from the extract), district boundary and code changes over four decades, yield as an administrative aggregate, distribution shift between periods, one pooled model across very different crops, an operational shock threshold, and no weather or remote-sensing inputs.

## Repository

```text
src/harvestguard_pk/   data, features, model, metrics, experiment, report, cli
tests/                 unit and end-to-end tests (no network)
data/                  synthetic test panel and notices
docs/                  methodology, protocol, data dictionary, sources, limitations
examples/              synthetic smoke run
```

## Licensing

- **Code:** MIT License (`LICENSE`).
- **PBS aggregate source data:** follow the current PBS Official Statistics & Data Dissemination Policy and its attribution requirements. The Data Darbar catalogue also labels its derived data CC BY 4.0; cite the PBS original and the Data Darbar packaging, mark modifications, and do not imply derived estimates are official PBS statistics. Check the upstream catalogue and policy at redistribution time.
- **Synthetic panel:** generated by this repository, not official observations; use under the repository's MIT code licence.

## Responsible interpretation

The model estimates district–crop yield from historical statistical panels. It does not identify causal climate effects, provide farm-level advice, forecast market prices, or replace crop-cutting surveys and agronomic expertise. Reporting/measurement changes, administrative boundary changes, crop definitions and missing geographies can bias results. Read `docs/LIMITATIONS.md` before interpreting or publishing results.

## Citation

See `CITATION.cff`. Cite PBS as the original statistical source and the Data Darbar extract as the machine-readable packaging when using that extract. Cite the specific release and retrieval date in any resulting paper or dataset card.
