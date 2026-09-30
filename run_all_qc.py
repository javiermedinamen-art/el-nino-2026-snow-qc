#!/usr/bin/env python3
"""Run publication SWE cleaning + site SD/SWE QC (order used in analysis pipeline)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def run(name: str, script: str) -> None:
    path = SCRIPT_DIR / script
    print(f"\n=== {name} ===")
    subprocess.run([sys.executable, str(path)], check=True)


def main() -> None:
    run("SWE automatic cleaning", "clean_swe_automatic.py")
    run("Laguna Negra SD QC", "apply_sd_qc.py")
    run("Quebrada Larga SWE QC (2026)", "apply_quebrada_swe_qc.py")
    print("\nDone. See cleaning_script/README.md and QC_PARAMETERS.csv for disclosure.")


if __name__ == "__main__":
    main()
