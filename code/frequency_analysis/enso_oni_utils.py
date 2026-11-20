"""Snowcourse Jul-31 helpers and CPC ONI v6 season alignment."""

from __future__ import annotations

import pandas as pd

# NOAA CPC ONI v6: each column is a 3-month running mean; the label is the
# center month (e.g. JJA = mean of Jun + Jul + Aug anomalies).
ONI_SEASON_BY_MONTH: dict[int, str] = {
    1: "DJF",
    2: "JFM",
    3: "FMA",
    4: "MAM",
    5: "AMJ",
    6: "MJJ",
    7: "JJA",
    8: "JAS",
    9: "ASO",
    10: "SON",
    11: "OND",
    12: "NDJ",
}

# Fallback order when the primary season is not yet published (e.g. 2026).
_ONI_FALLBACK: dict[str, list[str]] = {
    "JAS": ["JJA", "MJJ", "AMJ"],
    "JJA": ["MJJ", "JAS", "AMJ"],
    "MJJ": ["AMJ", "JJA", "JAS"],
    "ASO": ["JAS", "JJA", "MJJ"],
}


def oni_primary_season(event_date: pd.Timestamp) -> str:
    return ONI_SEASON_BY_MONTH[int(event_date.month)]


def oni_for_event_date(oni_row: pd.Series, event_date: pd.Timestamp) -> tuple[float, str]:
    """
    Match a snowcourse survey to the CPC 3-month ONI whose center month is the
    survey month (Jul → JJA, Aug → JAS, …). If that season is missing (partial
    calendar year), use the nearest earlier overlapping season.
    """
    primary = oni_primary_season(event_date)
    for season in [primary, *_ONI_FALLBACK.get(primary, [])]:
        value = oni_row.get(season)
        if pd.notna(value):
            return float(value), season
    return float("nan"), primary


def snowcourse_closest_jul31(
    snowcourse: pd.DataFrame,
    year: int,
    *,
    max_days: int = 21,
) -> dict | None:
    """Closest snowcourse survey to 31 July for one year."""
    data = snowcourse[snowcourse["date"].dt.year == year].dropna(
        subset=["ds_cm", "swe_mm"], how="any"
    )
    if data.empty:
        return None

    target = pd.Timestamp(year=year, month=7, day=31)
    data = data.copy()
    data["days_from_jul31"] = (data["date"] - target).abs().dt.days
    idx = data["days_from_jul31"].idxmin()
    row = data.loc[idx]
    days = int(row["days_from_jul31"])
    return {
        "year": year,
        "ds_cm": float(row["ds_cm"]),
        "swe_mm": float(row["swe_mm"]),
        "event_date": pd.Timestamp(row["date"]),
        "days_from_jul31": days,
        "within_21d": days <= max_days,
    }


def attach_oni_to_jul31(
    jul31: pd.DataFrame,
    oni: pd.DataFrame,
) -> pd.DataFrame:
    """Add event-aligned ONI columns to a Jul-31 snowcourse table."""
    oni = oni.set_index("year")
    rows: list[dict] = []
    for _, row in jul31.iterrows():
        year = int(row["year"])
        event_date = pd.to_datetime(row["event_date"])
        if year not in oni.index:
            oni_val, oni_season = float("nan"), oni_primary_season(event_date)
        else:
            oni_val, oni_season = oni_for_event_date(oni.loc[year], event_date)
        out = row.to_dict()
        out["oni_value"] = oni_val
        out["oni_season"] = oni_season
        out["strong_el_nino"] = bool(oni_val >= 1.5) if pd.notna(oni_val) else False
        out["el_nino"] = bool(oni_val >= 0.5) if pd.notna(oni_val) else False
        rows.append(out)
    return pd.DataFrame(rows)
