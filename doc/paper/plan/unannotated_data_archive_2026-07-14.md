# Unannotated Data Archive

Date: 2026-07-14

## Goal

Remove videos without annotation from the active dataset while preserving a local backup. The active `inputs/` dataset should only contain clips that can be used by the current paper experiments without ambiguity.

## Archived Targets

The following unannotated sources and their segment directories were moved to `inputs/archive/removed_unannotated_2026-07-14/`:

| Category | Clip ID | Archived source | Archived segments |
| --- | --- | --- | --- |
| static | `static_01` | `inputs/archive/removed_unannotated_2026-07-14/static/static_01.mp4` | `inputs/archive/removed_unannotated_2026-07-14/static/segments/static_01/` |
| static | `static_03` | `inputs/archive/removed_unannotated_2026-07-14/static/static_03.mp4` | none |
| scrolling | `scrolling_01` | `inputs/archive/removed_unannotated_2026-07-14/scrolling/scrolling_01.mp4` | `inputs/archive/removed_unannotated_2026-07-14/scrolling/segments/scrolling_01/` |
| scrolling | `scrolling_02` | `inputs/archive/removed_unannotated_2026-07-14/scrolling/scrolling_02.mp4` | `inputs/archive/removed_unannotated_2026-07-14/scrolling/segments/scrolling_02/` |
| screen_video | `screen_video_01` | `inputs/archive/removed_unannotated_2026-07-14/screen_video/screen_video_01.mp4` | `inputs/archive/removed_unannotated_2026-07-14/screen_video/segments/screen_video_01/` |
| screen_video | `screen_video_02` | `inputs/archive/removed_unannotated_2026-07-14/screen_video/screen_video_02.mp4` | `inputs/archive/removed_unannotated_2026-07-14/screen_video/segments/screen_video_02/` |
| weak_border | `weak_border_01` | `inputs/archive/removed_unannotated_2026-07-14/weak_border/weak_border_01.mp4` | `inputs/archive/removed_unannotated_2026-07-14/weak_border/segments/weak_border_01/` |

## Active Dataset After Cleanup

The active dataset now contains only:

- `inputs/static/static_02.mp4`
- `inputs/scrolling/scrolling_03.mp4`
- `inputs/screen_video/screen_video_03.mp4`
- `inputs/hard/hard_01.mp4`

Their existing segment videos and annotation CSV files remain in active `inputs/`.

## Verification

- No annotation CSV belonged to the archived unannotated targets.
- Active `inputs/` now contains only the four representative source videos and their existing annotated segments.
- `doc/paper/data_renaming_manifest.csv` records archived paths with role `archived_unannotated_backup`.
