"""Key DGA snow stations — aligned with UPLA paper Table 1."""

from __future__ import annotations

STATIONS: dict[str, dict] = {
    "04520006": {
        "name": "Quebrada Larga",
        "short": "Q. Larga",
        "basin": "Limarí",
        "latitude": -30.28,
        "code_dga": "04520006-K",
        "clean_col": "04520006",
        "raw_col": "04520006",
        "has_swe": True,
        "has_snowcourse": True,
        "region": "Coquimbo",
    },
    "05401007": {
        "name": "Portillo",
        "short": "Portillo",
        "basin": "Aconcagua",
        "latitude": -32.84,
        "code_dga": "05401007-9",
        "clean_col": "05401007_unified",
        "raw_col": "05401007",
        "has_swe": True,
        "has_snowcourse": True,
        "region": "Valparaíso",
    },
    "05703009": {
        "name": "Laguna Negra",
        "short": "L. Negra",
        "basin": "Maipo",
        "latitude": -33.64,
        "code_dga": "05703009-7",
        "clean_col": "05703009",
        "raw_col": "05703009",
        "has_swe": True,
        "has_snowcourse": True,
        "region": "Metropolitana",
    },
    "06020001": {
        "name": "Termas del Flaco",
        "short": "T. Flaco",
        "basin": "Tinguiririca",
        "latitude": -34.93,
        "code_dga": "06020001-7",
        "clean_col": "06020001",
        "raw_col": "06020001",
        "has_swe": True,
        "has_snowcourse": False,
        "region": "O'Higgins",
    },
    "07301000": {
        "name": "Lo Aguirre",
        "short": "Lo Aguirre",
        "basin": "Maule",
        "latitude": -35.58,
        "code_dga": "07301000-0",
        "clean_col": "07301000",
        "raw_col": "07301000",
        "has_swe": True,
        "has_snowcourse": True,
        "region": "Maule",
    },
}

STATION_ORDER = ["04520006", "05401007", "05703009", "06020001", "07301000"]

# North → south (latitude descending: -30°S before -35°S)
STATION_ORDER_BY_LATITUDE = sorted(
    STATION_ORDER, key=lambda sid: STATIONS[sid]["latitude"], reverse=True
)

STATION_COLORS = {
    "04520006": "#2a9d8f",
    "05401007": "#e76f51",
    "05703009": "#457b9d",
    "06020001": "#bc6c25",
    "07301000": "#6a4c93",
}

# Paper methodology (Section 2)
DS_INCREASE_WINDOWS = (3, 5, 7)
SWE_INCREASE_WINDOWS = (3, 5, 7, 15)
# Sum of daily max(0, Δds) over window; 1 = max single-day snowfall depth.
SF_ROLLING_WINDOWS = (1, 3, 5, 7)
SNOWCOURSE_TARGET = (7, 31)  # closest measurement to 31 July
SNOWCOURSE_MAX_DAYS = 21


def station_label(station_id: str, *, with_id: bool = True, with_basin: bool = False) -> str:
    meta = STATIONS[station_id]
    name = str(meta["name"])
    if with_basin and meta.get("basin"):
        name = f"{name} ({meta['basin']})"
    if with_id:
        return f"{name} ({station_id})"
    return name


def station_panel_title(station_id: str) -> str:
    meta = STATIONS[station_id]
    title = str(meta["name"])
    basin = meta.get("basin")
    if basin:
        title = f"{title} · {basin}"
    return title


def processed_sd_path(base_dir: str, station_id: str) -> str:
    import os

    return os.path.join(base_dir, "data", "processed", f"SD_{station_id}.csv")
