# Annotated Dataset Mosaic

Generated on 2026-07-14.

## Output

- `annotated_dataset_mosaic.jpg`: 15 annotated samples arranged as one row per category, three samples per row.
- `annotated_dataset_mosaic_manifest.csv`: selected frame and source media for each tile.

## Selection Rule

Categories included:

1. `scrolling`
2. `screen_video`
3. `static`
4. `weak_border`
5. `hard`

For `scrolling`, `screen_video`, `static`, and `weak_border`, the figure uses samples `01` through `03`.
For `hard`, the figure displays IDs `hard_01` through `hard_03`, but the source media are `hard_11.jpg`, `hard_12.jpg`, and `hard_13.jpg`.

For each sample, the script uses frame `0` if that frame has a corner annotation. If frame `0` is not annotated, it uses the earliest annotated frame in the sample CSV.

In the current output, all 15 samples use frame `0`.

## Regeneration

Run from the repository root:

```bash
uv run python scripts/paper/build_dataset_mosaic.py
```
