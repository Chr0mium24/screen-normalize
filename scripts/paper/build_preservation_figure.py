from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from screen_normalize.experiments.paper_style import apply_paper_style


ROOT = Path(__file__).resolve().parents[2]
METHODS = ("frame_wise", "optical_flow", "proposal_border")
METHOD_LABELS = {
    "frame_wise": "Frame-wise",
    "optical_flow": "Optical flow",
    "proposal_border": "Proposed",
}
METHOD_COLORS = {
    "frame_wise": "#5B6470",
    "optical_flow": "#7C8FB8",
    "proposal_border": "#2F7F73",
}
GRID = "#D9DDDF"
TEXT = "#242729"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build signal-preservation diagnostic figure.")
    parser.add_argument(
        "--detail",
        type=Path,
        default=ROOT
        / "runs"
        / "20260714_detail_preservation_demo_scrolling_01"
        / "detail_preservation_summary.csv",
    )
    parser.add_argument(
        "--frequency",
        type=Path,
        default=ROOT
        / "runs"
        / "20260714_frequency_preservation_demo_scrolling_01"
        / "frequency_preservation_summary.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "doc" / "current" / "paper" / "manuscript" / "figures" / "figure_06_signal_preservation.png",
    )
    parser.add_argument("--dpi", type=int, default=300)
    return parser.parse_args()


def read_summary(path: Path) -> dict[str, dict[str, float]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    result: dict[str, dict[str, float]] = {}
    for row in rows:
        method = row["method"]
        result[method] = {
            key: float(value)
            for key, value in row.items()
            if key not in {"method", "frames"} and value not in {"", None}
        }
    return result


def style_axis(axis: plt.Axes, panel: str, title: str, ylabel: str) -> None:
    axis.set_title(f"{panel}  {title}", loc="left", fontsize=8.5, fontweight="bold")
    axis.set_ylabel(ylabel)
    axis.grid(axis="y", color=GRID, linewidth=0.6, alpha=0.9)
    axis.spines[["top", "right"]].set_visible(False)
    axis.set_axisbelow(True)


def label_bars(axis: plt.Axes, bars: object, fmt: str = "{:.3f}") -> None:
    ymin, ymax = axis.get_ylim()
    offset = 0.018 * (ymax - ymin)
    for bar in bars:
        height = float(bar.get_height())
        x = bar.get_x() + bar.get_width() / 2
        axis.text(x, height + offset, fmt.format(height), ha="center", va="bottom", fontsize=5.7, color=TEXT)


def grouped_bars(
    axis: plt.Axes,
    data: dict[str, dict[str, float]],
    fields: list[tuple[str, str]],
    title: str,
    ylabel: str,
    panel: str,
    ylim: tuple[float, float] | None = None,
) -> None:
    x = np.arange(len(fields))
    width = 0.23
    offsets = np.linspace(-width, width, len(METHODS))
    containers = []
    for offset, method in zip(offsets, METHODS):
        values = [data[method][field] for field, _ in fields]
        bars = axis.bar(
            x + offset,
            values,
            width=width,
            label=METHOD_LABELS[method],
            color=METHOD_COLORS[method],
            edgecolor="#2B2B2B",
            linewidth=0.55,
        )
        containers.append(bars)
    axis.set_xticks(x, [label for _, label in fields])
    if ylim is not None:
        axis.set_ylim(*ylim)
    style_axis(axis, panel, title, ylabel)
    for bars in containers:
        label_bars(axis, bars)


def add_one_reference(axis: plt.Axes) -> None:
    axis.axhline(1.0, color="#9C6B2F", linewidth=0.9, linestyle="--")
    axis.text(
        0.99,
        1.01,
        "perfect ratio",
        transform=axis.get_yaxis_transform(),
        ha="right",
        va="bottom",
        fontsize=7,
        color="#7B5526",
    )


def save(fig: plt.Figure, output: Path, dpi: int) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    base = output.with_suffix("")
    fig.savefig(base.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(base.with_suffix(".png"), dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    args = parse_args()
    apply_paper_style()
    detail = read_summary(args.detail)
    frequency = read_summary(args.frequency)

    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.15))
    fig.subplots_adjust(left=0.08, right=0.985, top=0.81, bottom=0.10, wspace=0.18, hspace=0.44)
    grouped_bars(
        axes[0, 0],
        detail,
        [
            ("ssim_median", "SSIM"),
            ("gradient_magnitude_similarity_median", "Grad sim"),
            ("edge_f1_median", "Edge F1"),
        ],
        "Detail structure similarity",
        "higher is better",
        "a",
        (0.0, 1.05),
    )
    grouped_bars(
        axes[0, 1],
        detail,
        [
            ("gradient_log_ratio_abs_median", "Grad"),
            ("laplacian_log_ratio_abs_median", "Laplacian"),
        ],
        "Detail energy-ratio distance",
        "lower is better",
        "b",
        (0.0, 0.055),
    )
    grouped_bars(
        axes[1, 0],
        frequency,
        [
            ("log_fft_magnitude_similarity_median", "FFT sim"),
            ("orientation_histogram_intersection_median", "Orient hist"),
        ],
        "Frequency structure similarity",
        "higher is better",
        "c",
        (0.94, 1.005),
    )
    grouped_bars(
        axes[1, 1],
        frequency,
        [
            ("high_frequency_energy_ratio_median", "HF ratio"),
            ("band_energy_ratio_median", "Band ratio"),
        ],
        "Frequency energy ratios",
        "closer to 1 is better",
        "d",
        (0.94, 1.04),
    )
    add_one_reference(axes[1, 1])
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 0.90))
    fig.suptitle(
        "Reference-based signal preservation diagnostics on scrolling_01",
        fontsize=9.6,
        fontweight="bold",
        color=TEXT,
        y=0.98,
    )
    save(fig, args.output, args.dpi)
    print(f"wrote {args.output.with_suffix('.png')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
