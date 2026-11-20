"""Shared matplotlib styling for publication figures."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

# ONI phase backgrounds (CPC-style)
ONI_ZONES: list[tuple[float, float, str, float]] = [
    (-2.5, -0.5, "#cfe8ff", 0.38),
    (-0.5, 0.5, "#f0f0f0", 0.50),
    (0.5, 1.5, "#ffe4cc", 0.38),
    (1.5, 3.0, "#ffd0a8", 0.42),
]

# Current-year overlay: near-black for contrast with every station accent color.
COLOR_2026 = "#212121"
BAR_ACCENT = "#4a6fa5"
SPINE = "#bbbbbb"
GRID = "#e6e6e6"

# Manuscript snow-depth symbol (d with subscript s).
DS_LABEL = r"$d_s$"
DS_YLABEL_CM = rf"{DS_LABEL} (cm)"


def ds_window_xtick(days: int, *, short: bool = True) -> str:
    suffix = "-d" if short else "-day"
    return rf"{DS_LABEL} {days}{suffix}"


def ds_jul31_xtick() -> str:
    return rf"Jul-31 {DS_LABEL}"


def ds_peak_xtick() -> str:
    return rf"Peak {DS_LABEL}"


def panel_label(ax, letter: str, *, x: float = -0.12, y: float = 1.04) -> None:
    ax.text(
        x,
        y,
        f"({letter})",
        transform=ax.transAxes,
        fontsize=11,
        fontweight="bold",
        va="bottom",
        ha="left",
    )


def apply_article_style(*, palatino: bool = True) -> None:
    if palatino:
        font = {
            "font.family": "serif",
            "font.serif": [
                "Palatino",
                "Palatino Linotype",
                "TeX Gyre Pagella",
                "DejaVu Serif",
                "Times New Roman",
                "serif",
            ],
            "mathtext.fontset": "dejavuserif",
        }
    else:
        font = {
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica", "sans-serif"],
        }
    plt.rcParams.update(
        {
            **font,
            "font.size": 10,
            "axes.labelsize": 10,
            "axes.titlesize": 10,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 8.5,
            "axes.linewidth": 0.9,
            "xtick.major.width": 0.7,
            "ytick.major.width": 0.7,
            "xtick.major.pad": 4,
            "ytick.major.pad": 4,
            "axes.facecolor": "white",
            "figure.facecolor": "white",
            "figure.dpi": 150,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "savefig.facecolor": "white",
        }
    )


def clean_axes(ax, *, grid: bool = True) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(SPINE)
    ax.spines["bottom"].set_color(SPINE)
    ax.tick_params(colors="#333333", length=3, width=0.7)
    if grid:
        ax.set_axisbelow(True)
        ax.grid(True, axis="y", color=GRID, alpha=1.0, linewidth=0.7, linestyle="-")
    ax.set_facecolor("white")


def draw_oni_zones(ax, xlim: tuple[float, float] = (-2.5, 3.0)) -> None:
    ax.set_xlim(xlim)
    for x0, x1, color, alpha in ONI_ZONES:
        ax.axvspan(x0, x1, color=color, alpha=alpha, zorder=0, linewidth=0)


ONI_ZONE_LABELS: list[tuple[float, str, str]] = [
    (-1.5, "La Niña", "#2a5f8f"),
    (0.0, "Neutral", "#555555"),
    (1.0, "El Niño", "#a05a20"),
    (2.25, "Strong\nNiño", "#8B4513"),
]


def draw_oni_zone_labels(
    ax,
    *,
    y: float = 1.02,
    xlim: tuple[float, float] = (-2.5, 3.0),
) -> None:
    """ENSO phase names just above each panel, outside the data area."""
    x0, x1 = xlim
    for x_data, label, color in ONI_ZONE_LABELS:
        frac = (x_data - x0) / (x1 - x0)
        ax.text(
            frac,
            y,
            label,
            transform=ax.transAxes,
            ha="center",
            va="bottom",
            fontsize=9,
            color=color,
            fontweight="bold",
            linespacing=0.9,
            clip_on=False,
        )


def draw_oni_zone_labels_figure_col(
    fig,
    ax,
    *,
    y: float,
    xlim: tuple[float, float] = (-2.5, 3.0),
    fontsize: float = 9,
) -> None:
    """ENSO phase names above one column, aligned to that panel's ONI x-axis."""
    pos = ax.get_position()
    x0, x1 = xlim
    for x_data, label, color in ONI_ZONE_LABELS:
        frac = (x_data - x0) / (x1 - x0)
        fig.text(
            pos.x0 + frac * (pos.x1 - pos.x0),
            y,
            label,
            transform=fig.transFigure,
            ha="center",
            va="bottom",
            fontsize=fontsize,
            color=color,
            fontweight="bold",
            linespacing=0.9,
        )


def draw_oni_zone_labels_figure(
    fig,
    axes,
    *,
    y: float = 0.93,
    xlim: tuple[float, float] = (-2.5, 3.0),
) -> None:
    """Shared ENSO phase titles above all ONI panels (figure coordinates)."""
    ax_list = list(np.atleast_1d(axes).flat)
    left = min(ax.get_position().x0 for ax in ax_list)
    right = max(ax.get_position().x1 for ax in ax_list)
    span = right - left
    x0, x1 = xlim
    for x_data, label, color in ONI_ZONE_LABELS:
        frac = (x_data - x0) / (x1 - x0)
        fig.text(
            left + frac * span,
            y,
            label,
            transform=fig.transFigure,
            ha="center",
            va="bottom",
            fontsize=9.5,
            color=color,
            fontweight="bold",
            linespacing=0.9,
        )


def oni_point_colors(x: np.ndarray) -> np.ndarray:
    colors = np.empty(len(x), dtype=object)
    for i, xi in enumerate(x):
        if xi >= 1.5:
            colors[i] = "#E87722"
        elif xi >= 0.5:
            colors[i] = "#F5C4A8"
        elif xi <= -0.5:
            colors[i] = "#7FDBFF"
        else:
            colors[i] = "#9aa0a6"
    return colors


def scatter_points(
    ax,
    x,
    y,
    *,
    colors=None,
    size: float = 34,
    zorder: int = 3,
) -> None:
    ax.scatter(
        x,
        y,
        c=colors if colors is not None else "#505050",
        s=size,
        edgecolors="white",
        linewidths=0.55,
        alpha=0.92,
        zorder=zorder,
    )


def scatter_2026(ax, x, y) -> None:
    ax.scatter(
        [x],
        [y],
        c=COLOR_2026,
        marker="D",
        s=52,
        edgecolors="white",
        linewidths=0.75,
        zorder=6,
    )


def bar_series(ax, x, heights, color, *, width: float = 0.58, alpha: float = 0.88) -> None:
    ax.bar(
        x,
        heights,
        width=width,
        color=color,
        alpha=alpha,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
