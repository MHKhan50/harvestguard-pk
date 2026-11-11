# Exploratory diagnosis (added after the shift results)

## Calibration vs test composition, with fixed-interval coverage

| Province | Cal. share | Cal. coverage | Test share | Test coverage |
|---|---|---|---|---|
| BALOCHISTAN | 0.188 | 0.906 | 0.228 | 0.658 |
| ISLAMABAD CAPITAL TERRITORY | 0.006 | 0.880 | 0.001 | 0.762 |
| KHYBER PAKHTUNKHWA | 0.203 | 0.869 | 0.221 | 0.900 |
| PUNJAB | 0.419 | 0.885 | 0.347 | 0.600 |
| SINDH | 0.185 | 0.963 | 0.204 | 0.950 |

| Years of history | Cal. share | Cal. coverage | Test share | Test coverage |
|---|---|---|---|---|
| 11-20 | 0.023 | 0.912 | 0.480 | 0.755 |
| 21+ | 0.075 | 0.906 | 0.083 | 0.867 |
| 3-5 | 0.224 | 0.884 | 0.045 | 0.639 |
| 6-10 | 0.679 | 0.904 | 0.391 | 0.734 |

## Province-wise (Mondrian) vs pooled radius

| Method | Coverage | 95% CI | Mean width (log) |
|---|---|---|---|
| pooled_fixed | 0.751 | 0.742 to 0.760 | 0.477 |
| mondrian_fixed | 0.757 | 0.749 to 0.766 | 0.478 |
| pooled_rolling4 | 0.839 | 0.831 to 0.846 | 0.862 |
| mondrian_rolling4 | 0.849 | 0.842 to 0.855 | 0.788 |

| Year | pooled_fixed | mondrian_fixed | pooled_rolling4 | mondrian_rolling4 |
|---|---|---|---|---|
| 2020 | 0.718 | 0.728 | 0.718 | 0.728 |
| 2021 | 0.735 | 0.740 | 0.802 | 0.838 |
| 2022 | 0.711 | 0.717 | 0.817 | 0.827 |
| 2023 | 0.751 | 0.755 | 0.898 | 0.905 |
| 2024 | 0.836 | 0.843 | 0.944 | 0.931 |

| Province | n | pooled_fixed | mondrian_fixed | pooled_rolling4 | mondrian_rolling4 |
|---|---|---|---|---|---|
| BALOCHISTAN | 4075 | 0.658 (w 0.48) | 0.651 (w 0.46) | 0.749 (w 0.87) | 0.815 (w 1.16) |
| ISLAMABAD CAPITAL TERRITORY | 21 | 0.762 (w 0.48) | 0.809 (w 0.56) | 0.809 (w 0.69) | 0.809 (w 0.67) |
| KHYBER PAKHTUNKHWA | 3951 | 0.900 (w 0.48) | 0.929 (w 0.62) | 0.939 (w 0.86) | 0.926 (w 0.59) |
| PUNJAB | 6205 | 0.600 (w 0.48) | 0.631 (w 0.52) | 0.757 (w 0.85) | 0.791 (w 0.99) |
| SINDH | 3644 | 0.950 (w 0.48) | 0.906 (w 0.27) | 0.969 (w 0.86) | 0.900 (w 0.25) |

Provinces using the pooled radius (fewer than 50 calibration residuals): ISLAMABAD CAPITAL TERRITORY
