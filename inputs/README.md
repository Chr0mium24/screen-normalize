# Formal Dataset Inventory

当前 active 数据集按固定 5 秒 clip 组织，供 `scripts/run_batch.py --input inputs` 直接读取。

视频文件和人工标注 CSV 按 `.gitignore` 保持本地，不提交 Git；本目录中的清单和文档记录命名、来源和验证结果。

## Active clips

| Category | Active clips | Source rule |
| --- | ---: | --- |
| `scrolling` | 10 | `VID20260712165829.mp4` 每 5 秒切成 1 个样本 |
| `screen_video` | 10 | `VID20260712170039.mp4`、`VID20260712170115.mp4` 各切 5 个样本 |
| `static` | 10 | 5 个短视频各裁到 5 秒，`VID20260712170211.mp4` 再切 5 个样本 |
| `weak_border` | 0 | 当前未纳入 active 数据集 |
| `hard` | 0 | 当前未纳入 active 数据集 |

## Naming contract

```text
inputs/<category>/<category>_<two_digit_id>.mp4
```

示例：

```text
inputs/scrolling/scrolling_01.mp4
inputs/screen_video/screen_video_06.mp4
inputs/static/static_10.mp4
```

## Local raw archive

原始采集视频已从工作区根目录 `premodify/` 移入：

```text
inputs/archive/raw_premodify_2026-07-14/
```

旧的未标注归档仍保留在：

```text
inputs/archive/removed_unannotated_2026-07-14/
```

## Reproducibility records

- 构建脚本：`scripts/archive/dataset/build_formal_dataset.py`
- 样本来源清单：`doc/archive/paper_workspace_cleanup_2026-07-14/generated_outputs/dataset_5s_manifest_2026-07-14.csv`
- 本次整理记录：`doc/paper/plan/dataset_organization_2026-07-14.md`
