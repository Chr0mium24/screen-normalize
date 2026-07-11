# Paper Workspace

本目录是当前论文的唯一工作区。

## 目录

| 路径 | 用途 |
| --- | --- |
| `source/proposal.pdf` | 已提交的正式 proposal，用于约束论文范围 |
| `outline_zh.md` | 最终论文的章节、论点和验收规格 |
| `figure_plan.md` | 7–9 个主图、表格、数据来源和结果槽位 |
| `implementation_roadmap.md` | 从最终结果反推数据、开发、实验和写作任务 |
| `plan/experiment_pipeline.md` | 五类数据、角点标注、四类指标、HTML、批处理和绘图的完整实施规格 |
| `draft_materials/` | 已有写作素材，可吸收进 Introduction、Related Work 和图表说明 |
| `references/samples/` | 教师提供的写作与排版样例 |
| `references/papers/` | 项目正式参考的学术论文 |
| `evidence/` | 真实实验指标和可复现运行清单 |

`doc/archive/` 中的文档仅供追溯，不代表当前论文计划或当前实验事实。

## 证据边界

- `evidence/experiment_summary.csv` 是已测量的时域稳定性结果。
- `evidence/run_manifest.md` 记录这些数字的执行命令和 run 名。
- `evidence/retained_runs.md` 记录本机 `runs/` 中保留的最小证据集。
- Proposal 中的 50 个视频、人工角点标注、几何精度、细节保持和 FFT 指标仍需用真实实验完成。
- 原 mock 稿件和 mock 图表已从当前分支移除，不得将模拟数字用于论文结论。
