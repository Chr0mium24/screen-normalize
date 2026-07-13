# Dataset Organization Record — 2026-07-14

## Goal

整理本地原始拍屏视频，生成当前实验可直接批量运行的正式 5 秒 clip 数据集。

## Input material

原始素材来自工作区根目录 `premodify/`。整理完成后，原始目录已归档到：

```text
inputs/archive/raw_premodify_2026-07-14/
```

## Build plan

| Category | Rule | Output clips |
| --- | --- | ---: |
| `scrolling` | `VID20260712165829.mp4` 从 0s 开始每 5s 切一段 | 10 |
| `screen_video` | `VID20260712170039.mp4`、`VID20260712170115.mp4` 各切 5 段 | 10 |
| `static` | 5 个短视频各取前 5s；`VID20260712170211.mp4` 切 5 段 | 10 |
| `weak_border` | 5 个短视频各取前 5s | 5 |

输出路径统一为：

```text
inputs/<category>/<category>_<two_digit_id>.mp4
```

## Source mapping

| Output range | Source video | Start seconds |
| --- | --- | --- |
| `scrolling_01`–`scrolling_10` | `VID20260712165829.mp4` | `0, 5, ..., 45` |
| `screen_video_01`–`screen_video_05` | `VID20260712170039.mp4` | `0, 5, 10, 15, 20` |
| `screen_video_06`–`screen_video_10` | `VID20260712170115.mp4` | `0, 5, 10, 15, 20` |
| `static_01` | `VID20260712170254.mp4` | `0` |
| `static_02` | `VID20260712170303.mp4` | `0` |
| `static_03` | `VID20260712170318.mp4` | `0` |
| `static_04` | `VID20260712170428.mp4` | `0` |
| `static_05` | `VID20260712170444.mp4` | `0` |
| `static_06`–`static_10` | `VID20260712170211.mp4` | `0, 5, 10, 15, 20` |
| `weak_border_01` | `VID20260712170738.mp4` | `0` |
| `weak_border_02` | `VID20260712170803.mp4` | `0` |
| `weak_border_03` | `VID20260712170822.mp4` | `0` |
| `weak_border_04` | `VID20260712170854.mp4` | `0` |
| `weak_border_05` | `VID20260712170915.mp4` | `0` |

完整逐 clip 清单见 `doc/archive/paper_workspace_cleanup_2026-07-14/generated_outputs/dataset_5s_manifest_2026-07-14.csv`。

## Execution

使用可复现脚本生成：

```bash
uv run python scripts/archive/dataset/build_formal_dataset.py \
  --mode nvenc \
  --force \
  --manifest doc/archive/paper_workspace_cleanup_2026-07-14/generated_outputs/dataset_5s_manifest_2026-07-14.csv \
  --archive-raw
```

说明：

- 先尝试 stream copy 时发现 `scrolling_02` 输出为 6.002s，不满足 5 秒样本要求。
- 最终使用 `h264_nvenc` 重编码裁切，保证时间边界稳定。
- 输出保留原始 3840×2160、60 fps 视频规格；音轨未保留。

## Validation result

| Category | Count | Duration range | Resolution | Frame rate |
| --- | ---: | --- | --- | --- |
| `scrolling` | 10 | 4.983s–5.000s | 3840×2160 | 60 fps |
| `screen_video` | 10 | 4.983s–5.000s | 3840×2160 | 60 fps |
| `static` | 10 | 4.983s–5.000s | 3840×2160 | 60 fps |
| `weak_border` | 5 | 5.000s–5.000s | 3840×2160 | 60 fps |

总计生成 35 个 active clip。`premodify/` 已不存在于工作区根目录，根目录只保留项目目录。

## Current dataset layout

```text
inputs/
├── scrolling/
│   ├── scrolling_01.mp4
│   └── ...
├── screen_video/
│   ├── screen_video_01.mp4
│   └── ...
├── static/
│   ├── static_01.mp4
│   └── ...
├── weak_border/
│   ├── weak_border_01.mp4
│   └── ...
└── archive/
    └── raw_premodify_2026-07-14/
```
