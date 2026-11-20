"""Shared calendar window for snow-season climatology figures (Apr–Dec)."""

from __future__ import annotations

import matplotlib.dates as mdates
import pandas as pd

CLIMATOLOGY_MONTH_START = 4
CLIMATOLOGY_MONTH_END = 12
CLIMATOLOGY_MONTHS = tuple(range(CLIMATOLOGY_MONTH_START, CLIMATOLOGY_MONTH_END + 1))


def filter_apr_dec(df: pd.DataFrame) -> pd.DataFrame:
    month = df["date"].dt.month
    return df.loc[month.between(CLIMATOLOGY_MONTH_START, CLIMATOLOGY_MONTH_END)].copy()


def climatology_xlim(axis_year: int) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Apr 1 through end of December (right edge = Jan 1 next year, no January tick)."""
    return (
        pd.Timestamp(year=axis_year, month=CLIMATOLOGY_MONTH_START, day=1),
        pd.Timestamp(year=axis_year + 1, month=1, day=1),
    )


def apply_climatology_xlim(ax, axis_year: int) -> None:
    xmin, xmax = climatology_xlim(axis_year)
    ax.set_xlim(xmin, xmax)
    ax.margins(x=0)


def configure_climatology_xaxis(
    ax,
    axis_year: int,
    *,
    tick_labelsize: float | None = None,
) -> None:
    """Apr–Dec axis: month ticks only, no padding after December."""
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=list(CLIMATOLOGY_MONTHS)))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    apply_climatology_xlim(ax, axis_year)
    if tick_labelsize is not None:
        ax.tick_params(axis="x", labelsize=tick_labelsize)
