# 论文实验流水线实施计划

## 1. 目标

建立一条面向最终论文的轻量实验流程：

```text
数据采集与角点标注
  -> 单视频方法运行
  -> 四类指标计算
  -> 单视频 HTML 审核
  -> 批量运行
  -> 从 runs 汇总结果并绘图
  -> 撰写论文
```

这套流程优先服务算法开发、实验审核和论文结果，不建设通用实验平台，不引入文件 hash、数据库或复杂任务状态系统。

本文件定义实验流程和产物；具体代码模块、现有实现缺口和开发顺序见 `code_implementation.md`。

## 2. 核心原则

1. `inputs/` 只保存原始视频和人工角点标注。
2. 人工标注只有屏幕四角，不增加 ROI 标注。
3. 所有方法输出、指标、图片和 HTML 都写入单个时间命名的 run。
4. 一次顶层命令只创建一个 run 根目录。
5. 四个指标脚本只处理一个 clip/method，不包含批处理逻辑。
6. `analyze_video.py` 负责单视频闭环，`run_batch.py` 独占所有遍历、筛选和批处理逻辑。
7. 后续表格和论文图只读取 `runs/`，不再读取或改动 `inputs/`。

## 3. 数据组织

### 3.1 五类视频

`inputs/` 按 proposal 中的五类场景组织，每类 10 个视频：

```text
inputs/
├── static/
├── scrolling/
├── screen_video/
├── weak_border/
└── hard/
```

文件名使用类别加两位序号：

```text
static_01.mp4
static_02.mp4
scrolling_01.mp4
screen_video_01.mp4
weak_border_01.mp4
hard_01.mp4
```

文件名即 clip ID，在标注、run、指标和论文图表中保持一致。

### 3.2 角点标注

每个视频可以有一个同名 CSV：

```text
inputs/static/static_01.mp4
inputs/static/static_01.csv
```

CSV 只保存选定关键帧的四角坐标：

```csv
frame,tl_x,tl_y,tr_x,tr_y,br_x,br_y,bl_x,bl_y
0,312,184,1610,205,1654,927,275,914
30,310,183,1612,204,1655,928,274,915
60,308,182,1613,203,1657,929,272,916
```

角点顺序固定为 TL、TR、BR、BL。没有标注的帧不出现在 CSV 中。

### 3.3 不使用人工 ROI

Detail 和 FFT 不需要额外人工 ROI：

- 根据人工角点或方法估计角点将屏幕归一化到固定屏幕坐标系。
- 自动排除归一化画面边缘，例如四周各 10%。
- Detail 在剩余有效屏幕区域中统一计算。
- FFT 在有效屏幕区域或自动检测的高频区域计算。

这样人工工作只集中在四角标注。

## 4. Run 结构

### 4.1 命名

一次运行在 `runs/` 下只创建一个时间命名目录：

```text
runs/20260712-153000_analysis/
```

时间目录创建功能封装在公共模块中。`analyze_video.py` 被单独调用时可创建 run；`run_batch.py` 创建整批唯一的 run 并传入每个单视频任务。四个指标脚本始终接收已有输出目录，不创建时间 run。

### 4.2 单视频目录

```text
runs/20260712-153000_analysis/
├── index.html
├── static/
│   └── static_01/
│       ├── frame_wise/
│       │   ├── normalized.mp4
│       │   ├── estimated_corners.csv
│       │   ├── geometry.json
│       │   ├── temporal.json
│       │   ├── detail.json
│       │   ├── frequency.json
│       │   └── debug.csv
│       ├── optical_flow/
│       ├── proposed/
│       ├── keyframes/
│       ├── report.html
│       └── notes.md
├── scrolling/
├── screen_video/
├── weak_border/
└── hard/
```

原视频不复制到 run。`report.html` 通过相对路径引用原视频，并展示 run 内的 normalized 视频和图片。`notes.md` 用于人工记录审核结论，不需要独立审核系统。

## 5. 四类指标脚本

四个脚本都是单元执行器：一次只计算一个 clip 的一个 method 输出。它们不搜索 `inputs/`、不遍历类别、不选择方法，也不创建时间 run。

### 5.1 Geometry

```text
scripts/evaluate_geometry.py
```

输入人工角点与方法估计角点，输出：

- corner error；
- quadrilateral IoU；
- aspect-ratio error；
- 按帧指标 CSV 与汇总 JSON；
- 人工/预测角点叠加图。

没有角点 CSV 时该指标标记为 skipped。

### 5.2 Temporal

```text
scripts/evaluate_temporal.py
```

输出：

- 相邻帧 residual translation；
- residual rotation；
- residual scale variation；
- 帧级时间序列 CSV；
- 汇总统计 JSON；
- 时间曲线。

动态屏幕内容场景需在屏幕固定结构或标注几何上评估，避免将滚动和播放内容误解为相机抖动。

### 5.3 Detail

```text
scripts/evaluate_detail.py
```

在自动裁掉边缘的归一化屏幕区域输出：

- average gradient magnitude；
- edge preservation index；
- 采样帧级 CSV；
- 汇总 JSON；
- 自动选取的示例区域图。

### 5.4 Frequency

```text
scripts/evaluate_frequency.py
```

输出：

- 2D FFT 频谱；
- 水平与垂直主方向；
- orthogonality error；
- 采样帧级 CSV；
- 汇总 JSON；
- 代表帧频谱图。

FFT 是几何归一化后的频域诊断，用于描述方向规则性及重采样前后的高频变化，不宣称系统直接完成去摩尔纹。

## 6. 单视频分析脚本

```text
scripts/analyze_video.py
```

它负责一个视频的完整闭环：

1. 顶层单独调用时创建唯一的时间 run；被 `run_batch.py` 调用时接收已有 run。
2. 对该视频运行指定的 frame-wise、optical-flow 或 proposed method。
3. 每个方法的 normalization 只执行一次。
4. 将同一份方法输出交给四个指标模块。
5. 为该视频生成 `report.html`。

单视频调用示例：

```bash
uv run scripts/analyze_video.py \
  inputs/static/static_01.mp4 \
  --methods frame-wise optical-flow proposed \
  --metrics geometry temporal detail frequency
```

## 7. 独立批处理脚本

```text
scripts/run_batch.py
```

`run_batch.py` 是所有批处理的唯一入口，负责：

1. 创建整批唯一的时间 run。
2. 根据文件、目录、类别、数量或子集选择 clip。
3. 根据 `--methods` 选择需要运行的方法。
4. 根据 `--metrics` 选择需要计算的指标。
5. 为每个 clip 调用单视频分析能力。
6. 单个 clip 失败时记录错误并继续。
7. 为整个 run 生成 `index.html`。

按类别运行示例：

```bash
uv run scripts/run_batch.py \
  --input inputs/ \
  --categories static scrolling \
  --methods frame-wise optical-flow proposed \
  --metrics geometry temporal
```

指定视频运行示例：

```bash
uv run scripts/run_batch.py \
  --videos inputs/static/static_01.mp4 inputs/hard/hard_03.mp4 \
  --methods proposed \
  --metrics temporal frequency
```

复用已有方法产物、只重算 hard 类的 FFT：

```bash
uv run scripts/run_batch.py \
  --run-dir runs/20260712-153000_analysis \
  --categories hard \
  --metrics frequency \
  --reuse-outputs
```

批处理选择参数集中在该脚本：`--input`、`--videos`、`--categories`、`--methods`、`--metrics`、`--limit`、`--run-dir`、`--reuse-outputs` 和 `--skip-existing`。

## 8. 公共封装

下列运行目录能力不在脚本中重复实现：

```text
screen_normalize/experiments/run_io.py
```

### `run_io.py`

- 创建 `YYYYMMDD-HHMMSS_<name>` 格式的 run 目录；
- 接收已有 `run_dir`；
- 建立类别、clip 和 method 子目录；
- 读写 JSON/CSV；
- 统一文件名。

## 9. HTML 审核报告

每个 clip 的 `report.html` 至少包含：

1. clip ID 和类别；
2. 原视频；
3. 三种方法的 normalized 视频；
4. 人工角点与预测角点的关键帧叠加图；
5. 三种方法的主指标对比表；
6. translation、rotation 和 scale 时间曲线；
7. detail 示例与 FFT 频谱；
8. tracker rejection、inlier 和处理失败摘要；
9. skipped 指标的原因。

Run 根目录的 `index.html` 列出所有 clip，显示类别、成功/失败状态和报告链接，用于按视频快速审核。

## 10. 全量与部分实验

`run_batch.py` 支持全量和子集，但子集应在正式运行前确定。指标脚本本身不感知子集。

| 结果 | 运行范围 |
| --- | --- |
| 数据集构成 | 五类各 10 个视频，并展示每类代表帧 |
| 主方法成功率 | 全部 50 个视频 |
| 三方法主对比 | 原则上全部视频 |
| Geometry | 所有具有人工角点的关键帧 |
| Temporal | 全部视频 |
| Detail | 全部视频或预先确定的纹理子集 |
| Frequency | hard/moiré/grid 子集 |
| 模块消融 | 每类预先固定若干 clip，或时间允许时全量 |
| 定性图 | 每类预先确定的代表 clip |
| 失败案例 | 审核中确认的真实失败 clip |

可选子集可用一个简单 YAML 定义，但不强制建立复杂配置系统。

## 11. 后续汇总、绘图与论文

正式实验 run 经人工审核后，再运行后续脚本：

```text
scripts/paper/make_paper_results.py
```

该脚本只读取指定 run：

```bash
uv run scripts/paper/make_paper_results.py \
  runs/20260712-153000_analysis/
```

输出：

```text
runs/20260712-153000_analysis/summary/
├── all_metrics.csv
├── geometry_table.csv
├── temporal_table.csv
├── detail_table.csv
├── frequency_table.csv
├── ablation_table.csv
├── figures/
└── report.html
```

论文的所有数字和图表从该 `summary/` 获取。绘图和写作阶段不重新处理原视频，也不改动 `inputs/`。

## 12. 实施顺序

### 阶段 A：数据和标注协议

1. 建立五个类别目录和命名规则。
2. 定义同名角点 CSV 格式。
3. 调整 `.gitignore`，只忽略视频，允许提交标注 CSV。
4. 使用现有角点 GUI 完成一个视频的标注往返验证。

### 阶段 B：单视频闭环

1. 实现 run 目录封装。
2. 实现四类指标的单视频调用。
3. 实现 `analyze_video.py` 的单视频闭环。
4. 生成一个静态视频的完整 `report.html`。
5. 再用滚动页面和屏幕内视频验证动态内容处理。

### 阶段 C：批处理

1. 实现独立 `run_batch.py`。
2. 在 `run_batch.py` 中集中实现五类目录遍历和指定文件选择。
3. 支持方法、指标、类别、子集、数量、reuse-outputs 和 skip-existing 筛选。
4. 使用小批量验证 run 结构和 HTML 索引。
5. 运行并审核全部 50 个视频。

### 阶段 D：论文结果

1. 选定一个完整、已审核的正式 run。
2. 汇总全量、分类别、分方法和消融结果。
3. 生成 `figure_plan.md` 要求的图表。
4. 根据真实结果替换全部 `TBD-*` 槽位。
5. 先完成 Results 图表、caption 和结论，再撰写 Abstract 和 Discussion。

## 13. 最小验收条件

单视频流程完成的标准：

1. 一条命令只创建一个 run 目录。
2. run 中同时包含三种方法的视频产物。
3. 有角点标注时 geometry 指标正常生成。
4. 四类指标均生成 JSON/CSV，不适用时明确标记 skipped。
5. `report.html` 可直接比较原视频与三种方法。
6. 重跑单个指标时可复用已有方法产物。

批量流程完成的标准：

1. 可以对五个类别或指定子集运行。
2. 单个 clip 失败不阻断其他 clip。
3. `index.html` 可导航到每个 clip 报告。
4. 后续绘图脚本仅依赖选定 run 中的结果。
