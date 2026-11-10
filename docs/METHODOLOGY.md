# Methodology and experimental protocol

## 1. Unit of analysis and target

One observation is a district × crop × fiscal-year record. The target is the reported crop yield in tonnes per hectare for fiscal year `t`. Fiscal years are represented by their starting calendar year (for example, `2024-25` maps to `2024`).

Rows with unlabelled crop placeholders, invalid fiscal-year strings, non-finite values, or non-positive cultivated area/yield are excluded. Missing district–crop–years remain missing; they are not interpreted as zero production.

## 2. Forecast origin and features

For every target row in year `t`, features use only records for the same district–crop panel and same province–crop aggregate with year `< t`:

1. log yield at the most recent observed panel year;
2. log yield at the second-most-recent observed panel year;
3. log median yield over the last three observed panel records;
4. log cultivated area at the most recent observed panel year;
5. log area ratio between the two most recent observed records;
6. log median yield for the province–crop group using all earlier records;
7. normalized target year;
8. year gap between `t` and the latest panel observation;
9. year gap between `t` and the second-most-recent panel observation.

A supervised example is created only after at least three historical observations exist for that district–crop group. All same-year rows are featurized before any of them are added to history, preventing within-year leakage in province–crop aggregates.

## 3. Models

- **Persistence:** forecast equals the most recently observed yield.
- **Rolling median:** forecast equals the median of the last three observed yields.
- **Pooled ridge:** standardized lagged features and a ridge-regularized linear model fitted on training examples only. The intercept is not penalized. The implementation uses a small normal-equation system and Gaussian elimination from the Python standard library.

The target is log yield. Predictions are exponentiated for yield-scale reporting. No current-year production, current-year area, future weather, or target-year aggregates enter the predictors.

## 4. Temporal split

Split by target fiscal-year start:

- training: `target_year <= 2015`;
- calibration: `2016 <= target_year <= 2019`;
- test: `2020 <= target_year <= 2024`.

The model is fitted once on training data. Calibration residuals are computed on the untouched calibration years. The test set is not used for model fitting, feature selection, or interval calibration. If an input does not contain all three periods with enough examples, the experiment stops with a clear error rather than silently changing the split.

## 5. Conformal uncertainty

For calibration examples, compute absolute log residuals `|y_log - yhat_log|`. The split-conformal radius is the finite-sample empirical quantile at level `1 - alpha`, using the `ceil((n + 1) * (1 - alpha))` order statistic with index clipping. The default `alpha=0.10` yields a nominal 90% interval on log yield:

`[exp(yhat_log - radius), exp(yhat_log + radius)]`.

Report empirical test coverage and mean interval width on log scale. Coverage is an empirical diagnostic, not a guarantee under arbitrary temporal or geographic distribution shift.

## 6. Yield-shock definition and alert evaluation

For each example, the reference level is the median of the previous three observed yields. A realized shock is `target_yield <= 0.85 * previous_median`. A model alert is emitted when the point forecast is at or below the same threshold. Precision, recall, F1 and alert rate are reported. This operational definition is fixed before test evaluation; alternative thresholds should be treated as sensitivity analyses.

## 7. Metrics and uncertainty

Report log-scale RMSE and MAE for all three forecasters, yield-scale RMSE for the pooled ridge model, conformal coverage and interval width, and shock precision/recall/F1. A deterministic group bootstrap resamples district–crop groups (not individual rows) to estimate a percentile interval for the test RMSE difference `ridge - rolling_median`.

A negative RMSE difference favours ridge. The bootstrap interval is descriptive and should not be interpreted as a formal causal or universal significance claim.

## 8. Reproducibility controls

- Fixed seed (default 17) for synthetic data and group bootstrap.
- Standard-library-only model and test path.
- Source data, retrieval date, upstream schema and checksum should be recorded by the research team for any publication-grade run.
- Report actual-data and synthetic smoke-test outputs separately.
