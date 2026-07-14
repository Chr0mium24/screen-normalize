# Current Paper Documents

本目录只保留当前需要维护和交付的论文材料。历史计划、旧审稿意见、demo 记录和被当前稿件取代的结果说明已经归档到 `../archive/current_cleanup_2026-07-14/`。

## Current Entry Points

| 路径 | 用途 |
| --- | --- |
| `paper/manuscript/` | 当前中英文论文源文件、HTML、PDF、样式和主图 |
| `paper/source/proposal.pdf` | 正式 proposal，用于约束论文范围 |
| `paper/references/papers/` | 当前论文引用的学术文献 |
| `paper/references/samples/` | 教师提供的写作与排版样例 |
| `paper/rewrite_notes_2026-07-14.md` | 当前论文主线、证据映射和图表说明 |
| `paper/proposal_border_ablation_2026-07-14.md` | 当前 Proposed 方法的模块和边框消融结果 |

## Current Manuscript State

- 当前论文主线是 **border-guided screen-plane normalization**。
- `proposal_border` 是正文 Proposed 方法；它使用 profile-based physical border observations。
- 主实验使用 `runs/20260714_small_sample_with_proposal_border`，覆盖五类拍摄条件、每类两个代表 clip。
- current Proposed 消融使用 `runs/20260714_proposal_border_ablation_scrolling_01`，比较 no-border diagnostics、border-observation variants 和功能模块变体。
- 正文只主张几何屏幕平面归一化，不主张内容恢复或去摩尔纹质量。

## Archive Boundary

`../archive/` 中的文档仅供追溯，不代表当前论文结论。尤其是旧 reference-anchored Proposed 结果、旧消融、旧图表计划和早期 review notes 都不应再作为正文主证据使用。
