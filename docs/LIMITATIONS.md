# Limitations and threats to validity

1. **Official data not bundled:** the repository contains a synthetic smoke-test panel only. Real-data performance remains unmeasured until the PBS-derived panel is fetched and the experiment is run.
2. **Secondary packaging:** the bulk Parquet is distributed by Data Darbar and states that its source is the PBS National Accounts crop portal. Researchers should verify the upstream values against PBS before formal publication and archive the exact source version/hash.
3. **Coverage gaps:** the catalogue notes that 33 of 156 districts in its geography frame have no crop rows, including all AJK and GB districts in this extract, several Karachi districts and newer districts. Coverage varies by crop; many fruits/vegetables have shorter histories than major crops.
4. **Administrative changes:** district boundaries, district codes, crop names and reporting practices may change over decades. A code match is not proof of stable geography or measurement.
5. **Yield is an administrative aggregate:** it can reflect area/production measurement error, revisions, weather, irrigation, inputs, pests, policy, market incentives and other omitted variables. The model cannot attribute causes.
6. **Short panel for some groups:** only three historical observations are required, but a small number of annual observations can produce unstable forecasts. The code does not infer missing years as zero.
7. **Temporal distribution shift:** the fixed 2015/2016–2019/2020–2024 split may expose the model to structural changes. Conformal coverage can fail under non-exchangeability.
8. **Pooled model heterogeneity:** crop types and agro-ecological zones differ substantially. A single pooled ridge model is a baseline research design, not necessarily the best agronomic model.
9. **Shock threshold is operational:** the 15% decline from the prior-three-observation median is a benchmark label, not an official food-security threshold. Sensitivity analyses are needed.
10. **No farm-level advice:** outputs are district–crop statistical alerts, not recommendations for individual farmers, planting dates, input use or procurement decisions.
11. **No climate covariates:** the v0.1.0 protocol deliberately focuses on leakage-safe historical yield-panel prediction. It does not estimate climate effects. Adding weather/remote-sensing features requires separate source validation and a new preregistered protocol.
12. **Synthetic smoke data:** synthetic metrics validate code execution only and must never be reported as evidence of forecast skill in Pakistan.
