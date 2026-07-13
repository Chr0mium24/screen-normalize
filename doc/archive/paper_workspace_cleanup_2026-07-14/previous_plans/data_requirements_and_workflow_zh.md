# 论文阶段性数据要求与完整执行流程

> 更新日期：2026-07-13  
> 依据：`outline_zh.md`、`figure_plan.md`、`implementation_roadmap.md`、`plan/experiment_pipeline.md`、当前 `inputs/`、`runs/`、代码与测试状态。  
> 用途：作为数据采集、标注、正式实验、结果汇总和论文回填的统一执行文档。

## 技术结论

当前阶段不再以“50 个独立视频、每类 10 个”为完成条件。正式评估范围固定为 **static、scrolling、screen_video、hard 四类**；`weak_border` 已备份归档并从当前实验与报告验收中排除。四个纳入类别各保留 1 个已有标注/报告的代表视频。

数据采集现在按用户确认视为 **完成**。`inputs/` 中 active 数据集只保留 `static_02`、`scrolling_03`、`screen_video_03` 和 `hard_01` 四个已有标注/报告的代表源视频；7 个未标注源视频及其分段已备份到 `inputs/archive/removed_unannotated_2026-07-14/`，不进入当前实验分母。历史 run 目录作为证据保留旧名称。

按当前四类口径，代表结果已经 **4/4 完成**：static、scrolling、screen_video、hard 均有 3/3 方法、12/12 指标 JSON 且状态为 `ok`。数据收集、标注和主方法输出不再重跑；下一阶段直接进入消融实验，最终 HTML 通过映射表显示新 clip ID。

当前 `proposed` 是 reference-anchored LK + RANSAC + 几何门控 + 轨迹修复/平滑 + residual alignment；它没有实现 proposal 中单独的“边框运动 vs. 内部内容运动”一致性模块。为避免重新设计主方法和重跑已有结果，当前消融采用与代码一致的路线：分别关闭 reliability gates、trajectory smoothing 和 offline trajectory repair，并同步修订论文中的模块名称。

## 当前类别 HTML 覆盖清单

- [x] **static**：`static_02_000` 对应的历史 run 已有完整 HTML；3/3 方法、12/12 指标均为 `ok`。
- [x] **scrolling**：`scrolling_03_000` 对应的历史 run 已有完整 HTML；3/3 方法、12/12 指标均为 `ok`。
- [x] **screen_video**：`screen_video_03_000` 对应的历史 run 已有完整 HTML；3/3 方法、12/12 指标均为 `ok`。
- [x] **weak_border**：数据已收集；按当前决定从实验和报告验收中排除。
- [x] **hard**：`hard_01` 对应的历史 run 已有完整 HTML；3/3 方法、12/12 指标均为 `ok`。
- [x] **阶段性数据集规模完成：四个纳入类别均有完整 HTML 报告。** 当前进度：4/4。

## 一、当前资产与论文要求的差距

| 项目 | 论文验收要求 | 当前状态 | 仍需补充 | 优先级 |
| --- | --- | --- | --- | --- |
| 数据集规模 | 当前阶段：四个纳入类别各至少 1 个完整 HTML 报告 | 4/4 类完成；weak_border 排除 | 无数据规模缺口 | 完成 |
| 数据组织 | active 数据只保留已有标注/报告的代表 clip；未标注数据归档 | 4 个 active 代表源视频；7 个未标注源视频及其分段已备份 | 无 | 完成 |
| 几何真值 | 当前四个代表 clip 的选定关键帧具有 TL/TR/BR/BL | 四类代表标注已存在 | 不重标；直接复用现有 CSV | 完成 |
| 标注质量 | 当前消融使用与主实验相同的固定标注 | 现有标注可供同输入配对比较 | 本阶段不新增复标；复标属于后续扩展 | 完成 |
| Proposed 方法证据 | 消融名称与当前真实模块一一对应 | reliability gates、trajectory smoothing、offline trajectory repair 已存在，但缺独立关闭配置 | 增加三个独立配置与隔离测试 | P0 |
| 三方法主实验 | 四个纳入类别的代表 clip 均运行 frame-wise、optical flow、proposed | 四类历史代表报告已完成 | 不重跑；最终 HTML 使用新旧 ID 映射 | 完成 |
| 几何指标 | corner error、quad IoU、aspect-ratio error | 指标代码存在，正式全量结果缺失 | 对全部 250 个建议标注帧做配对评估，按类别和总体汇总 | P1 |
| 独立时域指标 | translation、rotation、scale，且不受动态内容污染 | 旧 summary 是少量 pilot 的估计轨迹诊断，不是独立正式证据 | 固定独立定义；建议增加连续标注/物理边框复核子集，见下文 | P0 |
| 细节保持 | gradient magnitude、edge preservation | 代码存在；正式对齐参考和全量结果缺失 | 用人工角点生成 GT-rectified reference，再与三方法同尺度对齐比较 | P1 |
| 频域诊断 | FFT 主方向、正交误差、高频能量变化 | 有 pilot 诊断；正式预注册子集和结果缺失 | 在看主结果前固定 hard/grid/moiré 子集与帧，保留诊断性表述 | P1 |
| 消融 | full、w/o reliability gates、w/o trajectory smoothing、w/o offline trajectory repair | full 已有；三个去模块变体尚无独立可执行配置 | 增加开关并只运行三个新增变体 | P0 |
| 定性图与失败案例 | 五类对比图、时间曲线、至少有解释的真实失败 | 仍为占位图；有零散诊断 run | 预先固定 5 个代表 clip；正式审核后固定至少 3 个真实失败案例 | P1 |
| 运行与复现 | 参数、版本、硬件、耗时、commit、成功判据 | method JSON 和 run 结构已具备部分能力 | 记录正式环境、处理边界、Git commit、每 clip 状态与失败原因 | P1 |
| 统计报告 | 配对比较、样本数、不确定性、分类结果 | 尚无正式统计 | 保存逐帧和逐 clip 数据；按分布选择均值±SD或中位数[IQR]，报告配对 CI | P1 |

## 数据重命名与整理结果

- [x] 4 个 active 代表源视频采用 `category_NN` 命名。
- [x] 7 个未标注源视频及其分段已备份到 `inputs/archive/removed_unannotated_2026-07-14/`。
- [x] 所有已有分段目录改为对应 clip ID。
- [x] 分段 MP4 与角点 CSV 使用与分段目录一致的名称。
- [x] `hard/moire/` 中的正式数据移到 `inputs/hard/hard_01.*`。
- [x] 建立旧名称到新名称的 CSV 映射表。
- [x] 修复历史 HTML 中的输入路径；17/17 个引用均存在。
- [x] `premodify/` 保留为未归档原始素材，不混入正式 `inputs/` clip ID。

完整映射见 `doc/paper/data_renaming_manifest.csv`。

说明：现有 `doc/paper/evidence/experiment_summary.csv` 只能作为软件路径和 pilot 现象的证据，不能直接填入正式主表。它只覆盖少量旧视频，且时域数值来自估计轨迹，未满足最终论文要求的独立验证口径。

## 二、需要新增或冻结的数据

### 2.1 当前阶段的视频与报告覆盖

当前阶段的目标不是视频总数，而是**类别覆盖**：每类至少 1 个可审核的完整 HTML 报告。

| 类别 | 可用代表视频 | 完整报告目标 | 当前状态 | 还差什么 |
| --- | --- | ---: | --- | --- |
| static | `static_02_000.mp4` | 1 | [x] 完成 | 无 |
| scrolling | `scrolling_03_000.mp4` | 1 | [x] 完成 | 无 |
| screen_video | `screen_video_03_000.mp4` | 1 | [x] 完成 | 无 |
| weak_border | `archive/removed_unannotated_2026-07-14/weak_border/weak_border_01.mp4` | 排除 | [x] 已备份 | 当前实验不使用 |
| hard | `hard_01.mp4` | 1 | [x] 完成 | 无 |
| **合计** | **五类均已有视频** | **4 个纳入类别** | **4/4** | **无数据缺口** |

因此当前“数据集规模”已完成。原大纲的 50 个视频目标保留为后续扩展；weak_border 也保留在 `inputs/`，但不进入当前汇总、图表和论文结果分母。

### 2.2 稀疏几何标注数据

当前阶段不再新增人工标注。四个纳入类别已有代表标注；weak_border 被排除。若后续重新纳入 weak_border，建议标注 5 帧，取 `0%、25%、50%、75%、100%` 附近的可解码帧。可选新增标注量为：

- 1 clip × 5 帧 = **5 个标注关键帧**；
- 每帧 4 个角点 = **20 个二维点**；
- 每个标注 CSV 固定列：`frame, tl_x, tl_y, tr_x, tr_y, br_x, br_y, bl_x, bl_y`；
- 角点顺序固定 TL → TR → BR → BL；坐标必须在帧内、四边形凸且非退化。

阶段性验收先要求在 HTML 中人工检查 5 帧角点叠加是否正确。跨标注者一致性和 250 帧全量标注属于后续 50-video 扩展阶段。

### 2.3 独立时域验证数据

仅使用某方法自己的平滑轨迹计算“稳定性”，会把估计器的平滑直接当作成功证据。正式时域主结论需要外部或人工几何参照。推荐采用两层设计：

1. **全量诊断层：** 50 个 clip 全帧保存三种方法的 estimated corners/homography、translation、rotation、scale、接受/拒绝状态；用于成功率、曲线和故障定位。
2. **独立验证层：** 每类预先选 2 个 clip，共 10 个；每个 clip 标注连续 1 秒（按 30 帧计约 30 帧）的四角或固定物理边框点，共约 **300 个连续标注帧**。所有方法都对同一连续帧计算输出中的残余边框运动。

若 300 帧人工连续标注成本过高，可以用经过人工抽查的独立边框检测器产生连续参考，但该检测器不能与被评估方法共享同一平滑轨迹，并必须报告抽查误差。两种方案只能在正式运行前选定，不能看完结果后切换。

### 2.4 细节保持与频域数据

细节指标不需要新增人工 ROI，但需要统一参照：对每个稀疏标注帧，用人工角点生成 GT-rectified reference；三种方法输出按相同画布、尺寸和有效区域裁剪。然后计算平均梯度比例与 edge preservation index。建议正式主结果覆盖全部可用标注帧，同时预先固定 10–20 个文字/图表纹理丰富帧用于 Fig. 6 局部放大。

频域分析只做诊断。建议在正式结果产生前，从 hard 类及其他含规则网格/高频伪影的样本中固定 5–10 个 clip、每个 3–5 帧；保存原始 crop、GT-rectified、三方法 rectified、2D FFT、主方向、正交误差与高频能量比例。论文中不得把这些数据解释为去摩尔纹性能。

### 2.5 运行、失败和复现数据

每个方法运行至少保存：

- `normalized.mp4`、`estimated_corners.csv`、`debug.csv`、`method.json`；
- 处理帧数、墙钟时间、每帧或每 clip 成功状态；
- tracker inlier 数/比例、重投影误差、覆盖率、拒绝原因、冻结/重检测/插值次数；
- Git commit、Python/OpenCV/NumPy/FFmpeg 版本、CPU/GPU、操作系统；
- 明确的成功判据，例如“视频完整解码并输出、有效角点比例达到阈值、无非有限或退化四边形”。

失败案例不是从“最难看”的图中主观挑选，而应从预先定义的失败规则和人工审核记录中选出。至少固定 3 个代表性失败：弱/不可见边框、遮挡或快速运动、强高频/摩尔纹或眩光；每个案例同时保存输入、输出缺陷和对应 debug 证据。

## 三、正式实验前必须冻结的定义

### 3.1 方法定义决策

当前阶段采用路线 B，并将配置写入 `method.json` 和论文 Method：

- **路线 A：保持原大纲。** 实现物理边框逐帧主导、内部特征一致性检查、低置信重检测/冻结/修复，并提供 `disable_consistency`、`disable_recovery`、`disable_smoothing` 三个独立开关。
- **路线 B：保持当前代码。** 将 proposed 改写为 reference-anchored feature tracking with geometric reliability gates，删除“已实现 border-guided motion separation”的贡献表述，并把消融名称改成当前真正可关闭的模块。

**当前冻结路线 B。** 原因是数据、标注、主方法结果已经存在，当前目标是完成可复现的消融，而不是重做主方法。中英文稿、大纲、图注和结论必须同步改成当前真实模块名称。

### 3.2 指标与聚合定义

正式运行前应把以下内容写死并加入测试：

- corner error 是四角平均欧氏误差、RMSE，还是两者同时报告；像素是在原始分辨率还是归一化画布；
- quad IoU 的多边形实现、无效四边形处理；
- aspect-ratio reference 来自人工四角还是已知显示器比例；
- temporal translation/rotation/scale 如何从独立参考分解，单位与聚合层级；
- detail 的 reference、插值方式、有效区域裁剪比例；
- FFT 的频带范围、方向计算、能量归一化；
- 先逐 clip 汇总、再跨 clip 配对，避免长视频因帧数多而获得更大权重；
- 缺失、skipped、failed 不得被默认为 0，也不得只删除不报告。

### 3.3 子集与选图协议

在查看最终方法排名前固定：

- 10 个连续时域验证 clip；
- detail 局部放大帧；
- frequency 子集；
- 消融子集（若不做 50 clip 全量）；
- 五类定性代表 clip 及起始/中间/结束帧选择规则；
- 失败判据和人工审核表。

## 四、从数据到论文的完整流程

```text
当前阶段：四类正式 HTML 闭环
  [x] static 完整报告
  [x] scrolling 完整报告
  [x] screen_video 完整报告
  [x] weak_border：已收集，当前实验排除
  [x] hard 完整报告
      ↓
  [x] 四个纳入类别 4/4 验收完成
```

### 当前下一任务：完成消融实验

1. [x] 数据收集与重命名完成。
2. [x] static、scrolling、screen_video、hard 四类已有代表标注和历史完整报告。
3. [x] weak_border 明确排除，不进入当前实验分母。
4. [x] 将消融名称冻结为代码真实存在的模块：`full`、`w/o reliability gates`、`w/o trajectory smoothing`、`w/o offline trajectory repair`。
5. [x] 已增加三个独立方法配置，并用隔离测试确认每个变体只关闭目标模块。
6. [x] 已复用四类各一个代表视频和角点 CSV，完成 12/12 个新增消融任务；`full` 复用已有 proposed 输出并按当前代码重算指标，统一排除初始化帧。
7. [x] 已生成 `ablation_table.csv`、逐 clip 明细、质量检查和消融 HTML；[ ] 正式 Figure 7 仍待根据已审核数值替换占位图。

### 后续扩展阶段（不作为当前数据集规模门槛）

以下 50-video、复标和独立时域验证流程继续保留为扩展工作；当前先完成四类代表数据上的消融和论文回填。

### 后续阶段 0：冻结方法与实验契约

1. 按已冻结的路线 B 审计 current proposed 与论文 Method 的对应关系。
2. 固定 `frame_wise`、`optical_flow`、`proposed` 参数。
3. 固定四类指标公式、单位、输出字段和失败处理。
4. 固定稀疏标注、连续时域标注、复标和子集规则。
5. 给每个 Figure/Table 字段建立 `TBD → CSV/JSON 字段` 映射。

**退出条件：** 同一输入和参数必然产生结构一致的输出；Figure 7 的每个消融名称都有可执行开关。

### 后续阶段 1：整理和补采数据

1. 对 `inputs/` 与 `premodify/` 按内容和文件指纹去重。
2. 将有效候选归入五类；`hard/moire/` 应整理为流水线可识别的 hard clip 路径，或明确支持二级子目录。
3. 检查每个候选是否约 5 秒、屏幕可见、可解码、不是同一长视频的重复切片。
4. 优先补 weak_border 和 hard 各 9 个，再补其余类别各 7 个。
5. 统一命名为 `static_01`…`hard_10`，保留旧名到新 ID 的一次性映射表作为工作记录。

**退出条件：** 五类各 10 个，共 50 个独立可解码 clip；每个只属于一个类别。

### 后续阶段 2：标注和质控

1. 自动生成每个 clip 的 5 个稀疏帧号。
2. 用 Web/GUI 工具标 TL/TR/BR/BL；保存同名 CSV。
3. 运行坐标范围、凸性、面积、角点顺序和帧号校验。
4. 完成 25 帧分层复标并裁决。
5. 完成 10 个预定 clip 的连续 1 秒时域标注，或验证独立边框参考方案。
6. 生成 Fig. 2 所需五类代表帧和标注叠加预览。

**退出条件：** 正式稀疏标注无缺失；复标结论和最终真值可追溯；时域主指标有独立参考。

### 后续阶段 3：小规模端到端验证

1. 每类选 1 个 clip，运行 5-clip smoke batch。
2. 每个 clip 同时运行三方法和四指标。
3. 检查 normalized 视频、角点轨迹、JSON/CSV、曲线和 `report.html`。
4. 检查动态内容没有被时域指标误当作相机运动。
5. 对合成变换/自一致样例验证指标方向和单位。

**退出条件：** 任一 clip 失败不会中断 batch；所有 skipped 都有原因；汇总脚本不再读取原视频。

### 后续阶段 4：冻结正式运行

1. 固定 Git commit 和依赖版本。
2. 固定参数、画布、编码器、插值、随机种子（如适用）。
3. 固定所有子集、代表 clip 和失败判据。
4. 建立只读正式 run 目录命名和运行清单。

**退出条件：** 此后不得根据最终排名改参数或换样例；如必须修改，创建新正式 run，并废弃旧 run 的论文资格。

### 后续阶段 5：主实验、消融和审核

1. 三方法主实验：50 clip × 3 = 150 个方法任务。
2. 三个去模块变体：50 clip × 3 = 150 个额外任务；完整方法直接复用主实验 proposed 输出。
3. 四类指标都从同一方法产物计算，不重复归一化。
4. 人工打开每个 clip 报告，记录输出缺陷、失败原因和是否可纳入对应指标。
5. 不允许用失败 clip 的缺失值替代为 0；按成功率和有效配对样本数显式报告。

**退出条件：** 一个完整 reviewed formal run 覆盖全部 50 clip；每个任务状态明确；消融与主结果可复现。

### 后续阶段 6：汇总、统计和图表

1. 先按帧计算，再按 clip 聚合，最后按类别和全数据集聚合。
2. 三方法使用同一 clip/帧做配对比较，并报告有效配对数。
3. 检查分布后选择均值±SD或中位数[IQR]；改进量报告配对置信区间。
4. 生成 geometry、temporal、detail、frequency、ablation 表和逐 clip 附表。
5. 生成 Fig. 1–8；禁止使用占位 SVG 或模拟数值。
6. 每个图表记录源 run、源 CSV/JSON、生成命令和 commit。

**退出条件：** 任意论文数字可回溯到正式 run 的一个字段；图、表、正文中的相同数字完全一致。

### 后续阶段 7：论文回填与最终 QA

1. 先完成 Results 图表、caption 和逐项结论。
2. 再根据真实结果写 Abstract、Discussion、Limitations 和 Conclusion。
3. 同步更新中英文稿，删除全部 `[TBD-*]` 和占位图。
4. 明确“描述性/诊断性”与“改进/因果性”结论边界。
5. 补 Data Availability、Code Availability、Author Contributions。
6. 运行最终 PDF 构建，检查页码、引用、图注、字体和中英文数字一致性。

## 五、数据到论文图表的映射

| 论文产物 | 必需数据 | 来源与生成时点 |
| --- | --- | --- |
| Fig. 1 Pipeline | 1 个预定 static clip 的 3–5 连续帧；检测线、角点、homography、warp、smooth 中间结果 | smoke test 后冻结代表 clip；正式 commit 重跑 |
| Fig. 2 Dataset | 四类各 1 个代表帧及四角叠加；weak_border 标注为排除 | 复用现有输入与标注 |
| Fig. 3 Geometry | 4 个代表 clip 的标注帧上三方法 corner error、IoU、aspect error | 当前四类代表实验；不得声称全数据集泛化 |
| Fig. 4 Temporal | 4 个代表 clip 的轨迹诊断与三方法曲线 | 当前阶段仅作诊断；独立时域验证留待扩展 |
| Fig. 5 Qualitative | 4 个预定代表 clip × 3 帧 × 输入/三方法 | 从现有 run 取图 |
| Fig. 6 Detail/FFT | GT-rectified reference、三方法同尺度 crop、detail 指标；预定高频子集的 FFT | 正式主实验 |
| Fig. 7 Ablation | full 与三个真实可执行去模块变体的配对指标 | 正式消融 run |
| Fig. 8 Failures | 至少 3 个符合预设失败判据的输入、缺陷、debug 证据 | 全量人工审核后 |
| Abstract/Results | 明确报告为四类代表 clip 的 pilot/coverage 结果，不写成 50-video benchmark | 四类 HTML 闭环并审核后 |
| Discussion | 最难类别、模块贡献、失败机制、数据规模与方法边界 | 基于正式结果与失败审计 |

## 六、建议的最小执行清单

### P0：当前数据与四类 HTML 闭环

- [x] 四类 active 代表视频数据均已保留；未标注视频已备份归档。
- [x] 将当前数据集规模目标改为“四个纳入类别各至少一个完整 HTML 报告”。
- [x] 审计现有报告的三方法、12 个指标 JSON 和状态。
- [x] static 至少 1 个完整 HTML 报告。
- [x] scrolling 至少 1 个完整 HTML 报告。
- [x] screen_video 至少 1 个完整 HTML 报告。
- [x] weak_border 已收集并明确排除，不要求完整 HTML。
- [x] hard 至少 1 个完整 HTML 报告。
- [x] 四个纳入类别均有历史完整报告；当前 4/4。

### P1：消融实验

- [x] 数据收集、标注和四类主方法结果已存在，不再重跑。
- [x] 固定 `static_02_000`、`scrolling_03_000`、`screen_video_03_000`、`hard_01` 为消融数据。
- [x] 增加 `no_reliability_gates`、`no_trajectory_smoothing`、`no_offline_repair` 三个独立配置。
- [x] 添加配置隔离测试，确认每个变体只关闭目标模块；当前全量测试为 22 passed。
- [x] 运行三个新增变体；完整方法复用已有 proposed 输出，当前 16/16 方法产物和 64/64 指标 JSON 完整。
- [x] 生成并审核消融表、tracker 接受率柱状图和 HTML；正式 Figure 7 占位图尚待替换。
- [x] 将消融 run 和旧主结果共同记录到 evidence manifest。

### P2：后续正式论文扩展

- [x] 冻结为 current reference-anchored 方法路线，不再补做 border-guided 主方法。
- [x] Figure 7 的三个消融名称已与真实可执行配置一一对应。
- [ ] 如恢复 50-video 目标，再进行补采、全量标注、复标和独立时域验证。
- [ ] 固定 commit、环境、参数、画布与编码配置。
- [ ] 生成 reviewed formal run 的 summary、图表和配对统计。
- [ ] 用真实数据替换 Fig. 1–8 和全部 `[TBD-*]`。

### P3：最终论文质量

- [ ] 补硬件、软件版本、运行时间、Code/Data Availability。
- [ ] 补至少 3 个有诊断证据的失败案例。
- [ ] 同步中英文稿、图注、表格、结论与引用。
- [ ] 构建并检查中英文 PDF；确认没有占位数、模拟图或越界的去摩尔纹结论。

## 下一步缺什么

按依赖顺序，当前缺口不是继续采集或重跑主实验，而是以下四项：

1. [x] **实现并冻结三个真实消融变体。** 使用 reliability gates、trajectory smoothing、offline trajectory repair 三个当前代码模块，不再使用尚未实现的 border/content consistency 名称。
2. [x] **运行消融实验。** 四类各一个 clip，12/12 个新增任务完成；full proposed 结果复用且指标口径已统一。
3. [x] **汇总消融与主结果。** 已生成 `ablation_table.csv`、逐 clip 表和消融 HTML，并使用新 ID；[ ] 正式 Figure 7 图像仍待替换。
4. [ ] **解决方法与论文表述并回填论文。** 将方法和消融名称同步到中英文稿，再替换 `[TBD-*]` 与占位图。

下一步先处理实验有效性问题：scrolling/full 几何失败、hard/full 长期冻结，以及 offline repair 在当前四个 clip 上没有可修复内部区间。然后再据此决定 Figure 7 是标注为描述性/inconclusive，还是更换一个能触发 repair 的现有代表 clip。

## 七、最终完成判据

当前阶段只有在以下条件同时满足时才视为“数据集规模完成”：

1. [x] 四个纳入类别的 active 代表视频都已存在；未标注视频已备份归档；
2. [x] static、scrolling、screen_video、hard 各有至少 1 个完整 HTML 报告；
3. [x] weak_border 明确排除，不进入当前实验分母；
4. [x] 四类历史代表报告均为 3/3 方法、12/12 指标 JSON 且状态为 `ok`；
5. [x] 消融实验和消融汇总已完成；[ ] Figure 7 正式图及论文回填尚未完成。

当前“数据集规模”已经打勾。50 个独立视频、weak_border 报告、复标和独立时域验证属于后续论文扩展，不阻塞当前阶段；当前实验执行的完成门槛是第 5 项消融实验。

## 八、证据来源与口径限制

- 论文规格：`doc/paper/outline_zh.md`、`doc/paper/figure_plan.md`、`doc/paper/implementation_roadmap.md`。
- 实验与目录契约：`doc/paper/plan/experiment_pipeline.md`、`doc/paper/plan/code_implementation.md`。
- 当前证据边界：`doc/paper/README.md`、`doc/paper/manuscript/00_scope.md`、`01_research_canon.md`、`02_evidence_table.md`。
- pilot 时域证据：`doc/paper/evidence/experiment_summary.csv`；仅用于验证软件路径与观察失败模式，不作为正式主结果。
- 当前资产盘点：2026-07-13 对 `inputs/`、`premodify/`、`runs/`、角点 CSV、方法配置与测试的本地只读审计。
