# Documentation Layout

本目录分成两个用途明确的路径：

| 路径 | 用途 | 更新方式 |
| --- | --- | --- |
| `current/` | 持续维护的最新状态、论文稿件、图表计划、参考材料和入口 README | 直接更新原文件，始终代表当前判断 |
| `archive/` | 已冻结的实验结果、历史计划、旧稿、一次性操作记录和生成物 | 新增带日期或批次名的子目录，不覆盖旧记录 |

## Current

- `current/README.md`：当前论文文档入口。
- `current/paper_status.md`：当前事实、证据边界、完成项和下一步缺口。
- `current/paper_outline_zh.md`：最终论文结构和验收规格。
- `current/figure_plan.md`：主图、表格和数据来源规划。
- `current/visual_style.md`：论文图表视觉规范。
- `current/paper/manuscript/`：当前中英文论文源文件、PDF、HTML 和主图。
- `current/paper/references/`：当前仍需引用的论文和课程样例。
- `current/paper/source/proposal.pdf`：正式 proposal。

## Archive

- `archive/paper_results/2026-07-14-first-pass/`：当前提交过的 first-pass 主实验、消融、调参 smoke、数据 mosaic 和证据文件。
- `archive/paper_workspace_cleanup_2026-07-14/`：论文工作区清理前移出的旧计划、占位图、生成报告和操作记录。
- `archive/development_notes/`：开发复盘和方法探针。
- `archive/previous_drafts/`：已被当前论文取代的旧稿件。
- `archive/previous_plans/`：旧项目目标、方向决策、实验计划和答辩大纲。

新实验如果需要提交结果，应在 `archive/paper_results/` 下新建批次目录，并在 `current/paper_status.md` 中更新“当前采用哪一批证据”。
