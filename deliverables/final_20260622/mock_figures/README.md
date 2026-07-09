# Mock Final Figures

These CSV and SVG files are mock ideal-result figures for planning the final report and presentation. They are not measured experiment outputs.

Regenerate them with:

```bash
uv run scripts/make_mock_final_figures.py
```

Files:

- `mock_final_metrics.csv`: scenario-by-method mock summary metrics.
- `mock_temporal_metrics.csv`: frame-level mock residual motion for the timeline chart.
- `mock_ablation_translation_bar.svg`: method ablation summary.
- `mock_scenario_method_heatmap.svg`: scenario-by-method robustness heatmap.
- `mock_geometry_signal_panel.svg`: geometry and signal metric panel.
- `mock_fft_orthogonality_bar.svg`: frequency-domain regularity diagnostic.
- `mock_temporal_stability_timeline.svg`: frame-level stability timeline.
