"""
Quality-control parameters for UPLA El Niño 2026 paper (automatic SD/SWE).

Disclosed in cleaning_script/README.md and QC_PARAMETERS.csv.
"""

from __future__ import annotations

# Automatic SWE is set to 0 when gated SD (rolling max) is missing or below this (cm).
SWE_ZERO_UNLESS_SD_MIN_CM = 2.0
SWE_SD_GATE_ROLLING_DAYS = 7
# Linear infill across short SWE=0 gaps when neighbors indicate an active pack.
SWE_INFILL_MAX_GAP_DAYS = 7
SWE_INFILL_MIN_CONTEXT_MM = 15.0

SWE_MAX_MM: dict[str, float] = {
    "04520006": 3500.0,
    "05401007": 1200.0,
    "05703009": 3000.0,
    "06020001": 1200.0,
    "07301000": 1200.0,
}

SWE_DEFAULT_CLEAN = {
    "fwindow": 3,
    "k": 4.0,
    "abs_thr_mm": 100.0,
    "smooth_window": 3,
}

SWE_STATION_CLEAN: dict[str, dict] = {
    "05401007": {
        "fwindow": 3,
        "k": 3.5,
        "abs_thr_mm": 75.0,
        "smooth_window": 9,
    },
}

QUEBRADA_SWE_LIMIT_MM = 3500.0
QUEBRADA_SWE_SD_MIN_CM = 50.0
QUEBRADA_SWE_RATIO_MIN = 0.05
QUEBRADA_SWE_RATIO_MAX = 12.5
QUEBRADA_SWE_SHALLOW_SD_MIN_CM = 5.0
QUEBRADA_SWE_SHALLOW_SD_MAX_CM = 10.0
QUEBRADA_SWE_SHALLOW_MAX_MM = 40.0
QUEBRADA_SWE_QC_YEARS = (2026,)

LAGUNA_SD_ZERO_PREV_MIN_CM = 50.0
LAGUNA_SD_ZERO_FFILL_LIMIT_DAYS = 3

STATION_ORDER = [
    "04520006",
    "05401007",
    "05703009",
    "06020001",
    "07301000",
]

STATION_NAMES: dict[str, str] = {
    "04520006": "Quebrada Larga",
    "05401007": "Portillo",
    "05703009": "Laguna Negra",
    "06020001": "Termas del Flaco",
    "07301000": "Lo Aguirre",
}

SWE_FILENAMES: dict[str, str] = {
    "04520006": "QUEBRADA_LARGA_SWE.csv",
    "05401007": "PORTILLO_SWE.csv",
    "05703009": "LAGUNA_NEGRA_SWE.csv",
    "06020001": "TERMAS_DEL_FLACO_SWE.csv",
    "07301000": "LO_AGUIRRE_SWE.csv",
}

SD_FILENAMES: dict[str, str] = {
    "04520006": "QUEBRADA_LARGA_SD.csv",
    "05401007": "PORTILLO_SD.csv",
    "05703009": "LAGUNA_NEGRA_SD.csv",
    "06020001": "TERMAS_DEL_FLACO_SD.csv",
    "07301000": "LO_AGUIRRE_SD.csv",
}
