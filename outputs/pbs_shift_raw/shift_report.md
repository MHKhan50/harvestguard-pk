# Coverage under temporal shift

## Point forecasts (train <= 2015, test 2020-2024, 19177 examples)

| Forecaster | RMSE (log) | MAE (log) |
|---|---|---|
| persistence | 0.4639 | 0.2001 |
| rolling_median | 0.4483 | 0.2166 |
| pooled_ridge | 0.4136 | 0.2093 |

Shock rate 10.3%. Alerts F1: persistence 0.309 (P 0.392, R 0.255); ridge 0.195 (P 0.338, R 0.138).

## Interval coverage, nominal 90%

| Method | Coverage | 95% CI (group bootstrap) | Mean width (log) |
|---|---|---|---|
| fixed | 0.746 | 0.737 to 0.754 | 0.477 |
| rolling4 | 0.838 | 0.830 to 0.845 | 0.879 |
| expanding | 0.811 | 0.803 to 0.819 | 0.701 |
| refit_rolling4 | 0.837 | 0.831 to 0.844 | 0.870 |
| aci_g0.1 | 0.799 | 0.792 to 0.807 | 0.656 |
| aci_g0.5 | 0.883 | 0.878 to 0.888 | 2.026 |

## Coverage by target year

| Year | n | fixed | rolling4 | expanding | refit_rolling4 | aci_g0.1 | aci_g0.5 |
|---|---|---|---|---|---|---|---|
| 2020 | 3370 | 0.710 | 0.710 | 0.710 | 0.710 | 0.710 | 0.710 |
| 2021 | 3817 | 0.730 | 0.799 | 0.781 | 0.801 | 0.762 | 0.997 |
| 2022 | 3983 | 0.707 | 0.820 | 0.784 | 0.819 | 0.765 | 0.796 |
| 2023 | 3946 | 0.752 | 0.901 | 0.858 | 0.897 | 0.844 | 0.994 |
| 2024 | 4061 | 0.822 | 0.937 | 0.904 | 0.935 | 0.899 | 0.898 |

## Coverage by province

| Province | n | fixed | rolling4 | refit_rolling4 |
|---|---|---|---|---|
| BALOCHISTAN | 4289 | 0.653 | 0.749 | 0.746 |
| ISLAMABAD CAPITAL TERRITORY | 29 | 0.690 | 0.759 | 0.759 |
| KHYBER PAKHTUNKHWA | 4348 | 0.894 | 0.936 | 0.937 |
| PUNJAB | 6686 | 0.592 | 0.755 | 0.755 |
| SINDH | 3825 | 0.950 | 0.971 | 0.969 |
