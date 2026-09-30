"""Snow depth (SD) and site-specific SWE post-QC for UPLA El Niño 2026."""

from __future__ import annotations

import numpy as np
import pandas as pd

from station_qc_config import (
    LAGUNA_SD_ZERO_FFILL_LIMIT_DAYS,
    LAGUNA_SD_ZERO_PREV_MIN_CM,
    SWE_INFILL_MAX_GAP_DAYS,
    SWE_INFILL_MIN_CONTEXT_MM,
    SWE_SD_GATE_ROLLING_DAYS,
    SWE_ZERO_UNLESS_SD_MIN_CM,
    QUEBRADA_SWE_LIMIT_MM,
    QUEBRADA_SWE_QC_YEARS,
    QUEBRADA_SWE_RATIO_MAX,
    QUEBRADA_SWE_RATIO_MIN,
    QUEBRADA_SWE_SD_MIN_CM,
    QUEBRADA_SWE_SHALLOW_MAX_MM,
    QUEBRADA_SWE_SHALLOW_SD_MAX_CM,
    QUEBRADA_SWE_SHALLOW_SD_MIN_CM,
)


def qc_laguna_negra_zeros(out: pd.DataFrame) -> pd.DataFrame:
    """
    Null abrupt SD = 0 when the previous valid depth (up to 3-day gap-fill) was > 50 cm.
    Applies to SD_mean_clean and SD_mean_raw when raw is also zero.
    """
    out = out.sort_values("date").copy()
    s = out["SD_mean_clean"]
    prev_valid = s.ffill(limit=LAGUNA_SD_ZERO_FFILL_LIMIT_DAYS).shift(1)
    bad = s.eq(0) & prev_valid.gt(LAGUNA_SD_ZERO_PREV_MIN_CM)
    out.loc[bad, "SD_mean_clean"] = pd.NA
    raw_bad = bad & out["SD_mean_raw"].eq(0)
    out.loc[raw_bad, "SD_mean_raw"] = pd.NA
    return out


def qc_quebrada_larga_swe(
    swe: pd.DataFrame,
    sd: pd.DataFrame,
    *,
    years: tuple[int, ...] = QUEBRADA_SWE_QC_YEARS,
) -> pd.DataFrame:
    """
    Null pillow SWE on selected years when inconsistent with same-day SD_mean_clean.

    Reject if: SWE < 0 or |SWE| > limit; missing SD; SD < 50 cm;
    SD >= 10 cm and SWE/SD outside [0.05, 12.5];
    5 cm <= SD < 10 cm and SWE > 40 mm.
    """
    out = swe.sort_values("date").copy()
    merged = out.merge(sd[["date", "SD_mean_clean"]], on="date", how="left")
    year_mask = merged["date"].dt.year.isin(years)
    has_swe = merged["media"].notna()

    sd_v = merged["SD_mean_clean"]
    swe_v = merged["media"]
    ratio = swe_v / sd_v

    bad = year_mask & has_swe & (
        (swe_v < 0)
        | (swe_v.abs() > QUEBRADA_SWE_LIMIT_MM)
        | sd_v.isna()
        | sd_v.lt(QUEBRADA_SWE_SD_MIN_CM)
        | (sd_v.ge(10) & (ratio.lt(QUEBRADA_SWE_RATIO_MIN) | ratio.gt(QUEBRADA_SWE_RATIO_MAX)))
        | (
            sd_v.ge(QUEBRADA_SWE_SHALLOW_SD_MIN_CM)
            & sd_v.lt(QUEBRADA_SWE_SHALLOW_SD_MAX_CM)
            & swe_v.gt(QUEBRADA_SWE_SHALLOW_MAX_MM)
        )
    )

    out.loc[out["date"].isin(merged.loc[bad, "date"]), "media"] = pd.NA
    return out


def _infill_short_swe_gaps(
    values: np.ndarray,
    *,
    max_gap: int,
    min_context_mm: float,
) -> np.ndarray:
    """Linear infill for brief SWE=0 runs between similar non-zero neighbors."""
    v = values.astype(float, copy=True)
    n = len(v)
    i = 0
    while i < n:
        if not (v[i] == 0 or np.isnan(v[i])):
            i += 1
            continue
        j = i
        while j < n and (v[j] == 0 or np.isnan(v[j])):
            j += 1
        run_len = j - i
        left = v[i - 1] if i > 0 else np.nan
        right = v[j] if j < n else np.nan
        if (
            run_len <= max_gap
            and np.isfinite(left)
            and np.isfinite(right)
            and left >= min_context_mm
            and right >= min_context_mm
        ):
            for k in range(i, j):
                t = (k - i + 1) / (run_len + 1)
                v[k] = left + t * (right - left)
        i = j if j > i else i + 1
    return v


def align_swe_with_sd(
    swe: pd.DataFrame,
    sd: pd.DataFrame,
    *,
    sd_col: str = "SD_mean_clean",
    swe_cols: tuple[str, ...] = ("min", "media", "max"),
    min_sd_cm: float = SWE_ZERO_UNLESS_SD_MIN_CM,
    gate_days: int = SWE_SD_GATE_ROLLING_DAYS,
    infill_max_gap: int = SWE_INFILL_MAX_GAP_DAYS,
    infill_min_context_mm: float = SWE_INFILL_MIN_CONTEXT_MM,
) -> pd.DataFrame:
    """
    Zero SWE when a rolling-max snow depth (gate) indicates no pack (< min_sd_cm).

    Uses a centered rolling maximum of SD so single-day depth dropouts do not
    create vertical SWE spikes to zero during accumulation. Brief zero gaps
    between active SWE values are linearly infilled for continuous time series.
    """
    out = swe.sort_values("date").copy()
    sd_sorted = sd.sort_values("date")
    merged = out.merge(sd_sorted[["date", sd_col]], on="date", how="left")
    merged["water_year"] = np.where(
        merged["date"].dt.month >= 4,
        merged["date"].dt.year,
        merged["date"].dt.year - 1,
    )
    present = [c for c in swe_cols if c in out.columns]

    for _, idx in merged.groupby("water_year").groups.items():
        block = merged.loc[idx]
        sd_gate = block[sd_col].rolling(gate_days, center=True, min_periods=1).max()
        no_snow = sd_gate.isna() | sd_gate.lt(min_sd_cm)
        if no_snow.any():
            zero_idx = block.index[no_snow.to_numpy()]
            for col in present:
                out.loc[zero_idx, col] = 0.0

        for col in present:
            segment = out.loc[block.index, col].to_numpy()
            filled = _infill_short_swe_gaps(
                segment,
                max_gap=infill_max_gap,
                min_context_mm=infill_min_context_mm,
            )
            out.loc[block.index, col] = filled
    return out


def zero_swe_when_sd_zero(
    swe: pd.DataFrame,
    sd: pd.DataFrame,
    **kwargs,
) -> pd.DataFrame:
    """Backward-compatible alias; uses paper default min_sd_cm from config."""
    return align_swe_with_sd(swe, sd, **kwargs)
