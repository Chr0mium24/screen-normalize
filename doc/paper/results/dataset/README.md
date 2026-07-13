# Annotated Dataset Mosaic

Generated on 2026-07-14.

## Output

- `annotated_dataset_mosaic.jpg`: 30 annotated clips arranged as one row per category.
- `annotated_dataset_mosaic_manifest.csv`: selected frame for each tile.

## Selection Rule

Categories included:

1. `scrolling`
2. `screen_video`
3. `static`

For each clip, the script uses frame `0` if that frame has a corner annotation. If frame `0` is not annotated, it uses the earliest annotated frame in the clip CSV.

In the current output, `static_08` uses frame `74`; all other clips use frame `0`.

## Regeneration

Run from the repository root:

```bash
uv run python scripts/paper/build_dataset_mosaic.py
```
