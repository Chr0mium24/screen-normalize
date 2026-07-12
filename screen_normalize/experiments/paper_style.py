from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt


METHOD_LABELS = {
    "frame_wise": "Frame-wise",
    "optical_flow": "Optical flow",
    "proposed": "Proposed",
}
METHOD_COLORS = {
    "frame_wise": "#526D82",
    "optical_flow": "#C58B3A",
    "proposed": "#2F7F73",
}
METHOD_MARKERS = {"frame_wise": "o", "optical_flow": "s", "proposed": "D"}
METHOD_LINES = {"frame_wise": "-", "optical_flow": "--", "proposed": "-"}
GRID_COLOR = "#D9DDDF"
TEXT_COLOR = "#242729"


def apply_paper_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.5,
            "axes.titlesize": 9,
            "axes.labelsize": 8.5,
            "axes.edgecolor": TEXT_COLOR,
            "axes.labelcolor": TEXT_COLOR,
            "xtick.color": TEXT_COLOR,
            "ytick.color": TEXT_COLOR,
            "legend.fontsize": 8,
            "legend.frameon": False,
            "svg.fonttype": "none",
        }
    )


def finish_axis(axis: Any, panel: str, title: str, ylabel: str) -> None:
    axis.set_title(f"({panel}) {title}", loc="left", fontweight="bold", pad=7)
    axis.set_ylabel(ylabel)
    axis.grid(axis="y", color=GRID_COLOR, linewidth=0.6, alpha=0.9)
    axis.spines[["top", "right"]].set_visible(False)
    axis.set_axisbelow(True)
