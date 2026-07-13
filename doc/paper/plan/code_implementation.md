# 代码实施计划

## 1. 目标与边界

本文档说明如何从当前代码实现 `experiment_pipeline.md`。实验流水线文档负责定义数据、run 和论文产物；本文档负责定义代码模块、接口、开发顺序和测试。

代码只服务本项目的 50 个短视频实验，不建设通用任务平台。共享内容限于明确需要复用的配置、路径、指标计算和 HTML 渲染，不引入数据库、文件 hash、任务队列或插件系统。

## 2. 当前代码基线

当前可运行主链：

```text
scripts/normalize_screen.py
  -> screen_normalize/cli.py
  -> detection / tracking / trajectory
  -> alignment / warp / encoding
```

已有能力：

- `detect`、`flow`、`reference` 三种 tracker 模式；
- 屏幕检测、LK 跟踪、RANSAC、轨迹修复和平滑；
- 透视变换、可选 residual alignment、视频编码和 debug CSV；
- `screen_normalize/experiments/evaluation.py` 中已有几何、时域、细节和 FFT 的试验性计算。

当前缺口：

- 现有角点 GUI 不能完成多关键帧 CSV 的加载、修改和保存；
- 三种论文方法还没有稳定的程序化配置接口；
- proposed 与论文所述 border-guided method 的差距尚未逐项确认；
- 四类指标尚未拆成稳定的输入/输出契约；
- 没有单视频闭环、HTML 报告、批处理和论文汇总脚本。

## 3. 代码分层

### 3.1 算法层

保留现有 `screen_normalize/` 主链，先避免大规模重构。新增一个轻量程序化入口，例如：

```text
screen_normalize/experiments/runner.py
```

它接收输入视频、方法配置和已有输出目录，调用现有检测、跟踪、轨迹和编码模块。`scripts/normalize_screen.py` 继续作为人工调试 CLI，但 `analyze_video.py` 不通过拼接 shell 命令驱动算法。

三种方法使用固定 method ID：

| method ID | 当前映射 | 实施要求 |
| --- | --- | --- |
| `frame_wise` | `tracker=detect` | 每帧独立检测，不使用跨帧轨迹平滑 |
| `optical_flow` | `tracker=flow` | 只使用内容特征光流，不使用 proposed 的一致性和恢复模块 |
| `proposed` | `tracker=reference` 的当前实现 | 先作为基线，完成代码审计后补齐论文真正需要的 border guidance、consistency check 和 failure recovery |

每种方法必须输出同一组基础产物：

```text
normalized.mp4
estimated_corners.csv
debug.csv
method.json
```

`method.json` 只记录 method ID、参数和处理耗时，不记录 hash 或复杂环境快照。

### 3.2 标注层

新增：

```text
scripts/annotate_corners.py
screen_normalize/experiments/annotations.py
```

职责：

- 按固定间隔或指定帧号打开关键帧；
- 加载同名 CSV 并跳转到已有标注；
- 新增、修改、删除一帧的 TL/TR/BR/BL；
- 校验帧号、坐标范围、四边形顺序和非退化面积；
- 原子写回与视频同名的 CSV。

`select_corners.py` 保留为单帧调试工具，不承担正式数据集标注。

### 3.3 指标层

先将 `screen_normalize/experiments/evaluation.py` 中可复用代码拆到：

```text
screen_normalize/metrics/
├── geometry.py
├── temporal.py
├── detail.py
└── frequency.py
```

对应四个 `scripts/evaluate_*.py` 只负责参数解析和文件读写。`analyze_video.py` 直接调用 metrics Python API，不启动四个子进程。

开始实现前必须为每类指标写清：

1. 必需输入和允许缺失的输入；
2. 精确公式、单位和聚合方式；
3. 适用的视频或标注帧范围；
4. JSON 汇总字段和帧级 CSV 列；
5. `ok`、`skipped`、`failed` 的判定。

特别约束：

- Detail 只在可对齐到同一坐标系和尺度的帧上比较；
- Temporal 先解决动态内容污染，不能直接把全画面内容光流当作相机抖动；
- Frequency 只报告方向规则性和重采样前后的频谱变化，不输出 `moire_suppression` 指标。

### 3.4 Run 与报告层

新增：

```text
screen_normalize/experiments/run_io.py
screen_normalize/experiments/reporting.py
scripts/analyze_video.py
```

`run_io.py` 只负责时间目录、category/clip/method 路径和 JSON/CSV 读写。clip ID 和类别已体现在目录路径中，不再额外生成数据集 `metadata.json`。视频解码时仍可在内存中读取尺寸、FPS 和帧数，但它们只是处理视频所需的运行信息，不是需要整理的实验数据。

`analyze_video.py` 按以下顺序工作：

1. 解析一个视频及其同名角点 CSV；
2. 为选中的方法各运行一次 normalization；
3. 对同一方法产物调用选中的 metrics API；
4. 保存关键帧、曲线和指标文件；
5. 用 `reporting.py` 生成该 clip 的 `report.html`。

报告使用静态 HTML，不引入 Web 服务或前端构建系统。

### 3.5 批处理与汇总层

新增：

```text
scripts/run_batch.py
scripts/paper/make_paper_results.py
```

`run_batch.py` 是唯一遍历入口：选择视频、创建一个 run、逐个调用单视频 Python API、记录失败并生成 `index.html`。它不复制指标实现。

`make_paper_results.py` 只读取一个已完成 run 的结构化指标，生成 CSV、图和 summary HTML。类别和 clip ID 从 run 的目录结构获得，不生成或汇总视频属性元数据。

## 4. Proposed 方法开发

流水线外壳不能代替核心方法开发。对 proposed 按以下顺序补齐：

1. **现状审计：** 将 outline 中的 border guidance、consistency check、failure recovery 和 smoothing 映射到当前函数和参数，标出已完成、部分完成、未完成。
2. **固定基线：** 先冻结 `frame_wise` 和 `optical_flow` 的行为，避免 proposed 开发影响 baseline。
3. **边框证据：** 在现有检测结果中输出边线、交点和 border confidence，确认是否需要补 LSD/Hough 组合。
4. **一致性检查：** 明确边框运动与内部特征 homography 的一致性判据，并保存拒绝原因。
5. **失败恢复：** 对低置信帧定义重检测、冻结上一有效变换和轨迹插值的优先级。
6. **消融开关：** 为 consistency、recovery 和 smoothing 提供独立布尔开关，供 Figure 7 使用。

每完成一步，先在 `static`、`scrolling`、`screen_video` 各一个 pilot clip 上检查，再扩大范围。

## 5. 实施顺序

### 阶段 0：冻结契约

1. 完成 proposed 现状审计。
2. 固定三方法配置。
3. 固定四类指标公式和输出 schema。
4. 用一个小型手写 CSV 固定角点标注 schema。

### 阶段 1：标注与程序化算法入口

1. 实现 `annotations.py` 和 `annotate_corners.py`。
2. 实现 `runner.py`，让三方法写入已有 method 目录。
3. 在一个 pilot 视频上验证标注、运行和重新加载。

### 阶段 2：四类指标

1. 从 `evaluation.py` 迁移并修正 Geometry。
2. 解决动态内容口径后实现 Temporal。
3. 基于同坐标参考实现 Detail。
4. 实现不含去摩尔纹结论的 Frequency。
5. 为每类指标增加合成数据或自一致测试。

### 阶段 3：单视频闭环

1. 实现 `run_io.py`。
2. 实现 `analyze_video.py`。
3. 实现静态 HTML 报告。
4. 用静态、滚动和屏幕视频各一个 clip 验证。

### 阶段 4：批处理和论文汇总

1. 实现 `run_batch.py` 和根 `index.html`。
2. 先运行每类 1 个视频的 5-clip smoke batch。
3. 实现 `make_paper_results.py`。
4. 固定正式子集后运行全部主实验和消融。

## 6. 测试与完成条件

最低测试集：

- annotation CSV 读写、覆盖修改和非法四边形拒绝；
- run 路径创建和已有目录复用；
- 三方法配置不会互相串用参数；
- 四类指标在正常、缺输入和坏输入下分别返回 `ok`、`skipped`、`failed`；
- 单视频失败不会破坏同一 batch 的其他 clip；
- HTML 中引用的本地文件全部存在；
- summary 的每个论文数字能回到一个 JSON 字段或 CSV 列。

代码实施完成的判据不是“所有脚本存在”，而是一个 5-clip smoke run 能生成完整目录、可审核 HTML、结构化指标和论文汇总，并且不读取人工维护的额外元数据。
