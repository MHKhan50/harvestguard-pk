# Sources and provenance

## Primary institutional source

**Pakistan Bureau of Statistics (PBS), National Accounts — Agriculture Statistics / Crop Statistics dashboard.** PBS describes district-level production, yield and cultivation area for 121 crops.

- Dashboard: https://na.data.gov.pk/Crops/Home
- PBS statistics portal: https://www.pbs.gov.pk/
- PBS data dissemination policy: https://www.pbs.gov.pk/data-dissemination/

## Machine-readable extract used by the fetch pipeline

**Data Darbar / Adaad — “Crop area, production and yield by district”.** The catalogue reports 78,425 rows, 9 fields, 108 crops, 123 districts and fiscal years 1981–82 to 2024–25. It identifies PBS Agriculture Statistics via the National Accounts portal as the source and states that the displayed extract was pulled on 2026-09-27. The Parquet file is available at:

- Dataset page: https://darbar.adaad.org/datasets/crops-district-fy/
- Parquet: https://darbar.adaad.org/data/warehouse/crops_district_fy.parquet

The catalogue explicitly documents absent district coverage and unlabelled crop IDs. Read its caveats before merging to district boundaries or making national claims.

## Pakistan-specific research context

- Hussain, A. & Bangash, R. (2017), “Impact of Climate Change on Crops’ Productivity across Selected Agro-ecological Zones in Pakistan”, *The Pakistan Development Review*, 56(2), 163–187. PIDE record: https://pide.org.pk/research/impact-of-climate-change-on-crops-productivity-across-selected-agro-ecological-zones-in-pakistan/
- Arshad et al. (2018), “Climatic variability and thermal stress in Pakistan's rice and wheat systems”, *Ecological Indicators*, 89, 496–506. DOI: https://doi.org/10.1016/j.ecolind.2017.12.014
- Wajid et al. (2017), “Forecasting wheat yield from weather data and MODIS NDVI using Random Forests for Punjab province, Pakistan”, *International Journal of Remote Sensing*. DOI: https://doi.org/10.1080/01431161.2017.1323282

## Licensing and attribution

The PBS policy page states that aggregate statistics and non-confidential datasets are normally released under an open licence and that Tier 1/2 products permit copying/adaptation and commercial/non-commercial reuse with attribution. The Data Darbar catalogue says the source data are reusable under the PBS open licence, instructs users to acknowledge PBS, mark changes, and not present derived figures as official PBS statistics; it also labels its derived data CC BY 4.0. Cite both PBS and Data Darbar, preserve attribution and modification notices, and verify the current policy and upstream terms at retrieval time. The MIT licence in this repository applies to code and the repository-generated synthetic fixture, not to PBS source data.

## Recommended attribution string for an actual-data release

“Source: Pakistan Bureau of Statistics (PBS), National Accounts Agriculture Statistics, retrieved via Data Darbar, ‘Crop area, production and yield by district’ (source pull noted as 2026-09-27). Processed by the authors; derived estimates are not official PBS statistics. Retrieval date and SHA-256 of the source file: [fill in].”
