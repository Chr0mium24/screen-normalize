# Video Format Conversion

Date: 2026-07-14

## Goal

Convert active source videos under `inputs/` to MP4 so the project uses one video container format for collected data, segments, annotations, reports, and future batch commands.

## Converted Files

| Original active path | Current active path |
| --- | --- |
| `inputs/static/static_01.MOV` | `inputs/static/static_01.mp4` |
| `inputs/static/static_02.MOV` | `inputs/static/static_02.mp4` |
| `inputs/scrolling/scrolling_01.MOV` | `inputs/scrolling/scrolling_01.mp4` |
| `inputs/scrolling/scrolling_02.MOV` | `inputs/scrolling/scrolling_02.mp4` |
| `inputs/screen_video/screen_video_01.MOV` | `inputs/screen_video/screen_video_01.mp4` |
| `inputs/screen_video/screen_video_02.MOV` | `inputs/screen_video/screen_video_02.mp4` |
| `inputs/weak_border/weak_border_01.MOV` | `inputs/weak_border/weak_border_01.mp4` |

## Conversion Policy

The conversion used ffmpeg stream copy rather than re-encoding. Only the primary video stream and first AAC audio stream were retained:

```bash
ffmpeg -i input.MOV -map 0:v:0 -map 0:a:0? -c copy -movflags +faststart output.mp4
```

iPhone MOV metadata and unsupported auxiliary audio/data streams were intentionally omitted because MP4 cannot store them in the same form and the experiment only uses decoded video frames.

## Verification

- 7/7 MP4 files were generated.
- `ffprobe` successfully read every converted MP4.
- Source and target durations matched within container timestamp rounding.
- Active `inputs/` contains no `.MOV` or `.mov` files after cleanup.

Historical `old_source` entries in `doc/paper/data_renaming_manifest.csv` still record the original camera filenames. The `new_source` column now points to the active MP4 dataset paths.
