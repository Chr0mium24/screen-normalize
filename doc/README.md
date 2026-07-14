# Documentation Layout

本目录分成两个用途明确的路径：

| 路径 | 用途 | 更新方式 |
| --- | --- | --- |
| `current/` | 当前论文交付入口、当前稿件、参考文献和当前证据说明 | 直接更新原文件，始终代表当前判断 |
| `archive/` | 已冻结的实验结果、历史计划、旧稿、一次性操作记录和生成物 | 新增带日期或批次名的子目录，不覆盖旧记录 |

## Current

- `current/README.md`：当前论文文档入口。
- `current/paper/manuscript/`：当前中英文论文源文件、PDF、HTML 和主图。
- `current/paper/rewrite_notes_2026-07-14.md`：当前论文主线、图表和证据映射。
- `current/paper/proposal_border_ablation_2026-07-14.md`：当前 Proposed 方法的模块和边框消融结果。
- `current/paper/frequency_preservation_demo_2026-07-14.md`：reference-based 高频/摩尔纹信号保留诊断 demo。
- `current/paper/references/`：当前仍需引用的论文和课程样例。
- `current/paper/source/proposal.pdf`：正式 proposal。

## Archive

- `archive/current_cleanup_2026-07-14/`：从 `current/` 顶层移出的旧计划、旧 review、demo 记录和被当前稿件取代的结果说明。
- `archive/paper_results/2026-07-14-first-pass/`：早期 first-pass 主实验、旧消融、调参 smoke、数据 mosaic 和证据文件。
- `archive/paper_results/2026-07-14-annotated-two-per-category/`：旧 reference-anchored 论文阶段的两例每类重跑结果。
- `archive/paper_workspace_cleanup_2026-07-14/`：论文工作区早期清理前移出的旧计划、占位图、生成报告和操作记录。
- `archive/development_notes/`：开发复盘和方法探针。
- `archive/previous_drafts/`：已被当前论文取代的旧稿件。
- `archive/previous_plans/`：旧项目目标、方向决策、实验计划和答辩大纲。

新实验如果需要提交结果，应优先保存为 Markdown 记录；若结果不再代表当前稿件，应放入 `archive/` 的日期批次目录。
