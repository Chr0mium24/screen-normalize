# Current Paper Documents

本目录只放需要持续维护的最新论文文档和当前交付件。一次性实验输出、历史计划和冻结结果放在 `../archive/`，不要和当前状态混写。

## 目录

| 路径 | 用途 |
| --- | --- |
| `paper_status.md` | 当前事实、证据边界、完成项和下一步缺口的唯一入口 |
| `paper/source/proposal.pdf` | 已提交的正式 proposal，用于约束论文范围 |
| `paper_outline_zh.md` | 最终论文的章节、论点和验收规格 |
| `figure_plan.md` | 7–9 个主图、表格、数据来源和结果槽位 |
| `visual_style.md` | 论文图表和视觉风格约束 |
| `paper/manuscript/` | 中英文论文正文 Markdown、HTML、PDF、样式和当前主图 |
| `paper/references/samples/` | 教师提供的写作与排版样例 |
| `paper/references/papers/` | 项目正式参考的学术论文 |

`../archive/` 中的文档仅供追溯，不代表当前论文计划或当前实验事实，除非 `paper_status.md` 明确声明某个归档批次是当前采用的证据。

## 证据边界

- `paper_status.md` 是当前论文状态的权威摘要。
- `../archive/paper_results/2026-07-14-first-pass/results/full_pipeline_first_pass/` 是当前 50-clip 三方法主实验 first-pass 的提交汇总。
- `../archive/paper_results/2026-07-14-first-pass/results/full_ablation_first_pass/` 是当前 50-clip 消融 first-pass 的提交汇总。
- `../archive/paper_results/2026-07-14-first-pass/results/ablation/` 是早期四 clip 消融 pilot 结果。
- `../archive/paper_results/2026-07-14-first-pass/evidence/` 是已保留的实验记录。
- 当前工作树有 50 个本地 active mp4 clip，五类各 10 个；每个 active clip 都有同名角点 CSV。
- Proposal 中的 50 个视频和完整五类 benchmark 已具备本地数据、标注和 first-pass 结果；正式结论仍需人工审核、修复或解释跳过指标，并完成论文图表/正文回填。
- 原 mock 稿件和 mock 图表已从当前分支移除，不得将模拟数字用于论文结论。
