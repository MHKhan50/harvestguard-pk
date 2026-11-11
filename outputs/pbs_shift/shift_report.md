# Coverage under temporal shift

Cleaning: 74803 rows in, 70225 out; 4355 aggregate rows excluded; 223 overlapping rows dropped; 98 crops.

## Point forecasts (train <= 2015, test 2020-2024, 17896 examples)

| Forecaster | RMSE (log) | MAE (log) |
|---|---|---|
| persistence | 0.4643 | 0.1979 |
| rolling_median | 0.4459 | 0.2127 |
| pooled_ridge | 0.4119 | 0.2064 |

Shock rate 10.0%. Alerts F1: persistence 0.301 (P 0.377, R 0.250); ridge 0.193 (P 0.315, R 0.139).

## Interval coverage, nominal 90%

| Method | Coverage | 95% CI (group bootstrap) | Mean width (log) |
|---|---|---|---|
| fixed | 0.751 | 0.741 to 0.760 | 0.477 |
| rolling4 | 0.839 | 0.831 to 0.845 | 0.862 |
| expanding | 0.814 | 0.806 to 0.821 | 0.692 |
| refit_rolling4 | 0.837 | 0.830 to 0.843 | 0.851 |
| aci_g0.1 | 0.801 | 0.794 to 0.808 | 0.646 |
| aci_g0.5 | 0.884 | 0.879 to 0.889 | 1.790 |

## Coverage by target year

| Year | n | fixed | rolling4 | expanding | refit_rolling4 | aci_g0.1 | aci_g0.5 |
|---|---|---|---|---|---|---|---|
| 2020 | 3261 | 0.718 | 0.718 | 0.718 | 0.718 | 0.718 | 0.718 |
| 2021 | 3626 | 0.735 | 0.802 | 0.785 | 0.802 | 0.763 | 0.988 |
| 2022 | 3673 | 0.711 | 0.817 | 0.785 | 0.814 | 0.765 | 0.798 |
| 2023 | 3651 | 0.751 | 0.898 | 0.857 | 0.895 | 0.843 | 0.993 |
| 2024 | 3685 | 0.836 | 0.944 | 0.913 | 0.942 | 0.908 | 0.908 |

## Coverage by province

| Province | n | fixed | rolling4 | refit_rolling4 |
|---|---|---|---|---|
| BALOCHISTAN | 4075 | 0.658 | 0.749 | 0.744 |
| ISLAMABAD CAPITAL TERRITORY | 21 | 0.762 | 0.809 | 0.809 |
| KHYBER PAKHTUNKHWA | 3951 | 0.900 | 0.939 | 0.939 |
| PUNJAB | 6205 | 0.600 | 0.757 | 0.756 |
| SINDH | 3644 | 0.950 | 0.969 | 0.968 |
