# Current Paper Documents

本目录只放需要持续维护的最新论文文档和当前交付件。一次性实验输出、历史计划和冻结结果放在 `../archive/`，不要和当前状态混写。

## 目录

| 路径 | 用途 |
| --- | --- |
| `paper_status.md` | 当前事实、证据边界、完成项和下一步缺口的唯一入口 |
| `paper/source/proposal.pdf` | 已提交的正式 proposal，用于约束论文范围 |
| `paper_outline_zh.md` | 当前重写稿的章节、论点和验收规格 |
| `figure_plan.md` | 当前正文使用的主图、表格、数据来源和排除项 |
| `visual_style.md` | 论文图表和视觉风格约束 |
| `paper/manuscript/` | 中英文论文正文 Markdown、HTML、PDF、样式和当前主图 |
| `paper/references/samples/` | 教师提供的写作与排版样例 |
| `paper/references/papers/` | 项目正式参考的学术论文 |

`../archive/` 中的文档仅供追溯，不代表当前论文计划或当前实验事实，除非 `paper_status.md` 明确声明某个归档批次是当前采用的证据。

## 证据边界

- `paper_status.md` 是当前论文状态的权威摘要。
- `../archive/paper_results/2026-07-14-annotated-two-per-category/` 是当前正文采用的主证据批次，只包含补齐标注后的 geometry 和 temporal 重算。
- `../archive/paper_results/2026-07-14-first-pass/` 是早期完整 first-pass 归档，只作为工程追溯和辅助记录，不作为当前正文主要数值来源。
- 当前工作树有 50 个本地 active mp4 clip，五类各 10 个；每个 active clip 都有同名角点 CSV。
- 当前重写稿只主张参考帧锚定带来估计轨迹平滑性，但没有提升标注几何；不要改回“总体优于基线”的叙事。
- 原 mock 稿件和 mock 图表已从当前分支移除，不得将模拟数字用于论文结论。
