#!/usr/bin/env python3
"""
Clean automatic-station SWE CSVs under Data/Station_SWE/.

Backs up each file once to Data/Station_SWE/_original_backup/ before first clean.
Always reads from backup when present so re-runs do not compound smoothing.

Usage (from repository root):
  python cleaning_script/clean_swe_automatic.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from station_qc_config import (  # noqa: E402
    STATION_NAMES,
    STATION_ORDER,
    SWE_DEFAULT_CLEAN,
    SWE_FILENAMES,
    SWE_MAX_MM,
    SWE_STATION_CLEAN,
)
from swe_clean_utils import clean_swe_dataframe  # noqa: E402

SWE_DIR = PROJECT_ROOT / "Data" / "Station_SWE"
BACKUP_DIR = SWE_DIR / "_original_backup"


def backup_if_needed(path: Path) -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    dest = BACKUP_DIR / path.name
    if not dest.exists():
        shutil.copy2(path, dest)
        print(f"  backup → {dest}")


def clean_file(station_id: str, path: Path) -> None:
    if not path.exists():
        print(f"  SKIP {station_id}: missing {path.name}")
        return

    backup_if_needed(path)
    backup = BACKUP_DIR / path.name
    src = backup if backup.exists() else path
    df = pd.read_csv(src, parse_dates=["date"])
    max_mm = SWE_MAX_MM.get(station_id, 3500.0)
    kwargs = {**SWE_DEFAULT_CLEAN, **SWE_STATION_CLEAN.get(station_id, {})}
    cleaned, spikes = clean_swe_dataframe(df, max_mm=max_mm, **kwargs)
    cleaned.to_csv(path, index=False, date_format="%Y-%m-%d")
    name = STATION_NAMES[station_id]
    print(
        f"  {name} ({station_id}): spikes nulled "
        f"min={spikes['min']} media={spikes['media']} max={spikes['max']} → {path.name}"
    )


def main() -> None:
    print("SWE cleaning (automatic stations only)")
    for station_id in STATION_ORDER:
        fname = SWE_FILENAMES.get(station_id)
        if not fname:
            continue
        clean_file(station_id, SWE_DIR / fname)
    print(f"Originals preserved under {BACKUP_DIR}/")


if __name__ == "__main__":
    main()
