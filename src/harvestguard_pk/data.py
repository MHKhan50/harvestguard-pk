"""Input validation and optional PBS-derived Parquet-to-CSV preparation."""
from __future__ import annotations

import csv
import math
import re
import urllib.request
from pathlib import Path
from typing import Dict, List, Union

PBS_PARQUET_URL = "https://darbar.adaad.org/data/warehouse/crops_district_fy.parquet"
REQUIRED_COLUMNS = {
    "district_code", "district", "province", "crop_id", "crop", "fy",
    "area_000ha", "production_000t", "yield_t_per_ha",
}
_FY_RE = re.compile(r"^(\d{4})\s*[-/]\s*(?:\d{2}|\d{4})$")


def parse_fiscal_year(value: str) -> int:
    match = _FY_RE.match(str(value).strip())
    if not match:
        raise ValueError("Invalid fiscal year {!r}; expected e.g. '2024-25'".format(value))
    return int(match.group(1))


def read_panel_csv(path: Union[str, Path]) -> List[Dict[str, object]]:
    """Read and validate the PBS/Data-Darbar-compatible crop panel schema."""
    rows: List[Dict[str, object]] = []
    seen = set()
    with Path(path).open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError("Input CSV missing required columns: {}".format(", ".join(sorted(missing))))
        for line_number, raw in enumerate(reader, start=2):
            crop = (raw.get("crop") or "").strip()
            if not crop or "unnamed crop" in crop.lower():
                continue
            try:
                year = parse_fiscal_year(raw["fy"])
                area = float(raw["area_000ha"])
                production = float(raw["production_000t"])
                yield_value = float(raw["yield_t_per_ha"])
            except (TypeError, ValueError) as exc:
                raise ValueError("Invalid row {}: {}".format(line_number, exc)) from exc
            values = (area, production, yield_value)
            if not all(math.isfinite(value) for value in values):
                continue
            if area <= 0 or production <= 0 or yield_value <= 0:
                continue
            district_code = str(raw["district_code"]).strip()
            crop_id = str(raw["crop_id"]).strip()
            province = str(raw["province"]).strip()
            district = str(raw["district"]).strip()
            if not district_code or not crop_id or not province or not district:
                continue
            key = (district_code, crop_id, year)
            if key in seen:
                raise ValueError("Duplicate district-crop-fiscal-year key at row {}: {}".format(line_number, key))
            seen.add(key)
            rows.append({
                "district_code": district_code,
                "district": district,
                "province": province,
                "crop_id": crop_id,
                "crop": crop,
                "fy": str(raw["fy"]).strip(),
                "year": year,
                "area_000ha": area,
                "production_000t": production,
                "yield_t_per_ha": yield_value,
            })
    if not rows:
        raise ValueError("No valid crop-yield rows remain after validation/filtering")
    rows.sort(key=lambda row: (int(row["year"]), str(row["district_code"]), str(row["crop_id"])))
    return rows


def fetch_pbs_panel(output_csv: Union[str, Path], source_url: str = PBS_PARQUET_URL) -> Path:
    """Download source Parquet and convert it to CSV using optional DuckDB."""
    try:
        import duckdb  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Optional dependency missing. Install with: python -m pip install -e '.[data]'") from exc

    output = Path(output_csv)
    output.parent.mkdir(parents=True, exist_ok=True)
    parquet_path = output.with_suffix(".source.parquet")
    temporary_csv = output.with_suffix(output.suffix + ".tmp")
    request = urllib.request.Request(source_url, headers={"User-Agent": "HarvestGuard-PK/0.1.0 research-data-preparation"})
    try:
        if parquet_path.exists():
            parquet_path.unlink()
        if temporary_csv.exists():
            temporary_csv.unlink()
        with urllib.request.urlopen(request, timeout=60) as response, parquet_path.open("wb") as target:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                target.write(chunk)
        if parquet_path.stat().st_size == 0:
            raise RuntimeError("Downloaded source Parquet is empty")
        parquet_sql = str(parquet_path.resolve()).replace("'", "''")
        output_sql = str(temporary_csv.resolve()).replace("'", "''")
        connection = duckdb.connect(database=":memory:")
        try:
            connection.execute(
                "COPY (SELECT * FROM read_parquet('{}')) TO '{}' (FORMAT CSV, HEADER, DELIMITER ',')".format(parquet_sql, output_sql)
            )
        finally:
            connection.close()
        # Validate the converted schema and rows before atomically replacing output.
        read_panel_csv(temporary_csv)
        temporary_csv.replace(output)
        return output
    except Exception:
        if temporary_csv.exists():
            temporary_csv.unlink()
        raise
    finally:
        if parquet_path.exists():
            parquet_path.unlink()
