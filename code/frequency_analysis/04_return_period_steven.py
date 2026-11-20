"""
Return-period analysis for the UPLA article (Section 2).

Figures written to Figures/:
  return_period/{station}_return_periods.png   — automatic SD (+ SWE if available)
  return_period/snowcourse_return_periods.png — Portillo snowcourse (peak + Jul-31 metrics)
  return_period/all_stations_return_periods.png — (a) Δds/ΔSWE, (b) snowfall, (c) snowcourse (Methods order)
  return_period/all_stations_snowfall_return_periods.png — standalone snowfall panel
  snowcourse/{station}_jul31_{sd,swe}.png      — per-route Jul-31 series
  snowcourse/all_stations_snowcourse_jul31.png — all routes (SD | SWE)
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import gamma, norm, skew

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from enso_oni_utils import snowcourse_closest_jul31  # noqa: E402
from paths import (  # noqa: E402
    FIG_RETURN_PERIOD,
    FIG_SNOWCOURSE,
    OUT_RETURN_PERIOD,
    OUT_STATIONS,
    PROCESSED_DIR,
    SNOWCOURSE_FILES,
)
from stations_config import (  # noqa: E402
    DS_INCREASE_WINDOWS,
    SF_ROLLING_WINDOWS,
    STATION_COLORS,
    STATION_ORDER,
    STATION_ORDER_BY_LATITUDE,
    STATIONS,
    SNOWCOURSE_MAX_DAYS,
    SWE_INCREASE_WINDOWS,
    station_label,
)
from plot_style import (  # noqa: E402
    BAR_ACCENT,
    DS_LABEL,
    DS_YLABEL_CM,
    apply_article_style,
    bar_series,
    clean_axes,
    ds_jul31_xtick,
    ds_peak_xtick,
    ds_window_xtick,
    scatter_2026,
    scatter_points,
)

TABLES_DIR = str(OUT_RETURN_PERIOD / "tables")
FIG_RP = str(FIG_RETURN_PERIOD)
FIG_SC = str(FIG_SNOWCOURSE)
SNOWCOURSE_OUT_DIR = str(OUT_RETURN_PERIOD / "snowcourse")
STATIONS_DATA_DIR = str(OUT_STATIONS)

SEASON_START_MONTH = 4
SEASON_END_MONTH = 12
TARGET_YEAR = 2026

RP_METRICS = [
    ("ds_3day_increase", ds_window_xtick(3)),
    ("ds_5day_increase", ds_window_xtick(5)),
    ("ds_7day_increase", ds_window_xtick(7)),
    ("swe_3day_increase", "SWE 3-d"),
    ("swe_5day_increase", "SWE 5-d"),
    ("swe_7day_increase", "SWE 7-d"),
    ("swe_15day_increase", "SWE 15-d"),
]

# Derived snowfall depth: sum of daily max(0, Δds) over rolling windows.
SNOWFALL_RP_METRICS = [
    ("sf_1day_sum", "SF 1-d"),
    ("sf_3day_sum", "SF 3-d"),
    ("sf_5day_sum", "SF 5-d"),
    ("sf_7day_sum", "SF 7-d"),
]
SF_RP_X = [0.0, 1.0, 2.0, 3.0]
SF_RP_XLIM = (-0.45, 3.45)

# Snowcourse panel (b): late-Jul window + seasonal peak (both SD and SWE).
SNOWCOURSE_RP_METRICS = [
    ("late_july_ds", ds_jul31_xtick()),
    ("peak_ds", ds_peak_xtick()),
    ("late_july_swe", "Jul-31 SWE"),
    ("peak_swe", "Peak SWE"),
]

# Shared horizontal layout: (a) at 0–6; (b) pairs centered under SD (0–2) and SWE (3–6) blocks.
RP_X_AUTO = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
RP_X_SNOWCOURSE = [0.6, 1.85, 3.65, 5.05]
SD_SWE_SEPARATOR_X = 2.5
RP_XLIM = (-0.45, 6.45)

PIII_KEY = "T_PIII"


@dataclass
class FitResult:
    values: np.ndarray
    years: np.ndarray
    mean: float
    std: float
    skewness: float
    n: int

    @property
    def latest_value(self) -> float:
        return float(self.values[-1])

    @property
    def latest_year(self) -> int:
        return int(self.years[-1])


def ensure_output_dir() -> None:
    for path in (TABLES_DIR, FIG_RP, FIG_SC, SNOWCOURSE_OUT_DIR, STATIONS_DATA_DIR):
        os.makedirs(path, exist_ok=True)


def load_daily_ds(station_id: str) -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_DIR / f"SD_{station_id}.csv", parse_dates=["date"])
    return (
        df[["date", "SD_mean_clean"]]
        .rename(columns={"SD_mean_clean": "ds_cm"})
        .sort_values("date")
        .reset_index(drop=True)
    )


def load_daily_swe(station_id: str) -> pd.DataFrame | None:
    path = PROCESSED_DIR / f"SWE_{station_id}.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, parse_dates=["date"])
    return (
        df[["date", "media"]]
        .rename(columns={"media": "swe_mm"})
        .sort_values("date")
        .reset_index(drop=True)
    )


def load_snowcourse(path: str) -> pd.DataFrame:
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


def snowcourse_jul31_with_2026(sc: pd.DataFrame) -> pd.DataFrame:
    """Strict ±21 d Jul-31 series; append 2026 closest survey if missing (for 2026 RP)."""
    jul31 = snowcourse_jul31_series(sc)
    if TARGET_YEAR in jul31["year"].values:
        return jul31
    extra = snowcourse_closest_jul31(sc, TARGET_YEAR, max_days=999)
    if extra is None:
        return jul31
    row = {
        "year": TARGET_YEAR,
        "ds_cm": float(extra["ds_cm"]),
        "swe_mm": float(extra["swe_mm"]),
        "event_date": extra["event_date"],
        "days_from_jul31": int(extra["days_from_jul31"]),
    }
    return pd.concat([jul31, pd.DataFrame([row])], ignore_index=True).sort_values("year")


def snowcourse_jul31_series(snowcourse: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year, group in snowcourse.groupby("year"):
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
                "event_date": valid.loc[idx, "date"],
                "days_from_jul31": int(valid.loc[idx, "days_from_jul31"]),
            }
        )
    return pd.DataFrame(rows)


def snowcourse_annual_peaks(sc: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year, group in sc.groupby("year"):
        valid = group.dropna(subset=["ds_cm", "swe_mm"], how="any")
        if valid.empty:
            continue
        rows.append(
            {
                "year": int(year),
                "peak_ds": float(valid["ds_cm"].max()),
                "peak_swe": float(valid["swe_mm"].max()),
            }
        )
    return pd.DataFrame(rows)


def season_mask(dates: pd.Series) -> pd.Series:
    return (dates.dt.month >= SEASON_START_MONTH) & (dates.dt.month <= SEASON_END_MONTH)


def daily_snowfall_from_ds(ds: pd.DataFrame) -> pd.DataFrame:
    """Positive day-to-day snow depth increments (cm), NaN if either day missing."""
    data = ds.sort_values("date").copy().set_index("date")
    full_index = pd.date_range(data.index.min(), data.index.max(), freq="D")
    data = data.reindex(full_index)
    ds_vals = data["ds_cm"]
    sf = ds_vals.diff()
    valid = ds_vals.notna() & ds_vals.shift(1).notna()
    sf = sf.where(valid)
    sf = sf.clip(lower=0)
    return pd.DataFrame({"date": sf.index, "sf_cm": sf.to_numpy()})


def _sum_sf_over_window(group: pd.DataFrame, end_idx: int, window: int) -> float:
    """Sum daily SF over `window` days ending at end_idx (inclusive)."""
    start = end_idx - window + 1
    if start < 0:
        return float("nan")
    chunk = group.iloc[start : end_idx + 1]["sf_cm"]
    if chunk.isna().any():
        return float("nan")
    return float(chunk.sum())


def annual_snowfall_metrics(ds: pd.DataFrame, sf: pd.DataFrame) -> list[pd.DataFrame]:
    """
    For each year and window n, locate the n-day interval with the largest net ds
    increase (same end date as the ds_n-day increase metric), then set the annual
    snowfall value to the **sum** of daily SF over that interval (not net ds change).
    """
    ds_frame = ds.sort_values("date").copy()
    ds_frame = ds_frame.loc[season_mask(ds_frame["date"])].dropna(subset=["ds_cm"])
    sf_frame = sf.sort_values("date").copy()
    sf_frame = sf_frame.loc[season_mask(sf_frame["date"])]

    frames: list[pd.DataFrame] = []

    for window in SF_ROLLING_WINDOWS:
        metric_key = f"sf_{window}day_sum"
        ds_annual = annual_max_increase(
            ds, "ds_cm", window, f"ds_{window}day_increase_ref"
        )
        rows = []
        for _, ev in ds_annual.iterrows():
            year = int(ev["year"])
            event_date = pd.Timestamp(ev["event_date"])
            sf_year = sf_frame.loc[sf_frame["date"].dt.year == year].sort_values("date")
            if sf_year.empty:
                continue
            sf_year = sf_year.reset_index(drop=True)
            pos = sf_year.index[sf_year["date"] == event_date]
            if pos.empty:
                continue
            end_idx = int(pos[0])
            total = _sum_sf_over_window(sf_year, end_idx, window)
            if not np.isfinite(total):
                continue
            rows.append(
                {
                    "year": year,
                    "value": total,
                    "event_date": event_date,
                    "metric": metric_key,
                }
            )
        frames.append(pd.DataFrame(rows))

    return frames


def annual_max_increase(
    series: pd.DataFrame, value_col: str, window_days: int, metric_name: str
) -> pd.DataFrame:
    data = series.sort_values("date").copy().set_index("date")
    full_index = pd.date_range(data.index.min(), data.index.max(), freq="D")
    data = data.reindex(full_index)
    values = data[value_col]
    increase = values - values.shift(window_days)
    increase = increase.where(values.notna() & values.shift(window_days).notna())
    frame = pd.DataFrame({"value": increase, "date": increase.index})
    frame = frame.loc[season_mask(frame["date"])].dropna(subset=["value"])
    rows = []
    for year, group in frame.groupby(frame["date"].dt.year):
        idx = group["value"].idxmax()
        rows.append(
            {
                "year": int(year),
                "value": float(group.loc[idx, "value"]),
                "event_date": group.loc[idx, "date"],
                "metric": metric_name,
            }
        )
    return pd.DataFrame(rows)


def fit_sample(annual: pd.DataFrame) -> FitResult:
    annual = annual.sort_values("year")
    values = annual["value"].astype(float).to_numpy()
    years = annual["year"].astype(int).to_numpy()
    return FitResult(
        values=values,
        years=years,
        mean=float(np.mean(values)),
        std=float(np.std(values, ddof=1)),
        skewness=float(skew(values, bias=False)),
        n=len(values),
    )


def pearson3_cdf(x: float, mean: float, std: float, cs: float) -> float:
    if std <= 0:
        return float("nan")
    if abs(cs) < 1e-8:
        return float(norm.cdf((x - mean) / std))
    alpha = 4.0 / cs**2
    beta = np.sign(cs) * np.sqrt(std**2 / alpha)
    tau = mean - alpha * beta
    if cs > 0:
        return float(gamma.cdf(max(x - tau, 0.0), a=alpha, scale=beta))
    return float(1.0 - gamma.cdf(max(tau - x, 0.0), a=alpha, scale=-beta))


def return_period_from_cdf(prob: float) -> float:
    if not np.isfinite(prob) or prob >= 1.0:
        return float("inf")
    if prob <= 0.0:
        return 1.0
    return 1.0 / (1.0 - prob)


def frequency_table(fit: FitResult, label: str) -> dict:
    x = fit.latest_value
    p_n = float(norm.cdf(x, loc=fit.mean, scale=fit.std)) if fit.std > 0 else float("nan")
    if np.all(fit.values > 0) and x > 0:
        log_values = np.log10(fit.values)
        log_mean = float(np.mean(log_values))
        log_std = float(np.std(log_values, ddof=1))
        log_skew = float(skew(log_values, bias=False))
        p_ln = float(norm.cdf(np.log10(x), loc=log_mean, scale=log_std))
        p_lpiii = pearson3_cdf(np.log10(x), log_mean, log_std, log_skew)
    else:
        log_mean = log_std = log_skew = p_ln = p_lpiii = float("nan")
    p_piii = pearson3_cdf(x, fit.mean, fit.std, fit.skewness)
    return {
        "metric": label,
        "latest_year": fit.latest_year,
        "latest_value": x,
        "n_years": fit.n,
        "T_normal": return_period_from_cdf(p_n),
        "T_lognormal": return_period_from_cdf(p_ln),
        "T_PIII": return_period_from_cdf(p_piii),
        "T_LPIII": return_period_from_cdf(p_lpiii),
    }


def cap_return_period(t: float, cap: float = 500.0) -> float:
    if not np.isfinite(t):
        return cap
    return min(float(t), cap)


def format_rp(t: float) -> str:
    if not np.isfinite(t):
        return "—"
    if t >= 100:
        return f"{t:.0f}"
    if t >= 10:
        return f"{t:.1f}"
    return f"{t:.2f}"


def format_rp_integer(t: float) -> str:
    if not np.isfinite(t):
        return "—"
    return str(int(round(t)))


def plot_piii_bars(categories: list[str], values: list[float], path: str) -> None:
    """Single-series Pearson III return periods."""
    apply_article_style()
    fig, ax = plt.subplots(figsize=(max(5.8, len(categories) * 1.05), 3.8))
    x = np.arange(len(categories))
    heights = [cap_return_period(v) for v in values]
    bar_series(ax, x, heights, BAR_ACCENT, width=0.52)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=32, ha="right")
    ax.set_yscale("log")
    ax.set_ylabel("Return period (yr)")
    ax.set_ylim(0.8, 600)
    clean_axes(ax)
    fig.subplots_adjust(bottom=0.24, left=0.11, right=0.97)
    fig.savefig(path)
    plt.close(fig)


def _draw_sd_swe_separator(ax) -> None:
    ax.axvline(
        SD_SWE_SEPARATOR_X,
        color="#b8b8b8",
        linewidth=0.85,
        linestyle=(0, (2, 3)),
        zorder=0,
    )


def _annotate_rp_values(
    ax,
    xs: list[float],
    heights: list[float],
    raw_ts: list[float],
    *,
    fontsize: float,
) -> None:
    """Return-period text above bars (readable on log scale and all station colors)."""
    for x, h, t in zip(xs, heights, raw_ts):
        if not np.isfinite(h) or h <= 0 or not np.isfinite(t):
            continue
        y = h * 1.14
        if y > 520:
            y = 520
        ax.text(
            x,
            y,
            format_rp_integer(t),
            ha="center",
            va="bottom",
            fontsize=fontsize,
            color="#1a1a1a",
            fontweight="medium",
            zorder=6,
            clip_on=True,
        )


def _plot_grouped_return_period_bars(
    ax,
    metric_defs: list[tuple[str, str]],
    table: pd.DataFrame,
    station_ids: list[str],
    *,
    bar_width: float,
    x_positions: list[float] | None = None,
    draw_sd_swe_separator: bool = False,
    show_rp_labels: bool = False,
    rp_label_fontsize: float = 6.0,
    xlim: tuple[float, float] | None = None,
) -> None:
    if x_positions is None:
        x_positions = list(np.arange(len(metric_defs)))
    if len(x_positions) != len(metric_defs):
        raise ValueError("x_positions must match metric_defs length")

    n = len(station_ids)
    offsets = np.linspace(-(n - 1) / 2, (n - 1) / 2, n) * bar_width

    label_xs: list[float] = []
    label_hs: list[float] = []
    label_ts: list[float] = []

    for i, sid in enumerate(station_ids):
        heights: list[float] = []
        raw_ts: list[float] = []
        for metric_key, _ in metric_defs:
            row = table.loc[
                (table["station_id"] == sid) & (table["metric"] == metric_key)
            ]
            if row.empty:
                heights.append(np.nan)
                raw_ts.append(np.nan)
            else:
                raw = float(row.iloc[0][PIII_KEY])
                raw_ts.append(raw)
                heights.append(cap_return_period(raw))

        valid = [
            (x_positions[j] + offsets[i], h, raw_ts[j])
            for j, h in enumerate(heights)
            if np.isfinite(h)
        ]
        if not valid:
            continue
        vx, vh, vt = zip(*valid)
        bar_series(ax, list(vx), list(vh), STATION_COLORS[sid], width=bar_width, alpha=0.9)
        if show_rp_labels:
            label_xs.extend(vx)
            label_hs.extend(vh)
            label_ts.extend(vt)

    if show_rp_labels and label_xs:
        _annotate_rp_values(
            ax, label_xs, label_hs, label_ts, fontsize=rp_label_fontsize
        )

    ax.set_xticks(x_positions)
    ax.set_xticklabels([m[1] for m in metric_defs], rotation=32, ha="right")
    ax.tick_params(axis="x", labelbottom=True, pad=2)
    if draw_sd_swe_separator:
        _draw_sd_swe_separator(ax)
    ax.set_xlim(xlim if xlim is not None else RP_XLIM)
    ax.set_yscale("log")
    ax.set_ylim(0.8, 600)
    clean_axes(ax)


def plot_snowfall_return_periods(summary: pd.DataFrame, path: str) -> None:
    """All-station return periods for derived snowfall depth (positive daily Δds)."""
    apply_article_style()
    summary = summary.copy()
    summary["station_id"] = summary["station_id"].astype(str).str.zfill(8)

    fig, ax = plt.subplots(figsize=(9.2, 4.0))
    _plot_grouped_return_period_bars(
        ax,
        SNOWFALL_RP_METRICS,
        summary,
        STATION_ORDER,
        bar_width=0.14,
        x_positions=SF_RP_X,
        draw_sd_swe_separator=False,
        show_rp_labels=True,
        rp_label_fontsize=6.5,
    )
    ax.set_xlim(SF_RP_XLIM)
    ax.set_ylabel("Return period (yr)")
    ax.set_title(
        "Snowfall depth (sum of daily increments over storm intervals, Apr–Dec)",
        fontsize=10,
        pad=8,
    )
    ax.legend(
        handles=[
            plt.matplotlib.patches.Patch(
                facecolor=STATION_COLORS[s],
                edgecolor="white",
                linewidth=0.8,
                label=STATIONS[s]["short"],
            )
            for s in STATION_ORDER
        ],
        loc="upper right",
        frameon=True,
        framealpha=0.96,
        edgecolor="#dddddd",
        ncol=2,
        fontsize=9.5,
        handlelength=1.45,
        handletextpad=0.55,
        borderpad=0.55,
    )
    fig.subplots_adjust(left=0.1, right=0.98, top=0.88, bottom=0.22)
    fig.savefig(path)
    plt.close(fig)


def plot_unified_return_periods(
    summary: pd.DataFrame,
    snowfall_summary: pd.DataFrame | None,
    snowcourse_summary: pd.DataFrame | None,
    path: str,
) -> None:
    """Three-row figure: (a) Δds/ΔSWE windows, (b) snowfall sums, (c) snowcourse."""
    apply_article_style()
    summary = summary.copy()
    summary["station_id"] = summary["station_id"].astype(str).str.zfill(8)
    if snowfall_summary is not None and not snowfall_summary.empty:
        snowfall_summary = snowfall_summary.copy()
        snowfall_summary["station_id"] = snowfall_summary["station_id"].astype(str).str.zfill(8)
    if snowcourse_summary is not None and not snowcourse_summary.empty:
        snowcourse_summary = snowcourse_summary.copy()
        snowcourse_summary["station_id"] = snowcourse_summary["station_id"].astype(str).str.zfill(8)

    snowcourse_ids = [s for s in STATION_ORDER if STATIONS[s].get("has_snowcourse")]

    fig, (ax_a, ax_b, ax_c) = plt.subplots(
        3,
        1,
        figsize=(10.0, 9.6),
        sharey=True,
        gridspec_kw={"height_ratios": [1, 1, 1], "hspace": 0.22},
    )

    _plot_grouped_return_period_bars(
        ax_a,
        RP_METRICS,
        summary,
        STATION_ORDER,
        bar_width=0.13,
        x_positions=RP_X_AUTO,
        draw_sd_swe_separator=True,
        show_rp_labels=True,
        rp_label_fontsize=6.0,
        xlim=RP_XLIM,
    )
    ax_a.set_ylabel("Return period (yr)")
    ax_a.text(
        -0.09,
        1.02,
        "(a)",
        transform=ax_a.transAxes,
        ha="left",
        va="bottom",
        fontsize=11,
        fontweight="bold",
    )
    ax_a.legend(
        handles=[
            plt.matplotlib.patches.Patch(
                facecolor=STATION_COLORS[s],
                edgecolor="white",
                linewidth=0.8,
                label=STATIONS[s]["short"],
            )
            for s in STATION_ORDER
        ],
        loc="upper right",
        frameon=True,
        framealpha=0.96,
        edgecolor="#dddddd",
        ncol=2,
        fontsize=10.5,
        handlelength=1.45,
        handletextpad=0.55,
        borderpad=0.55,
    )

    if snowfall_summary is not None and not snowfall_summary.empty:
        _plot_grouped_return_period_bars(
            ax_b,
            SNOWFALL_RP_METRICS,
            snowfall_summary,
            STATION_ORDER,
            bar_width=0.14,
            x_positions=SF_RP_X,
            draw_sd_swe_separator=False,
            show_rp_labels=True,
            rp_label_fontsize=6.5,
            xlim=SF_RP_XLIM,
        )
    ax_b.text(
        -0.09,
        1.02,
        "(b)",
        transform=ax_b.transAxes,
        ha="left",
        va="bottom",
        fontsize=11,
        fontweight="bold",
    )

    for ax in (ax_a, ax_b, ax_c):
        ax.tick_params(axis="x", labelbottom=True, pad=2)

    if snowcourse_summary is not None and not snowcourse_summary.empty:
        _plot_grouped_return_period_bars(
            ax_c,
            SNOWCOURSE_RP_METRICS,
            snowcourse_summary,
            snowcourse_ids,
            bar_width=0.24,
            x_positions=RP_X_SNOWCOURSE,
            draw_sd_swe_separator=True,
            show_rp_labels=True,
            rp_label_fontsize=7.0,
            xlim=RP_XLIM,
        )
    ax_c.text(
        -0.09,
        1.02,
        "(c)",
        transform=ax_c.transAxes,
        ha="left",
        va="bottom",
        fontsize=11,
        fontweight="bold",
    )

    fig.subplots_adjust(left=0.1, right=0.98, top=0.96, bottom=0.12)
    fig.savefig(path)
    plt.close(fig)


def metric_label(metric: str) -> str:
    labels = {
        "ds_3day_increase": ds_window_xtick(3, short=False),
        "ds_5day_increase": ds_window_xtick(5, short=False),
        "ds_7day_increase": ds_window_xtick(7, short=False),
        "swe_3day_increase": "SWE 3-day",
        "swe_5day_increase": "SWE 5-day",
        "swe_7day_increase": "SWE 7-day",
        "swe_15day_increase": "SWE 15-day",
        "peak_ds": ds_peak_xtick(),
        "late_july_ds": ds_jul31_xtick(),
        "peak_swe": "peak SWE",
        "late_july_swe": "late July SWE",
    }
    return labels.get(metric, metric)


def analyze_metrics(
    annual_frames: list[pd.DataFrame],
    station_id: str | None,
    tables_prefix: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    annual_all = pd.concat(annual_frames, ignore_index=True)
    if station_id is not None:
        annual_all.insert(0, "station_id", station_id)
        annual_all.insert(1, "station_name", STATIONS[station_id]["name"])

    summary_rows = []
    for metric, group in annual_all.groupby("metric"):
        group = group.dropna(subset=["value"]).sort_values("year")
        if len(group) < 3:
            continue
        fit = fit_sample(group)
        row = frequency_table(fit, metric)
        if station_id is not None:
            row = {"station_id": station_id, "station_name": STATIONS[station_id]["name"], **row}
        summary_rows.append(row)
        group.to_csv(
            os.path.join(TABLES_DIR, f"{tables_prefix}detail_{metric}.csv"),
            index=False,
            date_format="%Y-%m-%d",
        )

    return annual_all, pd.DataFrame(summary_rows)


def process_station_snowfall(station_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    ds = load_daily_ds(station_id)
    sf = daily_snowfall_from_ds(ds)
    frames = annual_snowfall_metrics(ds, sf)
    return analyze_metrics(frames, station_id, f"{station_id}_snowfall_")


def process_station(station_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    ds = load_daily_ds(station_id)
    frames = []
    for window in DS_INCREASE_WINDOWS:
        frames.append(annual_max_increase(ds, "ds_cm", window, f"ds_{window}day_increase"))

    swe = load_daily_swe(station_id)
    if swe is not None:
        for window in SWE_INCREASE_WINDOWS:
            frames.append(
                annual_max_increase(swe, "swe_mm", window, f"swe_{window}day_increase")
            )

    annual, summary = analyze_metrics(frames, station_id, f"{station_id}_")
    annual.to_csv(
        os.path.join(STATIONS_DATA_DIR, f"{station_id}_annual_events.csv"),
        index=False,
        date_format="%Y-%m-%d",
    )
    summary.to_csv(
        os.path.join(STATIONS_DATA_DIR, f"{station_id}_frequency_summary.csv"),
        index=False,
    )
    return annual, summary


def plot_station_return_periods(station_id: str, summary: pd.DataFrame) -> str:
    categories, values = [], []
    for metric_key, label in RP_METRICS:
        part = summary.loc[summary["metric"] == metric_key]
        if part.empty:
            continue
        categories.append(label)
        values.append(float(part.iloc[0][PIII_KEY]))

    if not categories:
        return ""
    path = os.path.join(FIG_RP, f"{station_id}_return_periods.png")
    plot_piii_bars(categories, values, path)
    return path


def fit_snowcourse_metric(years_values: pd.DataFrame) -> dict | None:
    sample = years_values.dropna(subset=["val"]).sort_values("year")
    if len(sample) < 3:
        return None
    annual = sample.rename(columns={"val": "value"})[["year", "value"]]
    annual["metric"] = "m"
    fit = fit_sample(annual)
    return frequency_table(fit, "m")


def build_snowcourse_return_period_rows(
    sc: pd.DataFrame,
    station_id: str,
    *,
    include_peaks: bool = False,
    jul31_for_rp: pd.DataFrame | None = None,
) -> list[dict]:
    jul31 = jul31_for_rp if jul31_for_rp is not None else snowcourse_jul31_with_2026(sc)
    datasets: dict[str, pd.DataFrame] = {
        "late_july_ds": jul31.rename(columns={"ds_cm": "val"})[["year", "val"]],
        "late_july_swe": jul31.rename(columns={"swe_mm": "val"})[["year", "val"]],
    }
    if include_peaks:
        peaks = snowcourse_annual_peaks(sc)
        datasets["peak_ds"] = peaks.rename(columns={"peak_ds": "val"})[["year", "val"]]
        datasets["peak_swe"] = peaks.rename(columns={"peak_swe": "val"})[["year", "val"]]

    rows: list[dict] = []
    for key, frame in datasets.items():
        row = fit_snowcourse_metric(frame)
        if row is None:
            continue
        row["metric"] = key
        row["station_id"] = station_id
        row["station_name"] = STATIONS[station_id]["name"]
        rows.append(row)
    return rows


def build_portillo_snowcourse_return_periods(sc: pd.DataFrame) -> tuple[list[str], list[dict]]:
    rows = build_snowcourse_return_period_rows(sc, "05401007", include_peaks=True)
    categories = [metric_label(r["metric"]) for r in rows]
    return categories, rows


def build_all_snowcourse_rp_summary() -> pd.DataFrame:
    allowed = {m[0] for m in SNOWCOURSE_RP_METRICS}
    all_rows: list[dict] = []
    for station_id, path in SNOWCOURSE_FILES.items():
        if not path.exists() or not STATIONS[station_id].get("has_snowcourse"):
            continue
        sc = load_snowcourse(str(path))
        jul31_rp = snowcourse_jul31_with_2026(sc)
        for row in build_snowcourse_return_period_rows(
            sc, station_id, include_peaks=True, jul31_for_rp=jul31_rp
        ):
            if row["metric"] in allowed:
                all_rows.append(row)
    return pd.DataFrame(all_rows)


def _overlay_snowcourse_2026(
    ax,
    jul31: pd.DataFrame,
    sc: pd.DataFrame,
    value_col: str,
) -> None:
    extra_2026 = jul31.loc[jul31["year"] == TARGET_YEAR]
    if extra_2026.empty:
        extra = snowcourse_closest_jul31(sc, TARGET_YEAR, max_days=999)
        if extra:
            val = extra["ds_cm"] if value_col == "ds_cm" else extra["swe_mm"]
            scatter_2026(ax, TARGET_YEAR, val)
    else:
        scatter_2026(ax, TARGET_YEAR, float(extra_2026.iloc[0][value_col]))


def _draw_snowcourse_jul31_panel(
    ax,
    jul31: pd.DataFrame,
    sc: pd.DataFrame,
    station_id: str,
    value_col: str,
    ylabel: str,
    *,
    show_xlabel: bool,
    y_limits: tuple[float, float] | None = None,
) -> None:
    color = STATION_COLORS[station_id]
    years = jul31["year"].to_numpy(dtype=float)
    values = jul31[value_col].to_numpy(dtype=float)
    mask = np.isfinite(years) & np.isfinite(values)
    scatter_points(ax, years[mask], values[mask], colors=color, size=30)
    _overlay_snowcourse_2026(ax, jul31, sc, value_col)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Year" if show_xlabel else "")
    if y_limits is not None:
        ax.set_ylim(y_limits)
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True, nbins=8))
    clean_axes(ax)


def plot_snowcourse_year_series(
    jul31: pd.DataFrame,
    station_id: str,
    value_col: str,
    ylabel: str,
    suffix: str,
) -> str:
    """Year vs Jul-31 snowcourse value (no trend line)."""
    apply_article_style()
    sc = load_snowcourse(str(SNOWCOURSE_FILES[station_id]))
    fig, ax = plt.subplots(figsize=(6.0, 3.5))
    _draw_snowcourse_jul31_panel(
        ax, jul31, sc, station_id, value_col, ylabel, show_xlabel=True
    )
    fig.subplots_adjust(left=0.12, right=0.97, bottom=0.14)
    path = os.path.join(FIG_SC, f"{station_id}_jul31_{suffix}.png")
    fig.savefig(path)
    plt.close(fig)
    return path


def plot_all_stations_snowcourse() -> str:
    """Four-row figure: Jul-31 snowcourse SD | SWE (north → south), same style as singles."""
    from plot_style import COLOR_2026, panel_label
    from snow_figure_limits import global_column_ylimits

    apply_article_style()
    station_ids = [
        sid for sid in STATION_ORDER_BY_LATITUDE if STATIONS[sid].get("has_snowcourse")
    ]
    n = len(station_ids)
    fig, axes = plt.subplots(
        n,
        2,
        figsize=(12.0, 2.08 * n),
        squeeze=False,
        sharex=True,
        sharey="col",
        gridspec_kw={"wspace": 0.24, "hspace": 0.28},
    )

    x_min, x_max = np.inf, -np.inf
    for station_id in station_ids:
        sc = load_snowcourse(str(SNOWCOURSE_FILES[station_id]))
        jul31 = snowcourse_jul31_series(sc)
        if not jul31.empty:
            x_min = min(x_min, float(jul31["year"].min()))
            x_max = max(x_max, float(jul31["year"].max()))
    x_min = max(1950, x_min - 1 if np.isfinite(x_min) else 1950)
    x_max = min(2027, x_max + 1 if np.isfinite(x_max) else 2026)

    column_ylim = global_column_ylimits(list(STATION_ORDER))
    panel_letters = "abcdefgh"
    for row, station_id in enumerate(station_ids):
        sc = load_snowcourse(str(SNOWCOURSE_FILES[station_id]))
        jul31 = snowcourse_jul31_series(sc)
        name = STATIONS[station_id]["name"]
        for col_idx, (value_col, ylabel) in enumerate(
            [("ds_cm", "cm"), ("swe_mm", "mm")]
        ):
            ax = axes[row, col_idx]
            y_key = "ds" if value_col == "ds_cm" else "swe"
            _draw_snowcourse_jul31_panel(
                ax,
                jul31,
                sc,
                station_id,
                value_col,
                ylabel,
                show_xlabel=(row == n - 1),
                y_limits=column_ylim[y_key],
            )
            ax.set_xlim(x_min, x_max)
            ax.set_ylabel(ylabel, labelpad=2)
            panel_label(ax, panel_letters[row * 2 + col_idx])
            ax.text(
                0.02,
                0.97,
                name,
                transform=ax.transAxes,
                ha="left",
                va="top",
                fontsize=8,
                color="#333333",
            )

    axes[0, 0].set_title(DS_LABEL, fontsize=11, pad=8)
    axes[0, 1].set_title("SWE", fontsize=11, pad=8)
    for ax in axes.flat:
        ax.tick_params(axis="x", pad=2, labelbottom=True)

    fig.text(
        0.98,
        0.02,
        "◆ 2026 survey",
        ha="right",
        va="bottom",
        fontsize=8.5,
        color=COLOR_2026,
        fontweight="bold",
        transform=fig.transFigure,
    )
    fig.subplots_adjust(left=0.07, right=0.98, top=0.96, bottom=0.07)
    path = os.path.join(FIG_SC, "all_stations_snowcourse_jul31.png")
    os.makedirs(FIG_SC, exist_ok=True)
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path


def process_snowcourses() -> None:
    portillo_sc = None
    for station_id, path in SNOWCOURSE_FILES.items():
        if not path.exists():
            continue
        sc = load_snowcourse(str(path))
        jul31 = snowcourse_jul31_series(sc)
        meta = STATIONS[station_id]
        out = jul31.copy()
        out.insert(0, "station_name", meta["name"])
        out.insert(0, "station_id", station_id)
        out.to_csv(
            os.path.join(SNOWCOURSE_OUT_DIR, f"{station_id}_snowcourse_jul31.csv"),
            index=False,
            date_format="%Y-%m-%d",
        )
        p_sd = plot_snowcourse_year_series(jul31, station_id, "ds_cm", DS_YLABEL_CM, "sd")
        p_swe = plot_snowcourse_year_series(jul31, station_id, "swe_mm", "SWE (mm)", "swe")
        print(f"  {station_id} → {p_sd}, {p_swe}")
        if station_id == "05401007":
            portillo_sc = sc

    if portillo_sc is not None:
        jul31_sc = snowcourse_jul31_series(portillo_sc)
        jul31_sc.to_csv(
            os.path.join(SNOWCOURSE_OUT_DIR, "portillo_snowcourse_jul31.csv"),
            index=False,
            date_format="%Y-%m-%d",
        )
        row_2026 = snowcourse_closest_jul31(portillo_sc, TARGET_YEAR, max_days=SNOWCOURSE_MAX_DAYS)
        if row_2026 is None:
            row_2026 = snowcourse_closest_jul31(portillo_sc, TARGET_YEAR, max_days=999)
        pd.DataFrame([{"source": "snowcourse", **row_2026}]).to_csv(
            os.path.join(SNOWCOURSE_OUT_DIR, "portillo_snowcourse_2026.csv"),
            index=False,
            date_format="%Y-%m-%d",
        )

        categories, rows = build_portillo_snowcourse_return_periods(portillo_sc)
        if rows:
            rp_path = os.path.join(FIG_RP, "snowcourse_return_periods.png")
            plot_piii_bars(
                categories,
                [float(r[PIII_KEY]) for r in rows],
                rp_path,
            )
            print(f"  snowcourse RP → {rp_path}")
            pd.DataFrame(rows).to_csv(
                os.path.join(TABLES_DIR, "snowcourse_return_periods.csv"),
                index=False,
            )

    all_sc_path = plot_all_stations_snowcourse()
    print(f"  all-stations snowcourse → {all_sc_path}")


def main() -> None:
    ensure_output_dir()

    all_annual, all_summary = [], []
    print("Return periods — automatic stations")
    for station_id in STATION_ORDER:
        annual, summary = process_station(station_id)
        all_annual.append(annual)
        all_summary.append(summary)
        rp = plot_station_return_periods(station_id, summary)
        print(f"  {station_label(station_id)} → {rp}")

    print("Snowcourse (≈31 July ±21 d)")
    process_snowcourses()

    summary = pd.concat(all_summary, ignore_index=True)
    summary["station_id"] = summary["station_id"].astype(str).str.zfill(8)

    snowcourse_rp_summary = build_all_snowcourse_rp_summary()
    if not snowcourse_rp_summary.empty:
        snowcourse_rp_summary.to_csv(
            os.path.join(TABLES_DIR, "snowcourse_return_periods_by_route.csv"),
            index=False,
        )

    sf_annual, sf_summary = [], []
    for station_id in STATION_ORDER:
        annual_sf, summary_sf = process_station_snowfall(station_id)
        sf_annual.append(annual_sf)
        sf_summary.append(summary_sf)
    sf_summary_all = pd.concat(sf_summary, ignore_index=True)
    sf_summary_all["station_id"] = sf_summary_all["station_id"].astype(str).str.zfill(8)

    unified_path = os.path.join(FIG_RP, "all_stations_return_periods.png")
    plot_unified_return_periods(
        summary, sf_summary_all, snowcourse_rp_summary, unified_path
    )
    print(f"\nUnified return periods → {unified_path}")
    print("  (a) Δds/ΔSWE windows | (b) snowfall sums | (c) snowcourse Jul-31 + peak")

    sf_path = os.path.join(FIG_RP, "all_stations_snowfall_return_periods.png")
    plot_snowfall_return_periods(sf_summary_all, sf_path)
    print(f"Snowfall return periods (standalone) → {sf_path}")
    sf_summary_all.to_csv(
        os.path.join(TABLES_DIR, "snowfall_frequency_summary.csv"),
        index=False,
    )
    pd.concat(sf_annual, ignore_index=True).to_csv(
        os.path.join(TABLES_DIR, "snowfall_annual_events.csv"),
        index=False,
        date_format="%Y-%m-%d",
    )
    annual_all = pd.concat(all_annual, ignore_index=True)
    summary.to_csv(os.path.join(TABLES_DIR, "frequency_summary.csv"), index=False)
    annual_all.to_csv(
        os.path.join(TABLES_DIR, "annual_events.csv"),
        index=False,
        date_format="%Y-%m-%d",
    )
    print(f"\nTables: {TABLES_DIR}")


if __name__ == "__main__":
    main()
