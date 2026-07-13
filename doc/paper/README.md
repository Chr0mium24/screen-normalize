# Paper Workspace

本目录是当前论文的唯一工作区。

## 目录

| 路径 | 用途 |
| --- | --- |
| `current_status.md` | 当前事实、证据边界、完成项和下一步缺口的唯一入口 |
| `source/proposal.pdf` | 已提交的正式 proposal，用于约束论文范围 |
| `outline_zh.md` | 最终论文的章节、论点和验收规格 |
| `figure_plan.md` | 7–9 个主图、表格、数据来源和结果槽位 |
| `visual_style.md` | 论文图表和视觉风格约束 |
| `data_renaming_manifest.csv` | 数据命名、代表 clip 和归档路径记录 |
| `results/ablation/` | 旧四 clip 消融实验的 CSV/JSON 汇总结果 |
| `results/full_pipeline_first_pass/` | 50-clip 三方法主实验 first-pass 汇总结果 |
| `results/full_ablation_first_pass/` | 50-clip 三消融方法 first-pass 汇总结果 |
| `manuscript/` | 中英文论文正文 Markdown 和样式文件 |
| `references/samples/` | 教师提供的写作与排版样例 |
| `references/papers/` | 项目正式参考的学术论文 |
| `evidence/` | 真实实验指标和可复现运行清单 |

`doc/archive/` 中的文档仅供追溯，不代表当前论文计划或当前实验事实。最近一次清理归档位于 `doc/archive/paper_workspace_cleanup_2026-07-14/`。

## 证据边界

- `current_status.md` 是当前论文状态的权威摘要。
- `results/full_pipeline_first_pass/` 是当前 50-clip 三方法主实验 first-pass 的提交汇总。
- `results/full_ablation_first_pass/` 是当前 50-clip 消融 first-pass 的提交汇总。
- `results/ablation/*.csv` 和 `results/ablation/*.json` 是早期四 clip 消融 pilot 结果。
- `evidence/experiment_summary.csv`、`evidence/run_manifest.md`、`evidence/retained_runs.md` 是已保留的实验记录。
- 当前工作树有 50 个本地 active mp4 clip，五类各 10 个；每个 active clip 都有同名角点 CSV。
- Proposal 中的 50 个视频和完整五类 benchmark 已具备本地数据、标注和 first-pass 结果；正式结论仍需人工审核、修复或解释跳过指标，并完成论文图表/正文回填。
- 原 mock 稿件和 mock 图表已从当前分支移除，不得将模拟数字用于论文结论。
