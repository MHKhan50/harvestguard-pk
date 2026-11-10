# Data dictionary

## Input panel CSV

The official-source preparation pipeline expects the following columns, matching the Data Darbar extract of PBS National Accounts crop statistics.

| Field | Type | Definition | Use |
|---|---|---|---|
| `district_code` | string | PBS district code as supplied by the extract | Panel key |
| `district` | string | District name | Descriptive metadata |
| `province` | string | Province/area label | Aggregate grouping |
| `crop_id` | string/integer | PBS crop identifier | Panel key |
| `crop` | string | Crop label | Descriptive metadata; unlabelled placeholders excluded |
| `fy` | string | Fiscal year, e.g. `2024-25` | Parsed into target start year |
| `area_000ha` | float | Area sown, thousand hectares | Lagged predictor and quality filter |
| `production_000t` | float | Production, thousand tonnes | Input quality/provenance field; not used as a predictor |
| `yield_t_per_ha` | float | Yield, tonnes per hectare | Forecast target and lagged predictor |

## Derived supervised table

| Field | Type | Definition |
|---|---|---|
| `target_year` | integer | Start year of the target fiscal year |
| `group_id` | string | `district_code|crop_id` panel key |
| `previous_median_yield` | float | Median of the three most recent earlier observed yields |
| `lag1_log_yield` | float | Log yield from latest earlier panel observation |
| `lag2_log_yield` | float | Log yield from second-latest earlier panel observation |
| `rolling3_log_median` | float | Log median of the last three earlier yields |
| `lag1_log_area` | float | Log area from latest earlier panel observation |
| `lagged_log_area_growth` | float | Log ratio of the two latest earlier areas |
| `province_crop_log_median` | float | Log province–crop median using earlier fiscal years only |
| `target_year_scaled` | float | `(target_year - 1981) / 40` |
| `gap_years_lag1` | float | Target year minus latest earlier observed year |
| `gap_years_lag2` | float | Target year minus second-latest earlier observed year |

## Bundled synthetic file

`data/synthetic_crop_panel.csv` follows the same input schema. It contains simulated district/crop/yield patterns for tests and smoke runs only. Its values are not measurements, estimates or official statistics for Pakistan. The file is marked with `synthetic=true` in `data/README.md` and in its accompanying notice.
