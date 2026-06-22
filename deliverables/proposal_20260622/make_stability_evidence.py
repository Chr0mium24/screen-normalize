"""Generate the stability-evidence figure for the proposal deck.

Plots the per-frame residual translation of the reference-plane (border-guided)
method over time, against the p95 baselines of all three tracking strategies.
All numbers come straight from evidence/*.csv (real measurements).

Usage:
    python deliverables/proposal_20260622/make_stability_evidence.py
"""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
EVID = HERE / "evidence"
OUT = HERE / "assets" / "stability_evidence.png"

# palette (matches slide 7 ablation bar chart)
RED = "#E24A3B"      # per-frame detection
ORANGE = "#F08A24"   # optical-flow tracking
BLUE = "#1F57C4"     # reference-plane (ours)
GRID = "#D9DEE8"

# ---------------------------------------------------------------- load data
# per-frame residual translation of the reference-plane method
times, trans = [], []
with open(EVID / "stability_metrics.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        times.append(float(r["time_seconds"]))
        trans.append(float(r["translation_px"]))

# three methods' p95 (last 2 s) — rows are fixed order: per-frame, optical-flow, reference-plane
with open(EVID / "proposal_ablation_summary.csv", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
p95_perframe = float(rows[0]["translation_p95_px_last2s"])
p95_flow = float(rows[1]["translation_p95_px_last2s"])
p95_ref = float(rows[2]["translation_p95_px_last2s"])

ratio = p95_perframe / p95_ref

# ---------------------------------------------------------------- plot
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12})
fig, ax = plt.subplots(figsize=(10.6, 5.0), dpi=150)

# reference-plane per-frame curve
ax.fill_between(times, trans, color=BLUE, alpha=0.12, zorder=2)
ax.plot(times, trans, color=BLUE, lw=1.4, zorder=3,
        label="Reference-plane (ours) — per-frame residual")

# p95 baselines as horizontal dashed lines
ax.axhline(p95_perframe, color=RED, ls="--", lw=1.8, zorder=2)
ax.axhline(p95_flow, color=ORANGE, ls=(0, (6, 3)), lw=1.8, zorder=2)
ax.axhline(p95_ref, color=BLUE, ls=":", lw=1.8, zorder=2)

# left-side labels for the two baselines (their lines nearly overlap near y≈1.93)
xmax = max(times)
ax.text(0.08, p95_perframe + 0.06, f"Per-frame detection   p95 = {p95_perframe:.3f} px",
        color=RED, ha="left", va="bottom", fontsize=11.5, fontweight="bold")
ax.text(0.08, p95_flow - 0.16, f"Optical-flow tracking   p95 = {p95_flow:.3f} px",
        color=ORANGE, ha="left", va="bottom", fontsize=11.5, fontweight="bold")
# ours label sits on its own low line, right side
ax.text(xmax * 0.995, p95_ref + 0.06, f"Reference-plane (ours)   p95 = {p95_ref:.3f} px",
        color=BLUE, ha="right", va="bottom", fontsize=11.5, fontweight="bold")

ax.set_xlim(0, xmax)
ax.set_ylim(0, 2.15)
ax.set_xlabel("Time (s)")
ax.set_ylabel("Residual translation per frame (px)")
ax.set_title("Residual frame-to-frame motion after normalization  (same input video)",
             fontsize=14, fontweight="bold", pad=12)
ax.grid(True, color=GRID, lw=0.8)
ax.set_axisbelow(True)
for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)

# improvement callout: a clean vertical double-arrow spanning the two p95 levels
xcb = 3.25
ax.annotate("", xy=(xcb, p95_perframe), xytext=(xcb, p95_ref),
            arrowprops=dict(arrowstyle="<|-|>", color="#333", lw=1.7))
ax.text(xcb + 0.12, (p95_perframe + p95_ref) / 2, f"≈ {ratio:.0f}×\nlower",
        color="#222", fontsize=12.5, fontweight="bold", ha="left", va="center")

# inset: zoom on the ours curve (0–0.2 px) to show it is genuinely flat
axin = ax.inset_axes([0.56, 0.58, 0.40, 0.34])
axin.fill_between(times, trans, color=BLUE, alpha=0.15)
axin.plot(times, trans, color=BLUE, lw=1.1)
axin.axhline(p95_ref, color=BLUE, ls=":", lw=1.3)
axin.set_ylim(0, 0.20)
axin.set_xlim(0, xmax)
axin.set_title("zoom · 0–0.2 px", fontsize=10, color="#444")
axin.tick_params(labelsize=8)
axin.grid(True, color=GRID, lw=0.6)
for spine in ("top", "right"):
    axin.spines[spine].set_visible(False)

fig.tight_layout()
fig.savefig(OUT, dpi=150, bbox_inches="tight", facecolor="white")
print(f"Saved: {OUT}  ({len(times)} frames, ~{xmax:.2f}s, ratio={ratio:.1f}x)")
