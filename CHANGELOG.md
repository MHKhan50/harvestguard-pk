# Changelog

## 0.3.0 (2026-11-11)

- New `shift` command: label cleaning (aggregate labels removed, case duplicates merged), interval coverage by target year and province, and five recalibration methods using only earlier years (rolling, expanding, refit-rolling, adaptive alpha with two fixed gammas), with district-crop group bootstrap intervals.
- Shift protocol fixed in `docs/EXPERIMENT_PROTOCOL.json` before the real-data run.

## 0.2.0 (2026-11-10)

- `fetch-pbs` writes a provenance record (source URL, retrieval time, SHA-256, row counts).
- Rows with missing area, production or yield are skipped instead of stopping the run.
- Clearer error listing the columns found when the input schema does not match.
- Persistence alerts reported next to ridge alerts for yield shocks.
- New `report` command: per-crop and per-year error tables and two figures.
- requirements.txt, pytest, author and ORCID metadata.

## 0.1.0 (2026-11-10)

- Leakage-safe lagged features, persistence and rolling-median baselines, pooled ridge.
- Split-conformal interval and district-crop group bootstrap.
- Synthetic smoke-test panel and unit tests.
