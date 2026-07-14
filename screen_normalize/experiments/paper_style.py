from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt


METHOD_LABELS = {
    "frame_wise": "Frame-wise",
    "optical_flow": "Optical flow",
    "proposed": "Proposed",
    "proposal_border": "Proposal border",
    "point_edge": "Point-edge",
}
METHOD_COLORS = {
    "frame_wise": "#5B6470",
    "optical_flow": "#7C8FB8",
    "proposed": "#0F4D92",
    "proposal_border": "#2F7F73",
    "point_edge": "#806491",
}
METHOD_MARKERS = {
    "frame_wise": "o",
    "optical_flow": "s",
    "proposed": "D",
    "proposal_border": "P",
    "point_edge": "^",
}
METHOD_LINES = {
    "frame_wise": "-",
    "optical_flow": "--",
    "proposed": "-",
    "proposal_border": "-",
    "point_edge": "-.",
}
GRID_COLOR = "#D9DDDF"
TEXT_COLOR = "#242729"


def apply_paper_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "font.size": 7.8,
            "axes.titlesize": 8.5,
            "axes.labelsize": 7.8,
            "axes.edgecolor": TEXT_COLOR,
            "axes.labelcolor": TEXT_COLOR,
            "xtick.color": TEXT_COLOR,
            "ytick.color": TEXT_COLOR,
            "legend.fontsize": 7.4,
            "legend.frameon": False,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def finish_axis(axis: Any, panel: str, title: str, ylabel: str) -> None:
    axis.set_title(f"({panel}) {title}", loc="left", fontweight="bold", pad=7)
    axis.set_ylabel(ylabel)
    axis.grid(axis="y", color=GRID_COLOR, linewidth=0.6, alpha=0.9)
    axis.spines[["top", "right"]].set_visible(False)
    axis.set_axisbelow(True)
