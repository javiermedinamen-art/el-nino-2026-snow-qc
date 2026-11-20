"""SWE cleaning: MAD spike detection + rolling-median smoothing (UPLA El Niño 2026)."""

from __future__ import annotations

import numpy as np
import pandas as pd

SWE_COLS = ("min", "media", "max")


def detect_spikes_mad(
    data: pd.DataFrame,
    cols: list[str],
    *,
    fwindow: int = 3,
    k: float = 4.0,
    abs_thr: float = 100.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Flag isolated spikes via MAD; set flagged values to NaN (abs_thr in mm for SWE)."""
    df_clean = data.copy()
    flags = pd.DataFrame(0, index=df_clean.index, columns=cols, dtype="int8")
    win_size = 2 * fwindow + 1

    for col in cols:
        s = df_clean[col].astype(float)
        med = s.rolling(win_size, center=True).median()
        mad = (s - med).abs().rolling(win_size, center=True).median()
        mad_safe = mad.replace(0, np.nan)

        z = (s - med).abs() / mad_safe
        prev_diff = (s - s.shift(1)).abs()
        next_diff = (s - s.shift(-1)).abs()
        neigh_diff = (s.shift(1) - s.shift(-1)).abs()

        safe_prev = prev_diff.fillna(np.inf)
        safe_next = next_diff.fillna(np.inf)

        spike_mad = (
            (mad_safe > 0)
            & (z > k)
            & (safe_prev > k * mad_safe)
            & (safe_next > k * mad_safe)
            & (neigh_diff.fillna(0) < k * mad_safe)
        )
        spike_abs = (prev_diff > abs_thr) & (next_diff > abs_thr)
        spike = spike_mad | spike_abs

        df_clean.loc[spike, col] = np.nan
        flags.loc[spike, col] = 1

    return df_clean, flags


def clip_swe_nonnegative(data: pd.DataFrame, cols: list[str] | None = None) -> pd.DataFrame:
    out = data.copy()
    use = list(cols or SWE_COLS)
    for col in use:
        if col not in out.columns:
            continue
        s = pd.to_numeric(out[col], errors="coerce")
        out[col] = s.clip(lower=0)
    return out


def cap_swe_physical(
    data: pd.DataFrame,
    cols: list[str],
    *,
    max_mm: float,
) -> pd.DataFrame:
    out = clip_swe_nonnegative(data, cols)
    for col in cols:
        s = out[col].astype(float)
        out.loc[s.gt(max_mm), col] = np.nan
    return out


def smooth_swe_series(
    data: pd.DataFrame,
    cols: list[str],
    *,
    window: int = 3,
    interpolate_limit: int = 2,
) -> pd.DataFrame:
    out = data.copy()
    for col in cols:
        s = out[col].astype(float)
        s = s.interpolate(limit=interpolate_limit, limit_direction="both")
        s = s.rolling(window, center=True, min_periods=1).median()
        out[col] = s
    return out


def clean_swe_dataframe(
    df: pd.DataFrame,
    *,
    max_mm: float,
    fwindow: int = 3,
    k: float = 4.0,
    abs_thr_mm: float = 100.0,
    smooth_window: int = 3,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Clean min/media/max; returns cleaned frame and spike counts per column."""
    work = df.copy()
    for col in SWE_COLS:
        if col not in work.columns:
            raise ValueError(f"Missing column {col}")

    present = [c for c in SWE_COLS if work[c].notna().any()]
    if not present:
        return work, {c: 0 for c in SWE_COLS}

    work = cap_swe_physical(work, present, max_mm=max_mm)
    cleaned, flags = detect_spikes_mad(
        work,
        present,
        fwindow=fwindow,
        k=k,
        abs_thr=abs_thr_mm,
    )
    cleaned = smooth_swe_series(cleaned, present, window=smooth_window)
    cleaned = clip_swe_nonnegative(cleaned, present)
    counts = {
        col: int(flags[col].sum()) if col in flags.columns else 0 for col in SWE_COLS
    }
    return cleaned, counts
