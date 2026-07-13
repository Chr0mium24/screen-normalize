# Collected Dataset Inventory

数据采集阶段已完成。Active 数据集只保留已有标注/完整报告的代表 clip；未标注视频已备份到 `archive/removed_unannotated_2026-07-14/`，不再参与当前实验。

## Source clips

| Category | Collected source clips | Representative evidence clip |
| --- | --- | --- |
| `static` | `static_02.mp4` | `segments/static_02/static_02_000.mp4` |
| `scrolling` | `scrolling_03.mp4` | `segments/scrolling_03/scrolling_03_000.mp4` |
| `screen_video` | `screen_video_03.mp4` | `segments/screen_video_03/screen_video_03_000.mp4` |
| `weak_border` | archived only | excluded |
| `hard` | `hard_01.mp4` | `hard_01.mp4` |

## Current completion state

- [x] 四个 active 代表源视频均有标注和历史完整报告。
- [x] 未标注源视频和分段已备份并移出 active 数据集。
- [x] active 原视频、分段目录和已有标注统一命名。
- [x] static 代表 clip 已标注并有历史完整报告。
- [x] scrolling 代表 clip 已标注并有历史完整报告。
- [x] screen_video 代表 clip 已标注并有历史完整报告。
- [x] weak_border 已备份归档；当前实验范围明确排除该类别，因此不要求代表标注和报告。
- [x] hard 代表 clip 已标注并有历史完整报告。

## Naming contract

```text
inputs/<category>/<clip_id>.<ext>
inputs/<category>/segments/<clip_id>/<clip_id>_<segment>.mp4
inputs/<category>/segments/<clip_id>/<clip_id>_<segment>.csv
```

旧名称、active 路径和归档路径的完整对应关系见 `doc/paper/data_renaming_manifest.csv`。`premodify/` 是未归档原始素材，不属于正式 `inputs/` 命名空间。
