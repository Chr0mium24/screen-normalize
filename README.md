# screen-normalize

面向真实手持拍屏视频的屏幕透视归一化与时域稳定化课程项目。

当前工作以最终论文结果为目标：采集五类视频并标注关键帧四角，运行三种方法，计算几何、时域、细节和频域四类指标，为每个视频生成 HTML 审核报告，最后从选定 run 汇总论文图表。

完整实施规格见 [`doc/paper/plan/experiment_pipeline.md`](doc/paper/plan/experiment_pipeline.md)，论文目标见 [`doc/paper/outline_zh.md`](doc/paper/outline_zh.md)。

## 当前入口

项目使用 `uv` 管理 Python 依赖，脚本通过 PEP 723 声明运行环境。

```bash
uv run scripts/normalize_screen.py --help
uv run scripts/select_corners.py inputs/static/static_01.mp4
```

- `scripts/normalize_screen.py`：当前屏幕归一化算法入口。
- `scripts/select_corners.py`：当前单帧四角点选取工具。
- `screen_normalize/`：检测、跟踪、轨迹平滑、变换、编码和评估计算模块。
- `scripts/archive/`：新流水线前的诊断和实验入口，仅供追溯。

plan 中的四个独立指标脚本、`analyze_video.py`、`run_batch.py` 和 `make_paper_results.py` 尚待实现。

## 数据与结果

正式数据固定为五类，每类目标 10 个视频；视频文件不提交 Git，同名角点 CSV 可以提交：

```text
inputs/
├── static/
├── scrolling/
├── screen_video/
├── weak_border/
└── hard/
```

一次顶层运行只在 `runs/` 创建一个时间命名目录。后续论文汇总只读取选定 run，不重新读取或修改 `inputs/`。

旧的 6 个试拍视频保留在本机 `inputs/archive/pilot/`，旧实验结果保留在 `runs/archive/pre_pipeline/`。它们只作为开发历史，不属于正式数据集。

## 目录

```text
.
├── README.md
├── doc/                 # 当前论文工作区与历史文档
├── inputs/              # 正式视频分类、角点 CSV 和本机 pilot archive
├── runs/                # 新实验 run 和本机旧结果 archive
├── screen_normalize/    # 可复用 Python 实现
└── scripts/             # 当前入口及 archived 旧入口
```

- `doc/paper/source/proposal.pdf`：正式 proposal。
- `doc/paper/outline_zh.md`：结果导向的最终论文大纲。
- `doc/paper/implementation_roadmap.md`：从结果反推的实现路线。
- `doc/paper/plan/experiment_pipeline.md`：当前唯一实验流水线计划。
- `doc/paper/references/samples/`：教师论文和课程 final report 示例。
- `doc/archive/`：过期计划、旧稿和开发记录。
