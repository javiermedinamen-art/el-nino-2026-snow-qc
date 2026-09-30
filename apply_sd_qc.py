#!/usr/bin/env python3
"""
Apply Laguna Negra SD QC in-place on Data/Station_SnowDepth/LAGUNA_NEGRA_SD.csv.

Quebrada Larga SWE QC runs in apply_quebrada_swe_qc.py (needs SD + SWE).

Usage (from repository root):
  python cleaning_script/apply_sd_qc.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from sd_qc_utils import qc_laguna_negra_zeros  # noqa: E402

SD_PATH = PROJECT_ROOT / "Data" / "Station_SnowDepth" / "LAGUNA_NEGRA_SD.csv"


def main() -> None:
    if not SD_PATH.exists():
        raise SystemExit(f"Missing {SD_PATH}")
    df = pd.read_csv(SD_PATH, parse_dates=["date"])
    before = df["SD_mean_clean"].eq(0).sum()
    out = qc_laguna_negra_zeros(df)
    after = out["SD_mean_clean"].eq(0).sum()
    out.to_csv(SD_PATH, index=False, date_format="%Y-%m-%d")
    print(f"Laguna Negra SD QC: wrote {SD_PATH}")
    print(f"  exact zeros in SD_mean_clean: {before} → {after}")


if __name__ == "__main__":
    main()
