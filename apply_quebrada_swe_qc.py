#!/usr/bin/env python3
"""
Apply Quebrada Larga 2026 pillow SWE QC (SD consistency) in-place.

Usage (from repository root):
  python cleaning_script/apply_quebrada_swe_qc.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from sd_qc_utils import qc_quebrada_larga_swe  # noqa: E402

SD_PATH = PROJECT_ROOT / "Data" / "Station_SnowDepth" / "QUEBRADA_LARGA_SD.csv"
SWE_PATH = PROJECT_ROOT / "Data" / "Station_SWE" / "QUEBRADA_LARGA_SWE.csv"


def main() -> None:
    sd = pd.read_csv(SD_PATH, parse_dates=["date"])
    swe = pd.read_csv(SWE_PATH, parse_dates=["date"])
    n_before = swe.loc[swe["date"].dt.year == 2026, "media"].notna().sum()
    out = qc_quebrada_larga_swe(swe, sd)
    n_after = out.loc[out["date"].dt.year == 2026, "media"].notna().sum()
    out.to_csv(SWE_PATH, index=False, date_format="%Y-%m-%d")
    print(f"Quebrada Larga SWE QC: wrote {SWE_PATH}")
    print(f"  2026 days with media: {n_before} → {n_after}")


if __name__ == "__main__":
    main()
