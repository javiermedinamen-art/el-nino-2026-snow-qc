"""Paths for this small repo."""

from __future__ import annotations

from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPTS_DIR.parents[1]
DATA_DIR = PACKAGE_ROOT / "data"
FIGURES_DIR = PACKAGE_ROOT / "figures"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = PACKAGE_ROOT / "outputs"

# QC SWE (full series). SD extension is under station_sd/.
SD_FILES: dict[str, Path] = {}
SWE_FILES: dict[str, Path] = {
    "04520006": DATA_DIR / "station_swe" / "QUEBRADA_LARGA_SWE.csv",
    "05401007": DATA_DIR / "station_swe" / "PORTILLO_SWE.csv",
    "05703009": DATA_DIR / "station_swe" / "LAGUNA_NEGRA_SWE.csv",
    "06020001": DATA_DIR / "station_swe" / "TERMAS_DEL_FLACO_SWE.csv",
    "07301000": DATA_DIR / "station_swe" / "LO_AGUIRRE_SWE.csv",
}

SNOWCOURSE_FILES: dict[str, Path] = {}
ONI_SEASONAL_FILE = DATA_DIR / "enso" / "oni_v6_seasonal.csv"

FIG_CLIMATOLOGY = FIGURES_DIR / "climatology"
FIG_RETURN_PERIOD = FIGURES_DIR / "return_period"
FIG_SNOWCOURSE = FIGURES_DIR / "snowcourse"
FIG_ENSO = FIGURES_DIR / "enso"
FIG_DATA_AVAILABILITY = FIGURES_DIR / "data_availability"

OUT_RETURN_PERIOD = OUTPUTS_DIR / "return_period"
OUT_ENSO = OUTPUTS_DIR / "enso"
OUT_STATIONS = OUT_RETURN_PERIOD / "stations"
