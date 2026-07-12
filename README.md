# screen-normalize

面向真实手持拍屏视频的屏幕透视归一化与时域稳定化课程项目。

当前工作以最终论文结果为目标：采集五类视频并标注关键帧四角，运行三种方法，计算几何、时域、细节和频域四类指标，为每个视频生成 HTML 审核报告，最后从选定 run 汇总论文图表。

实验产物规格见 [`doc/paper/plan/experiment_pipeline.md`](doc/paper/plan/experiment_pipeline.md)，代码开发顺序见 [`doc/paper/plan/code_implementation.md`](doc/paper/plan/code_implementation.md)，论文目标见 [`doc/paper/outline_zh.md`](doc/paper/outline_zh.md)。

## 当前入口

项目使用 `uv` 管理 Python 环境，依赖固定在 `pyproject.toml` 和 `uv.lock`。

```bash
uv run scripts/normalize_screen.py --help
uv run scripts/select_corners.py inputs/static/static_01.mp4
uv run scripts/annotate_corners.py inputs/static/static_01.mp4 --stride 30
```

- `scripts/normalize_screen.py`：当前屏幕归一化算法入口。
- `scripts/select_corners.py`：单帧四角点选取和算法调试工具。
- `scripts/annotate_corners.py`：正式多关键帧角点 CSV 标注工具。
- `screen_normalize/algorithms/`：检测、跟踪、轨迹平滑、对齐、变换和编码。
- `screen_normalize/experiments/`：标注、方法 runner、run 读写、单视频 pipeline、报告和论文绘图样式。
- `screen_normalize/metrics/`：Geometry、Temporal、Detail 和 Frequency 四类论文指标。
- `screen_normalize/` 根层只保留公共参数、CLI 和通用工具；历史演示支持代码集中在 `archive/`。
- `scripts/archive/`：新流水线前的诊断和实验入口，仅供追溯。

## 实验运行

单视频闭环：

```bash
uv run scripts/analyze_video.py inputs/static/static_01.mp4 \
  --methods frame_wise optical_flow proposed \
  --metrics geometry temporal detail frequency
```

批量运行五类数据：

```bash
uv run scripts/run_batch.py --input inputs \
  --methods frame_wise optical_flow proposed \
  --metrics geometry temporal detail frequency
```

也可以用 `--videos`、`--categories` 和 `--limit` 固定子集。对已有 run 使用
`--run-dir ... --reuse-outputs` 可只重算指标，`--skip-existing` 会保留已有指标。

生成论文表格和图：

```bash
uv run scripts/make_paper_results.py runs/20260712-153000_analysis
```

四个 `scripts/evaluate_*.py` 是单 clip/method 执行器，不遍历数据，也不创建 run。
`analyze_video.py` 单独运行时创建一个 run；`run_batch.py` 为整批创建唯一 run。

## Run 产物

每个方法目录包含 `normalized.mp4`、`estimated_corners.csv`、`debug.csv`、
`method.json`、所选指标的 JSON/帧级 CSV 以及审核图片。每个 clip 有 `report.html`
和 `notes.md`，run 根目录有批处理 `index.html`。`make_paper_results.py` 只读取 run，
在 `summary/` 生成表格、图和汇总报告。

代码测试与本机 pilot smoke run 已验证完整调用链。正式实验完成仍需要在五类目录放入
各 10 个视频、完成角点标注并运行 5-clip smoke batch 和正式 batch；pilot archive 不作为论文结果。

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
├── screen_normalize/    # algorithms、experiments、metrics 与公共入口
└── scripts/             # 当前入口及 archived 旧入口
```

- `doc/paper/source/proposal.pdf`：正式 proposal。
- `doc/paper/outline_zh.md`：结果导向的最终论文大纲。
- `doc/paper/implementation_roadmap.md`：从结果反推的实现路线。
- `doc/paper/plan/experiment_pipeline.md`：当前唯一实验流水线计划。
- `doc/paper/plan/code_implementation.md`：从现有代码到完整实验工具链的实施计划。
- `doc/paper/references/samples/`：教师论文和课程 final report 示例。
- `doc/archive/`：过期计划、旧稿和开发记录。
