"""Deterministic synthetic panel generator for software tests only."""
from __future__ import annotations

import csv
import math
import random
from pathlib import Path
from typing import List, Union

CROPS = [
    (1, "Wheat", 2.25),
    (2, "Rice", 2.85),
    (3, "Maize", 3.60),
    (4, "Cotton", 1.95),
    (5, "Sugarcane", 48.0),
]


def generate_synthetic_panel(output: Union[str, Path], seed: int = 17, districts: int = 24) -> Path:
    if districts < 4:
        raise ValueError("districts must be at least 4")
    rng = random.Random(seed)
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["district_code", "district", "province", "crop_id", "crop", "fy", "area_000ha", "production_000t", "yield_t_per_ha"]
    provinces = ["Punjab", "Sindh", "Khyber Pakhtunkhwa", "Balochistan"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for district_index in range(districts):
            district_code = "{:03d}".format(district_index + 1)
            district_name = "Synthetic District {:02d}".format(district_index + 1)
            province = provinces[district_index % len(provinces)]
            district_factor = 0.82 + 0.36 * rng.random()
            for crop_id, crop, base_yield in CROPS:
                crop_factor = 0.88 + 0.24 * rng.random()
                for year in range(1981, 2025):
                    elapsed = year - 1981
                    trend = 1.0 + 0.0018 * elapsed
                    cycle = 0.035 * math.sin(elapsed / 4.5 + district_index * 0.3 + crop_id)
                    noise = rng.gauss(0.0, 0.045)
                    shock = 0.72 if rng.random() < 0.025 else 1.0
                    yield_value = max(0.15, base_yield * district_factor * crop_factor * trend * (1 + cycle + noise) * shock)
                    area = 4.0 + 18.0 * rng.random()
                    if rng.random() < 0.008:
                        continue  # deterministic missing panel-year pattern under the fixed seed
                    writer.writerow({
                        "district_code": district_code,
                        "district": district_name,
                        "province": province,
                        "crop_id": str(crop_id),
                        "crop": crop,
                        "fy": "{}-{:02d}".format(year, (year + 1) % 100),
                        "area_000ha": "{:.4f}".format(area),
                        "production_000t": "{:.6f}".format(area * yield_value),
                        "yield_t_per_ha": "{:.6f}".format(yield_value),
                    })
    return path
