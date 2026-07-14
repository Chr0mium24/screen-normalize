# Screen Normalize 汇报 - Design Spec

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | Screen Normalize：物理边框主导的屏幕归一化 |
| **Canvas Format** | PPT 16:9（1280×720） |
| **Page Count** | 13 |
| **Design Style** | Pyramid 结论先行 × Swiss Minimal 瑞士极简 |
| **Target Audience** | ECE4512 课程教师、助教与同学；具备计算机视觉基础 |
| **Use Case** | 课堂项目汇报，投影观看 |
| **Deck Language** | English for all visible slide copy and speaker notes |
| **Delivery Purpose** | presentation |
| **Content Strategy** | 保持当前汇报大纲的章节顺序与核心结论；压缩背景、算法细节和普通方法介绍，将主要篇幅用于当前管线、三方案定量比较、消融与失败分析；只使用仓库现有材料和数据 |
| **Presentation Duration** | 10–12 分钟 |
| **Created Date** | 2026-07-14 |

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280×720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | 左右 56，上 44，下 36 |
| **Content Area** | 1168×620 |

## III. Visual Theme

### Theme Style

- **Mode**: pyramid。每页标题直接陈述结论，数据必须带比较和“所以什么”。
- **Visual style**: swiss-minimal。严格网格、直角、单线宽、大留白、无阴影、无装饰性卡片堆叠。
- **Theme**: Light theme。
- **Tone**: 精确、克制、工程化、证据导向。
- **Recurring motif**: 屏幕四边形、四角定位点和一条蓝色边框线；仅在关键页面出现，不作为装饰反复铺满。

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#FFFFFF` | 页面底色 |
| **Secondary bg** | `#EFF4F8` | 表格带、图表弱底色 |
| **Primary** | `#111827` | 标题、主结构线 |
| **Accent** | `#0066FF` | 本方案、关键数字、屏幕边框 |
| **Secondary accent** | `#14B8A6` | 正向辅助强调、稳定性 |
| **Body text** | `#1F2937` | 正文 |
| **Secondary text** | `#5B6472` | 注释、说明 |
| **Border/divider** | `#CFD8E3` | 网格与分隔线 |
| **Frame-wise baseline** | `#9AA4B2` | 逐帧检测 |
| **Optical-flow baseline** | `#5B6472` | 相邻帧光流 |
| **Warning** | `#D14343` | 限制与失效风险 |

不使用渐变。强调色占比控制在画布的 5% 以内；以位置、字重和留白建立层级。

## IV. Typography System

### Font Plan

**Typography direction**: 现代无衬线，中文与英文均面向投屏清晰度。

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | Microsoft YaHei | Arial | sans-serif |
| **Body** | Microsoft YaHei | Arial | sans-serif |
| **Emphasis** | Microsoft YaHei | Arial | sans-serif |
| **Code / method id** | Microsoft YaHei | Consolas | monospace |

**Per-role font stacks**:

- Title: `Arial, "Microsoft YaHei", sans-serif`
- Body: `Arial, "Microsoft YaHei", sans-serif`
- Emphasis: same as Body
- Code: `Consolas, "Microsoft YaHei", monospace`

### Font Size Hierarchy

所有尺寸均为无单位 px：

| Role | Size | Weight |
| ---- | ---: | ------ |
| Cover title | 88 | 700 |
| Hero number | 64 | 700 |
| Page title | 54 | 700 |
| Subtitle | 42 | 600 |
| Lead / core message | 36 | 500 |
| Subheading | 36 | 600 |
| Body | 32 | 400 |
| Annotation / chart label | 24 | 400–600 |
| Footnote / page number | 18 | 400 |

## V. Layout Principles

### Page Structure

- **Header area**: y=44–132；标题左对齐，最多两行。
- **Content area**: y=148–660；内容按 12 列隐式网格对齐。
- **Footer area**: y=676–704；左侧来源，右侧页码。
- **Grid**: 12 列，列间距 24；关键对象与 x=56、x=352、x=648、x=944 对齐。
- **Swiss rule**: 每页最多一个主视觉结构；无圆角卡片阵列、无阴影、无渐变。

### Layout Pattern Library

| Pattern | Use |
| ------- | --- |
| Negative-space hero | 封面、总体结论、最终结论 |
| Full-width process spine | 当前管线与失效链 |
| Asymmetric 4:8 split | 方法原理、定性图 + 解释 |
| Three-column comparison | 三种方法机制对比 |
| Small-multiple metric strips | 不同单位/方向的总体指标 |
| Split evidence panels | 滚动与弱边框两类关键场景 |
| Dense ruled table | 消融结果 |

### Spacing Specification

| Element | Current Project |
| ------- | --------------- |
| Safe margin | 56 |
| Content block gap | 32 |
| Icon-text gap | 12 |
| Table row padding | 18 |
| Rule width | 2（主分隔）/ 1（次分隔） |
| Corner radius | 0 |

## VI. Icon Usage Specification

- **Built-in icon library**: `tabler-outline`
- **Stroke width**: 2
- **Method**: `<use data-icon="tabler-outline/icon-name" .../>`

| Purpose | Icon Path | Page |
| ------- | --------- | ---- |
| 视频输入 | `tabler-outline/video` | P02, P03 |
| 屏幕与物理边界 | `tabler-outline/device-desktop` | P02–P05 |
| 边框搜索 | `tabler-outline/scan` | P03, P04 |
| 几何变换 | `tabler-outline/arrows-maximize` | P03 |
| 定量结果 | `tabler-outline/chart-bar` | P06–P08 |
| 时间稳定性 | `tabler-outline/activity` | P07, P10 |
| 安全保障 | `tabler-outline/shield-check` | P11 |
| 重检 | `tabler-outline/refresh` | P03, P11 |
| 风险 | `tabler-outline/alert-triangle` | P12 |
| 焦点/边缘证据 | `tabler-outline/focus-2` | P04 |

## VII. Visualization Reference List

Catalog read: 76 templates

| Page | Template | Path | Summary-quote (verbatim) | Usage |
| ---- | -------- | ---- | ------------------------ | ----- |
| P03 | pipeline_with_stages | `templates/charts/pipeline_with_stages.svg` | "Pick for 3-5 horizontal pipeline stages, each = title + 1-line description + output artifact, connected by arrows (data pipelines, ETL, build pipelines). Skip if any stage lacks an artifact (use process_flow or numbered_steps)." | 四阶段主链：初始化 → 边框观测 → 验证/恢复 → 平滑与变换；native-preset candidate: chevron/block arrow |
| P05 | comparison_table | `templates/charts/comparison_table.svg` | "Pick for 2-4 plans/products compared across many feature rows (dense matrix). Skip for pricing-tier marketing layout (use comparison_columns)." | 三种方法按主证据、传播方式、典型风险进行比较 |
| P06 | labeled_card | `templates/charts/labeled_card.svg` | "Pick for 3-4 parallel aspects of one subject with per-aspect titles + short body (self-introduction, four-pillar overview, capability quadrant). Skip for plain feature lists (use icon_grid), sequential steps (use numbered_steps), or strategic quadrants (use quadrant_text_bullets / matrix_2x2)." | 数据规模、正式评估、已覆盖指标、证据边界四块并列 |
| P07 | no-template-match | — | — | 三项指标量纲和优劣方向不同，使用自定义三条独立刻度带，不强行共轴 |
| P08 | grouped_bar_chart | `templates/charts/grouped_bar_chart.svg` | "Pick for 2-4 series side-by-side across the same categories (e.g. YoY/QoQ). Skip if showing composition within each category (use stacked_bar_chart)." | 滚动与弱边框两类场景中三种方法的 RMSE 并列比较 |
| P10 | basic_table | `templates/charts/basic_table.svg` | "Pick for plain tabular text/number grid, 3-8 columns. Skip if cells need visual bars (use consulting_table) or qualitative scores (use harvey_balls_table)." | 五个消融变体 × 三项指标，完整方法行突出 |
| P11 | vertical_list | `templates/charts/vertical_list.svg` | "Pick for 3-6 numbered key points each with a short description — design principles, core tenets, action items, key takeaways, recommendations, executive summary points. Skip for icon-style cards (use icon_grid) or sequential steps (use numbered_steps)." | 四个相同结果的直接原因与模块角色 |
| P12 | process_flow | `templates/charts/process_flow.svg` | "Pick for 3-8 sequential steps connected by simple arrows — approval workflows, customer onboarding, request handling, lifecycle stages. Skip if cyclical (use circular_stages) or stages produce named outputs (use pipeline_with_stages)." | 边界证据退化到错误变换/回退的失效链；native-preset candidate: block arrow |
| P13 | vertical_list | `templates/charts/vertical_list.svg` | "Pick for 3-6 numbered key points each with a short description — design principles, core tenets, action items, key takeaways, recommendations, executive summary points. Skip for icon-style cards (use icon_grid) or sequential steps (use numbered_steps)." | 三条最终结论 |

**Runners-up considered**:

- `kpi_cards` | rejected for P07: 只有三项且三项都是相对比较，不是 4–8 个独立概览 KPI。
- `grouped_bar_chart` | rejected for P07: RMSE、IoU 与平移变化量纲不同、优劣方向也不同，共轴会误导。
- `feature_matrix_table` | rejected for P05: 各方法差异是机制与风险的定性描述，不是二元勾选能力。

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Acquire Via | Status | Reference | text_policy | page_role |
| -------- | ---------- | ----: | ------- | ---- | -------------- | ----------- | ------ | --------- | ----------- | --------- |
| `figure_01_pipeline.png` | 2194×764 | 2.87 | P03 作为现有论文管线和样例输出的原始证据，无裁切 | Diagram | #19 Image floating in whitespace with thin frame and caption + #70 Image with thin colored matte frame | user | Existing | 仓库当前论文中的边框主导管线图与样例输出 | | |
| `figure_05_qualitative.png` | 2194×2329 | 0.94 | P09 展示五类场景的输入、逐帧、光流和本方案输出 | Qualitative comparison | #45 Background image + numbered hotspots with sidebar legend + #46 Background image + bordered "lens" rectangle highlighting a sub-region + #70 Image with thin colored matte frame | user | Existing | 仓库当前论文中的五类定性比较总图，原生标注强调滚动、弱边框与挑战场景 | | |

两张图均为数据/实验图，不允许裁切掉信息；P09 允许在 SVG 中使用同一图的局部放大视窗，但完整图仍保留为主视图。

## IX. Content Outline

> **Language override confirmed by user**: translate every title, label, caption, chart legend, table cell, footer, and speaker note below into concise technical English. The Chinese text in this section is planning reference only and must never appear in the exported deck.

### Part 1：问题与方案

#### Slide 01 - Cover

- **Cover impact**: 以“3.87 px vs 30+ px”的数据冲突作为视觉钩子；右侧用超大 `3.87`，左侧用一条蓝色四边形轮廓穿过标题，形成非对称数据海报。
- **Layout**: Negative-space poster；左 7 列标题，右 5 列英雄数字；底部仅保留课程标识与日期。
- **Title**: 物理边框主导的屏幕归一化
- **Subtitle**: 从真实拍屏视频中稳定估计屏幕平面
- **Info**: ECE4512 Project · 2026

#### Slide 02 - 难点不是拉正一帧，而是持续估计不被内容运动带偏的屏幕平面

- **Layout**: 左侧问题链，右侧一句核心观点与屏幕四边形示意，大留白。
- **Core message**: 拍屏视频同时包含相机运动和屏幕内部运动，只有把二者分开，才能稳定输出正面屏幕视频。
- **Content**:
  - 输入：背景、透视畸变、手持抖动、反光与内部滚动/视频同时存在。
  - 目标：持续定位物理屏幕四边形，并将每帧变换到固定正面坐标系。
  - 核心观点：让物理屏幕边框决定单应矩阵；内部光流只做冲突诊断。

#### Slide 03 - 当前管线以物理边框更新四边形，并用诊断与回退保证连续输出

- **Layout**: 顶部四阶段原生矢量管线；下方无裁切放置 `figure_01_pipeline.png` 作为论文图证据。
- **Core message**: 主链始终围绕“预测边附近的局部物理边框证据”更新屏幕平面。
- **Visualization**: pipeline_with_stages。
- **Content**:
  - 初始化：人工四角优先，自动检测回退 → 初始四边形。
  - 边框观测：预测四条边的搜索带 → Profile 采样与鲁棒直线拟合 → 四条边线。
  - 验证与恢复：交点形成候选四边形 → 几何门控 + LK 一致性诊断 → 接受、重检或保持。
  - 输出：轨迹插值/平滑 → 单应变换 → 固定尺寸正面视频。

#### Slide 04 - 局部 Profile 把搜索约束在预测边附近，减少内部纹理对平面估计的干扰

- **Layout**: 左 8 列屏幕边框局部采样示意，右 4 列三条原则；边线、内法线、梯度峰值与 RANSAC 拟合均为原生 SVG。
- **Core message**: 当前默认边框观测不是全帧重新找矩形，而是在上一帧预测边附近寻找最可信的物理边界。
- **Content**:
  - 沿每条预测边的内法线采样局部图像 Profile。
  - 在预测位置附近选择高梯度候选点并鲁棒拟合四条直线。
  - 相邻边求交得到四角，凸性、位移和尺度门控决定是否接受。
  - LK/RANSAC 只检查内部运动是否与边框运动冲突，不替代边框结果。

#### Slide 05 - 三种方法真正的区别，是各自相信哪一种证据

- **Layout**: 三列比较表；本方案列用蓝色单线框，基线列使用灰阶。
- **Core message**: 逐帧方法相信当前帧，光流相信内部纹理运动，本方案优先相信物理屏幕边界。
- **Visualization**: comparison_table。
- **Content**:
  - 逐帧检测：每帧独立定位；检测噪声会直接变成抖动，弱边框容易偏移。
  - 相邻帧光流：用内部特征传播四边形；滚动和屏幕内视频会造成内容驱动漂移。
  - 当前边框方案：物理边框更新四边形，内部光流只诊断；优势是抗内部运动，限制是依赖可辨认边界。

### Part 2：实验与结果

#### Slide 06 - 正式证据覆盖 10 个片段的几何与时域指标，细节/频域暂不参与排名

- **Layout**: 四块直角信息区：数据全集、正式评估、指标定义、证据边界。
- **Core message**: 三方案比较采用相同输入、初始化、标注和指标代码，但当前可用于排名的是几何精度与时间稳定性。
- **Visualization**: labeled_card。
- **Content**:
  - 数据全集：50 个自采集视频，共 14,985 帧。
  - 正式定量：五类条件、每类 2 个片段，共 10 个带标注片段；第 0 帧不计入几何评价。
  - 几何：角点 RMSE ↓、四边形 IoU ↑、宽高比误差 ↓。
  - 时域：平移/旋转/尺度变化 ↓；detail 与 frequency 尚未针对当前 `proposal_border` 统一重跑，因此只说明含义、不给排名。

#### Slide 07 - 总体上，本方案同时获得更低误差、更高重叠和更低抖动

- **Layout**: 三条互不共轴的指标带，每条均显示三种方法和方向箭头；下方一句“所以什么”。
- **Core message**: 物理边框方案不是用更平滑换取更差几何，而是在几何精度和时间稳定性上同时占优。
- **Visualization**: custom small-multiple metric strips（no-template-match）。
- **Content**:
  - 角点 RMSE / px ↓：逐帧 30.37；光流 31.40；本方案 **3.87**。
  - 四边形 IoU ↑：逐帧 0.980；光流 0.979；本方案 **0.996**。
  - 平移变化 / px·frame⁻¹ ↓：逐帧 2.83；光流 4.13；本方案 **2.45**。
  - So what：主要收益来自把单应矩阵的主证据从内部纹理切换到物理边界。

#### Slide 08 - 优势集中在滚动与弱边框场景，两类基线误差被显著放大

- **Layout**: 左右两组并列柱状图，统一使用 RMSE；每组顶部显示本方案英雄数字。
- **Core message**: 内部内容运动和弱边界会放大普通方法的失败，而局部边框搜索仍能维持可用几何。
- **Visualization**: grouped_bar_chart。
- **Content**:
  - 滚动：逐帧 31.76；光流 81.67；本方案 **2.87 px**。
  - 弱边框：逐帧 157.26；光流 155.87；本方案 **9.35 px**。
  - 解释：光流容易跟随页面内容；逐帧检测易受单帧边界定位误差影响；本方案把搜索限制在上一帧预测边附近。

#### Slide 09 - 定性结果验证内容运动被保留，但挑战场景仍暴露边界证据退化

- **Layout**: 左 7 列完整 `figure_05_qualitative.png`，原生框线标出滚动、弱边框和挑战行；右 5 列热点图例与挑战场景数据。
- **Core message**: 本方案在滚动、屏幕内视频和弱边框中保持屏幕贴合；反光和极低对比仍是主要限制。
- **Content**:
  - 滚动与屏幕内视频：页面内容被正常保留，输出边缘没有随内部内容明显漂移。
  - 弱边框：分类 RMSE 为 9.35 px，远低于两种基线的 155+ px。
  - 挑战场景：逐帧 RMSE 9.62 略低于本方案 10.70；但本方案平移变化 3.74，低于逐帧 5.19 和光流 8.56。
  - 证据边界：挑战类提醒我们不能把总体优势解释成所有片段逐项获胜。

### Part 3：消融与边界

#### Slide 10 - 轨迹滤波是当前片段中唯一直接改变输出的消融项

- **Layout**: 5 行消融表 + 右侧一条平移变化对比线；完整方案行蓝色强调。
- **Core message**: 去掉轨迹滤波后平移变化从 0.752 上升到 1.430，说明滤波直接负责抑制帧间抖动。
- **Visualization**: basic_table。
- **Content**:
  - 完整 Profile：RMSE 3.253；IoU 0.996038；平移变化 0.752。
  - 去掉轨迹滤波：2.932；0.996585；**1.430**。
  - 去掉 LK 一致性诊断：3.253；0.996038；0.752。
  - 去掉自动重检：3.253；0.996038；0.752。
  - 放宽边缘门控：3.253；0.996038；0.752。

#### Slide 11 - 指标相同并非模块无效，而是安全分支在该片段未被触发

- **Layout**: 四条编号解释，左侧用“主链/安全网”两层结构区分直接贡献和条件贡献。
- **Core message**: 正常边框证据持续有效时，诊断、门控和重检应当保持静默；它们的价值在异常检测与恢复，而不是持续改写主估计。
- **Visualization**: vertical_list。
- **Content**:
  - Profile 主链持续成功：`initial=1`、`edge_accept=298`、`held=0`。
  - LK 仅是诊断信号，不参与边框候选的主接受结果。
  - 自动重检分支没有被触发，因此关闭后数值不变。
  - 默认边缘门控已经全部通过，放宽阈值没有改变候选序列。
  - 结论：Profile 保证几何，滤波提高稳定性；LK、门控和重检构成条件触发的安全保障。

#### Slide 12 - 当前主要风险来自反光、遮挡与极低对比度造成的边界证据退化

- **Layout**: 上半页失效链，下半页改进方向；警示色只用于链中风险节点。
- **Core message**: 方法的极限不是内部内容运动，而是物理边界本身不可见或出现更强伪边缘。
- **Visualization**: process_flow。
- **Content**:
  - 失效链：真实边界梯度过弱/被反光遮挡 → Profile 选错候选 → 直线或交点偏移 → 门控拒绝或错误变换 → 重检/保持。
  - 观察：弱边框总体显著改善，但仍有片段 RMSE 14.39 px，高于多数普通片段。
  - 改进：反光饱和区降权；融合 Profile、LSD、颜色差与矩形约束；按边输出置信度；连续失败时主动重新初始化。

### Part 4：结论

#### Slide 13 - 物理边框应当是屏幕平面估计的主证据，内部光流只做诊断

- **Closing impact**: 让观众带走“边框主导、光流诊断”的一句话；使用一个超大蓝色屏幕四边形包围三条结论，右下角重复 3.87 / 0.996 / 2.45 数据签名。
- **Layout**: Negative-space closing poster；三条结论纵向排列，右下为数据签名，无“Thank you”占位页。
- **Core message**: 当前方案通过物理边框主链、轨迹滤波和条件触发安全网，同时获得更高几何精度与更好时间稳定性。
- **Visualization**: vertical_list。
- **Content**:
  - 主证据：物理屏幕边框直接决定四边形与单应矩阵。
  - 对比优势：避免逐帧检测噪声，也避免内部光流随滚动/视频内容漂移。
  - 工程完整性：Profile 主链 + 轨迹滤波 + LK/门控/重检安全网。
  - 总体结果：RMSE **3.87 px**、IoU **0.996**、平移变化 **2.45 px/frame**。

## X. Speaker Notes Requirements

- 每页一个 Markdown 文件，文件名与 SVG 一致，例如 `01_cover.md`。
- 风格：English, conclusion-first, natural spoken delivery with technical precision.
- 目的：report + persuade；用实验事实支撑当前方案相对逐帧和光流的优势。
- 每页首句直接说结论，随后给 2–3 个事实；所有数字都在同一句中带比较。
- 每页 35–55 秒；封面 20 秒，管线与结果页可到 60 秒，总时长控制在 10–12 分钟。
- 数据页页脚来源：`doc/current/paper/manuscript/paper_zh.md`；消融页另标 `doc/current/paper/proposal_border_ablation_2026-07-14.md`。
