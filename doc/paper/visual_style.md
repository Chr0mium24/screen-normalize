# Paper Figure and Table Style

This style is derived from the retained teacher sample's visual discipline rather than copied from any individual panel.

## 1. Figure system

- Export all charts as SVG with editable text (`svg.fonttype = none`).
- Use a 7.2-inch full-width canvas. Single-column panels use 3.45 inches.
- Use 8.5 pt body text, 9 pt panel titles, and 0.8--1.4 pt data strokes.
- Place bold panel labels `(a)`, `(b)`, ... at the upper left of each axis.
- Remove top and right spines; use light horizontal grid lines only.
- State units in axis labels, not in legends or titles.
- Show individual clip values whenever space permits. A summary mark must not hide the sample distribution.
- Keep method identity constant across every figure:

| Method | Color | Marker | Line |
| --- | --- | --- | --- |
| Frame-wise | `#526D82` | circle | solid |
| Optical flow | `#C58B3A` | square | dashed |
| Proposed | `#2F7F73` | diamond | solid, heavier |

Supporting colors are muted plum `#806491`, failure red `#B55D5D`, neutral gray `#6F7478`, and grid gray `#D9DDDF`. Do not use rainbow maps for categorical comparisons.

## 2. Table system

- No vertical rules in paper tables.
- Use a dark header rule, light row separators, and restrained gray header fill in HTML review output.
- Put the direction of improvement in the metric header using arrows (`↓` or `↑`).
- Report `n` next to every aggregate.
- Prefer `median [Q1, Q3]` for small or skewed clip sets; add mean ± standard deviation only when justified.
- Bold the best value only after formal results are frozen. Pilot tables must not automatically mark winners.
- Use the same method order as the figures: Frame-wise, Optical flow, Proposed.

## 3. Figure-plan coverage

| Planned item | Automatic source | Current behavior |
| --- | --- | --- |
| Figure 1 pipeline | saved intermediate frames | pending dedicated assets; never synthesized |
| Figure 2 dataset/annotations | formal representative frames and corner CSV | pending formal dataset |
| Figure 3 geometry | `geometry.json` across annotated clips | generated only when geometry status is `ok` |
| Figure 4 temporal | `temporal_frames.csv` and `temporal.json` | generated from a representative reviewed clip plus aggregate table |
| Figure 5 qualitative | original and three normalized videos | pending reviewed frame selection |
| Figure 6 detail/frequency | `detail.json`, `frequency.json`, spectra and crops | generated only for available subpanels |
| Figure 7 ablation | records explicitly tagged `experiment=ablation` | omitted until real ablation runs exist |
| Figure 8 failures | audited failed clips and notes | pending manual audit |
| Figure 9 speed | `method.json` elapsed time | optional; generated after runtime protocol is frozen |

Missing data produces an omitted figure and a manifest entry, not an empty panel or mock value.

