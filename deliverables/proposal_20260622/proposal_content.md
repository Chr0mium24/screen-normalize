# Proposal 内容稿

题目：**面向真实场景拍屏视频恢复的屏幕捕获矫正与时域稳定化**

本文件先作为 PPT 和报告的唯一内容源。先审内容、图和数据逻辑，确认后再导出 PPT/Word。

## 参考模板在做什么

`reference/proposal/example_proposal_presentation.pdf` 的结构很简单，不是在写 Final：

1. **Title + Motivation**  
   一句话说明问题为什么值得做。
2. **Goal and Methodology**  
   说明目标和 3-4 步方法。
3. **Dataset and Initial Results**  
   给出数据来源、初步图像结果和下一步评价方向。

`reference/proposal/proposal_template.docx` 也只要求一页：

- Description
- Task and goal
- Dataset and experiment
- Expected results
- Timeline / To-do list

所以本项目 Proposal 不应该写成完整 Final，也不应该堆很多没有实验证据的内容。当前要讲清楚的是：**真实拍屏视频在进入去摩尔纹、OCR 或归档之前，如何先通过传统几何方法完成屏幕捕获矫正、透视归一化和时域稳定，以及已有初步结果证明主流程能跑通。**

## 当前内容边界

本 Proposal 只讲前置几何链路：

- 屏幕区域定位；
- 透视矫正；
- 参考平面跟踪；
- 鲁棒几何估计；
- 输出视频的残余晃动评价。

不直接做去摩尔纹、颜色校正或画质恢复；这些属于后续可连接的 restoration 模块。

## 一页报告内容草稿

### Names & IDs

待填写

### Title

面向真实场景拍屏视频恢复的屏幕捕获矫正与时域稳定化

### Description

手机拍摄电脑屏幕时，视频中通常会同时出现屏幕外背景、斜拍造成的透视变形、手持拍摄带来的轻微晃动，以及屏幕内部内容变化。现有拍屏图像/视频去摩尔纹研究说明屏幕恢复是一个真实问题，但相关数据集通常服务于去摩尔纹或图像恢复任务，输入往往已经经过受控采集、裁剪、配对或时空对齐。在真实应用中，去摩尔纹、颜色校正或 OCR 之前，需要先把完整拍摄画面中的屏幕内容捕获、拉正并稳定。

对于课程项目，本工作希望把这类拍屏视频转换成接近正常录屏视角的视频：画面只保留屏幕内容，屏幕被拉正到固定比例，并且在时间上尽量稳定。这个输出可以作为后续 video demoiréing、归档或人工查看的前置输入。

这个问题可以建模为平面目标的几何归一化问题。电脑屏幕近似是一个平面，屏幕平面到相机图像之间可以用单应变换描述。难点在于：如果每帧都重新检测屏幕角点，角点误差会直接表现为画面抖动；如果直接依赖屏幕内部文字、播放器画面或网页内容，这些动态内容又可能错误地影响屏幕姿态估计。因此，本项目采用参考平面跟踪和鲁棒几何估计来稳定估计屏幕位置。

### Related datasets and gap

现有公开数据集可以证明拍屏恢复需求真实存在，但也能说明本项目补的是前置几何链路，而不是重复做一个去摩尔纹网络。

| 数据集/工作 | 数据特点 | 对本项目的启发 |
| --- | --- | --- |
| LCDMoire / AIM 2019 | 10,200 对合成 moiré/clean 图像，面向 image demoiréing benchmark | 证明屏幕 moiré 是标准恢复问题，但它不是完整手机拍屏视频，也不评估屏幕捕获和稳定 |
| UHDM | 5,000 对 4K 真实拍屏图像，覆盖不同设备和视角 | 更接近真实高清拍屏，但仍主要是图像对，重点不是视频中的透视稳定 |
| CVPR 2022 Video Demoiréing | 290 个 720p 手持拍屏视频，每个 60 帧，数据采集流程保证输入和 clean frames 的空间/时间对齐 | 证明 video demoiréing 需求存在，但它的数据设计已经解决了对齐问题；本项目关注对齐之前的真实拍屏输入 |
| RawVDemoiré | raw 域图像/视频 demoiréing，并构建 well-aligned raw video demoiréing dataset | 进一步说明主流 video demoiréing 工作需要良好对齐的数据，而本项目提供前置的几何归一化输入 |

因此，Proposal 阶段不应说“公开数据集没有实拍图像”。更准确的表述是：公开数据集已有真实设备采集或手持视频，但多数处在受控、裁剪、配对或已对齐的数据形态；本项目要处理的是更靠前的应用端输入，即带背景、边框、透视倾斜、手持晃动和动态屏幕内容的完整拍屏视频。

参考来源：

- Video Demoireing with Relation-based Temporal Consistency, CVPR 2022: https://daipengwa.github.io/VDmoire_ProjectPage/
- AIM 2019 Challenge on Image Demoireing / LCDMoire: https://ar5iv.labs.arxiv.org/html/1911.02498
- Towards Efficient and Scale-Robust Ultra-High-Definition Image Demoiréing / UHDM: https://xinyu-andy.github.io/uhdm-page/
- Recaptured Raw Screen Image and Video Demoiréing via Channel and Spatial Modulations / RawVDemoiré: https://arxiv.org/abs/2310.20332

### Task and goal

输入是一段拍摄电脑屏幕的视频。输出是一段固定 16:9、固定分辨率的正面屏幕视频。

目标包括：

- 去掉墙面、桌面和屏幕外背景；
- 把斜拍屏幕校正为正面矩形画面；
- 保持输出长宽比固定；
- 降低逐帧角点误差造成的平移、旋转和缩放抖动；
- 保留屏幕内部真实内容变化；
- 为后续去摩尔纹、OCR 或归档提供稳定、对齐的输入。

### Dataset and experiment

当前 Proposal 阶段使用一段本地拍屏视频作为初步样例：

- 输入：`inputs/VID20260621024117.mp4`
- 分辨率：1920x1080
- 帧数：317
- 时长：约 5.27 秒
- 内容：电脑屏幕中的文本页面，屏幕外包含墙面和桌面背景，存在明显透视倾斜。

当前实验不靠“多补几个视频”来撑内容，而是在同一段输入、同一分辨率、同一帧数下比较三种几何轨迹来源：

| 方法 | 作用 | 输出 |
| --- | --- | --- |
| 逐帧检测角点 | 作为抖动基线 | `runs/verify_old_detect_current/VID20260621024117_normalized.mp4` |
| 普通光流跟踪 | 作为跟踪基线 | `runs/verify_old_flow_current/VID20260621024117_normalized.mp4` |
| 参考平面跟踪 | 当前主方法 | `runs/proposal_best_geometry_gate/VID20260621024117_normalized.mp4` |

评价脚本 `scripts/analyze_stability.py` 估计归一化后相邻帧之间的残余仿射运动。这个指标衡量输出视频还剩多少帧间晃动，不等价于有真实录屏 ground truth 的重建误差。

当前同视频初步结果：

| 方法 | 最后 2 秒残余平移 p95 | 最后 2 秒残余旋转 p95 | 最后 2 秒尺度变化 p95 |
| --- | ---: | ---: | ---: |
| 逐帧检测角点 | 1.927 px | 0.0425 deg | 0.001079 |
| 普通光流跟踪 | 1.929 px | 0.0263 deg | 0.000589 |
| 参考平面跟踪 | 0.118 px | 0.0044 deg | 0.000118 |

这组数据只支持一个结论：在当前样例上，参考平面跟踪比逐帧角点检测和普通光流跟踪产生更低的残余晃动。它还不能支持“所有拍屏视频都稳定”的 Final 结论。

### Expected results

最终希望证明：把屏幕当作参考平面并用 LK 光流 + RANSAC 估计单应变换，比逐帧独立检测角点更适合真实拍屏视频的前置矫正和稳定。预期输出是接近录屏的固定比例视频，并能通过残余平移、旋转和尺度变化指标说明稳定性提升。

Final 阶段不应只追加视频数量，而应补齐以下证据：

- 同一输入上的方法消融；
- 屏幕四角点可视化；
- 归一化前后帧对比；
- 失败或不稳定场景的原因说明；
- 每个数字对应的运行命令和输出路径。

### Timeline / To-do list

- 已完成：应用端前处理主线确定；实现屏幕透视归一化；实现参考平面跟踪；生成同视频初步对比结果。
- 下一步：把本内容稿整理成 Proposal PPT 和一页报告。
- Final 前：补齐消融图表、失败案例图、运行命令和结果目录说明。

## PPT 内容草稿

按 example proposal 做 3 页即可。

### Slide 1: Title and Motivation

标题：面向真实场景拍屏视频恢复的屏幕捕获矫正与时域稳定化

Motivation:

手机拍摄电脑屏幕时，视频里会包含墙面和桌面背景，屏幕也会因为斜拍产生透视变形。已有 LCDMoire、UHDM、Video Demoiréing 和 RawVDemoiré 等数据集说明拍屏恢复是一个真实需求，但它们通常面向受控、裁剪、配对或已对齐的去摩尔纹输入；真实应用中还需要先完成屏幕定位、透视矫正和时域稳定。目标是把这种完整拍屏视频转换为接近正常录屏的视频：只保留屏幕内容，校正为正面矩形，并尽量减少帧间抖动。

推荐图：

- `assets/input_frame_4s.jpg`  
  原始拍屏帧，展示墙面、桌面和透视倾斜。
- 或 `assets/screen_corners_overlay_4s.jpg`  
  在原始帧上标出屏幕四角点，直观说明问题是屏幕平面的几何归一化。

### Slide 2: Goal and Methodology

Goal:

输入真实拍屏视频，输出固定 16:9 的正面屏幕视频，并降低由角点估计误差和手持拍摄造成的帧间晃动。

Plan of Action:

1. 在首帧定位屏幕四角点。
2. 用单应变换把屏幕映射到固定矩形画布。
3. 在屏幕参考平面内跟踪特征点。
4. 用 RANSAC 估计参考平面到当前帧的单应变换。
5. 用残余帧间运动指标评价输出稳定性。

推荐图：

- 方法流程图，用文字框即可：

```text
input video
  -> screen corners
  -> homography rectification
  -> LK feature tracking on reference plane
  -> RANSAC homography
  -> normalized video
```

暂时不放“raw vs smoothed trajectory”图。原因是当前最好样例里 `trajectory_debug.csv` 的 raw 和 smoothed 完全相同，放这个图不能证明平滑有效。

### Slide 3: Dataset and Initial Results

Dataset:

- Related datasets: LCDMoire、UHDM、Video Demoiréing、RawVDemoiré 证明拍屏恢复需求存在，但主要服务于去摩尔纹/恢复模型，不直接覆盖完整拍屏视频的前置捕获和稳定。
- 本地拍屏视频：`inputs/VID20260621024117.mp4`
- 1920x1080，317 帧，约 5.27 秒。

Initial results:

- `assets/comparison_4s.jpg`  
  左边是原始拍屏帧，右边是归一化输出帧。
- `assets/method_ablation_translation_p95.png`  
  同一输入视频上，三种方法的最后 2 秒残余平移 p95 对比。

Slide 上只写关键结论：

参考平面跟踪把最后 2 秒残余平移 p95 从约 1.93 px 降到 0.118 px。这个结果说明主流程在当前样例上能显著降低输出视频的帧间晃动。

## 图表清单

| 编号 | 文件 | 放在哪里 | 作用 | 当前状态 |
| --- | --- | --- | --- | --- |
| Fig. 1 | `assets/input_frame_4s.jpg` | Slide 1 / 报告 Description | 展示原始拍屏问题 | 已有 |
| Fig. 2 | `assets/screen_corners_overlay_4s.jpg` | Slide 1 或 Slide 2 | 展示屏幕平面和四角点 | 已生成 |
| Fig. 3 | `assets/comparison_4s.jpg` | Slide 3 / 报告 Initial Results | 展示归一化前后对比 | 已有 |
| Fig. 4 | `assets/method_ablation_translation_p95.png` | Slide 3 / 报告 Dataset and experiment | 展示同视频方法对比 | 已生成 |
| Table 1 | `evidence/proposal_ablation_summary.csv` | 报告 Dataset and experiment | 记录三种方法的指标来源 | 已生成 |

暂时不放的图：

- raw/interpolated/smoothed 轨迹图：当前样例 raw 和 smoothed 没有差异，不能支撑结论。
- 多视频平均表：当前没有清晰实验设计，单纯增加视频数量不会让 Proposal 更有说服力。

## 当前最好结果和证据路径

当前最好输出：

```text
runs/proposal_best_geometry_gate/VID20260621024117_normalized.mp4
```

交付包内复制件：

```text
deliverables/proposal_20260622/evidence/best_result_normalized.mp4
```

稳定性摘要：

```text
deliverables/proposal_20260622/evidence/stability_summary.json
```

同视频消融表：

```text
deliverables/proposal_20260622/evidence/proposal_ablation_summary.csv
```

## 现在不应该怎么写

不要写“已经完整解决拍屏视频转录屏”。当前只能说：

> 在一个 1920x1080 本地拍屏样例上，参考平面跟踪相比逐帧检测和普通光流跟踪明显降低残余帧间运动，说明传统几何归一化主流程可行。

不要用不清楚的数据。每个数字必须能追到：

- 输入视频；
- 运行目录；
- 评价脚本；
- JSON/CSV 结果；
- 对应图表。
