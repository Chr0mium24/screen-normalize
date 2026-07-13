# Collected Dataset Inventory

数据采集阶段已完成。正式输入使用 `category_NN` 作为 clip ID；分段目录、分段视频和角点 CSV 必须继承同一个 clip ID。

## Source clips

| Category | Collected source clips | Representative evidence clip |
| --- | --- | --- |
| `static` | `static_01.mp4`, `static_02.mp4`, `static_03.mp4` | `segments/static_02/static_02_000.mp4` |
| `scrolling` | `scrolling_01.mp4`, `scrolling_02.mp4`, `scrolling_03.mp4` | `segments/scrolling_03/scrolling_03_000.mp4` |
| `screen_video` | `screen_video_01.mp4`, `screen_video_02.mp4`, `screen_video_03.mp4` | `segments/screen_video_03/screen_video_03_000.mp4` |
| `weak_border` | `weak_border_01.mp4` | `segments/weak_border_01/weak_border_01_000.mp4` |
| `hard` | `hard_01.mp4` | `hard_01.mp4` |

## Current completion state

- [x] 五类原视频均已收集。
- [x] 原视频、分段目录和已有标注统一命名。
- [x] static 代表 clip 已标注并有历史完整报告。
- [x] scrolling 代表 clip 已标注并有历史完整报告。
- [x] screen_video 代表 clip 已标注并有历史完整报告。
- [x] weak_border 数据已收集；当前实验范围明确排除该类别，因此不要求代表标注和报告。
- [x] hard 代表 clip 已标注并有历史完整报告。

## Naming contract

```text
inputs/<category>/<clip_id>.<ext>
inputs/<category>/segments/<clip_id>/<clip_id>_<segment>.mp4
inputs/<category>/segments/<clip_id>/<clip_id>_<segment>.csv
```

旧名称与新名称的完整对应关系见 `doc/paper/data_renaming_manifest.csv`。`premodify/` 是未归档原始素材，不属于正式 `inputs/` 命名空间。
