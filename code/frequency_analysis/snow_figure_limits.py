"""Shared column y-axis limits: one scale for all d_s panels, one for all SWE panels."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from climatology_utils import filter_apr_dec  # noqa: E402
from enso_oni_utils import snowcourse_closest_jul31  # noqa: E402
from paths import PROCESSED_DIR, SNOWCOURSE_FILES  # noqa: E402
from stations_config import SNOWCOURSE_MAX_DAYS, STATIONS  # noqa: E402

CURRENT_YEAR = 2026
MARGIN_RATIO = 0.06
YSTEP_CM = 50
YSTEP_SWE_MM = 100


def _climatology_plot_peak(station_id: str, *, value_col: str, swe: bool = False) -> float:
    """Max of layers drawn on climatology panels: mean, p95 envelope, and 2026 series."""
    fname = f"SWE_{station_id}.csv" if swe else f"SD_{station_id}.csv"
    col = value_col if swe else "SD_mean_clean"
    path = PROCESSED_DIR / fname
    if not path.exists():
        return 0.0
    df = pd.read_csv(path, parse_dates=["date"])
    if swe:
        sd_path = PROCESSED_DIR / f"SD_{station_id}.csv"
        if sd_path.exists():
            cleaning = SCRIPT_DIR.parents[1] / "cleaning_script"
            if str(cleaning) not in sys.path:
                sys.path.insert(0, str(cleaning))
            from sd_qc_utils import align_swe_with_sd  # noqa: WPS433

            sd = pd.read_csv(sd_path, parse_dates=["date"])
            df = align_swe_with_sd(df, sd)
    df = df.dropna(subset=[col])
    if df.empty:
        return 0.0
    df = filter_apr_dec(df)
    hist = df[df["date"].dt.year < CURRENT_YEAR]
    current = df[df["date"].dt.year == CURRENT_YEAR][col]
    if hist.empty:
        return float(current.max()) if not current.empty else 0.0
    clim = hist.groupby(hist["date"].dt.dayofyear)[col].agg(
        mean="mean",
        p95=lambda x: np.percentile(x, 95),
    )
    peak = max(float(clim["p95"].max()), float(clim["mean"].max()))
    if not current.empty:
        peak = max(peak, float(current.max()))
    return peak


def _load_snowcourse(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.dropna(subset=["snowdepth", "swe"], how="any")
    return pd.DataFrame(
        {
            "date": df["date"],
            "year": df["date"].dt.year,
            "ds_cm": pd.to_numeric(df["snowdepth"], errors="coerce"),
            "swe_mm": pd.to_numeric(df["swe"], errors="coerce"),
        }
    ).dropna(subset=["date"]).sort_values("date")


def _snowcourse_jul31_series(sc: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year, group in sc.groupby("year"):
        valid = group.dropna(subset=["ds_cm", "swe_mm"], how="any")
        if valid.empty:
            continue
        target = pd.Timestamp(year=int(year), month=7, day=31)
        valid = valid.copy()
        valid["days_from_jul31"] = (valid["date"] - target).abs().dt.days
        idx = valid["days_from_jul31"].idxmin()
        if int(valid.loc[idx, "days_from_jul31"]) > SNOWCOURSE_MAX_DAYS:
            continue
        rows.append(
            {
                "year": int(year),
                "ds_cm": float(valid.loc[idx, "ds_cm"]),
                "swe_mm": float(valid.loc[idx, "swe_mm"]),
            }
        )
    return pd.DataFrame(rows)


def _snowcourse_figure_peak(station_id: str, col: str) -> float:
    """Max y of Jul-31 snowcourse scatter (+ 2026 diamond when shown)."""
    sc_path = SNOWCOURSE_FILES.get(station_id)
    if not sc_path or not sc_path.exists():
        return 0.0
    sc = _load_snowcourse(sc_path)
    jul31 = _snowcourse_jul31_series(sc)
    if jul31.empty and col not in sc.columns:
        return 0.0
    vals = jul31[col].astype(float) if not jul31.empty else pd.Series(dtype=float)
    if CURRENT_YEAR not in jul31["year"].values:
        extra = snowcourse_closest_jul31(sc, CURRENT_YEAR, max_days=999)
        if extra is not None:
            v = extra["ds_cm"] if col == "ds_cm" else extra["swe_mm"]
            vals = pd.concat([vals, pd.Series([float(v)])], ignore_index=True)
    if vals.dropna().empty:
        return 0.0
    return float(vals.max())


def _column_top_from_peak(peak: float, *, step: float) -> float:
    if peak <= 0:
        return step
    with_margin = peak * (1.0 + MARGIN_RATIO)
    return float(step * math.ceil(with_margin / step))


def global_column_ylimits(climatology_station_ids: list[str]) -> dict[str, tuple[float, float]]:
    """
    One y-range for every d_s panel and one for every SWE panel (Fig. 3 & Fig. 4).

    Upper bound = max over all stations of (climatology curves + snowcourse scatter),
    with margin, rounded up to ``YSTEP_CM`` / ``YSTEP_SWE_MM`` so every point is visible.
    """
    ds_peak = 0.0
    swe_peak = 0.0
    for sid in climatology_station_ids:
        ds_peak = max(ds_peak, _climatology_plot_peak(sid, value_col="SD_mean_clean", swe=False))
        swe_peak = max(
            swe_peak, _climatology_plot_peak(sid, value_col="media", swe=True)
        )
        if STATIONS[sid].get("has_snowcourse"):
            ds_peak = max(ds_peak, _snowcourse_figure_peak(sid, "ds_cm"))
            swe_peak = max(swe_peak, _snowcourse_figure_peak(sid, "swe_mm"))

    return {
        "ds": (0.0, _column_top_from_peak(ds_peak, step=YSTEP_CM)),
        "swe": (0.0, _column_top_from_peak(swe_peak, step=YSTEP_SWE_MM)),
    }
