"""Leakage-safe supervised feature construction for district-crop panels."""
from __future__ import annotations

import math
import statistics
from collections import defaultdict
from typing import Dict, List, Sequence

FEATURE_NAMES = [
    "lag1_log_yield",
    "lag2_log_yield",
    "rolling3_log_median",
    "lag1_log_area",
    "lagged_log_area_growth",
    "province_crop_log_median",
    "target_year_scaled",
    "gap_years_lag1",
    "gap_years_lag2",
]


def build_supervised_rows(panel_rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    """Create one-step-ahead samples; no row from year t enters features for year t."""
    by_year = defaultdict(list)
    for row in panel_rows:
        by_year[int(row["year"])].append(row)

    group_history = defaultdict(list)
    province_crop_history = defaultdict(list)
    examples: List[Dict[str, object]] = []

    for year in sorted(by_year):
        current = sorted(by_year[year], key=lambda item: (str(item["district_code"]), str(item["crop_id"])))
        # Featurize the whole year before adding any current-year observations to history.
        for row in current:
            group_id = "{}|{}".format(row["district_code"], row["crop_id"])
            history = group_history[group_id]
            if len(history) < 3:
                continue
            previous = history[-1]
            second_previous = history[-2]
            last_three = history[-3:]
            previous_median = statistics.median(float(item["yield_t_per_ha"]) for item in last_three)
            province_crop_key = (str(row["province"]), str(row["crop_id"]))
            aggregate_history = province_crop_history[province_crop_key]
            aggregate_median = statistics.median(aggregate_history) if aggregate_history else previous_median
            previous_area = float(previous["area_000ha"])
            second_area = float(second_previous["area_000ha"])
            area_growth = math.log(previous_area / second_area) if previous_area > 0 and second_area > 0 else 0.0
            features = [
                math.log(float(previous["yield_t_per_ha"])),
                math.log(float(second_previous["yield_t_per_ha"])),
                math.log(previous_median),
                math.log(previous_area),
                area_growth,
                math.log(aggregate_median),
                (year - 1981) / 40.0,
                float(year - int(previous["year"])),
                float(year - int(second_previous["year"])),
            ]
            examples.append({
                "features": features,
                "target_log": math.log(float(row["yield_t_per_ha"])),
                "target_yield": float(row["yield_t_per_ha"]),
                "previous_median_yield": previous_median,
                "group_id": group_id,
                "district_code": str(row["district_code"]),
                "district": str(row["district"]),
                "province": str(row["province"]),
                "crop_id": str(row["crop_id"]),
                "crop": str(row["crop"]),
                "fy": str(row["fy"]),
                "target_year": year,
            })
        # Update history only after all features for this year have been computed.
        for row in current:
            group_id = "{}|{}".format(row["district_code"], row["crop_id"])
            group_history[group_id].append(row)
            province_crop_history[(str(row["province"]), str(row["crop_id"]))].append(float(row["yield_t_per_ha"]))

    return examples
