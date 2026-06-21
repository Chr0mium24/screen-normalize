# Proposal for CIE6032 Final Project 2025

**Names & IDs:** 待填写  
**Title:** 基于传统图像处理的拍屏视频几何归一化与稳定化

## Description

本项目研究如何把手机拍摄电脑屏幕得到的视频转换成接近正常录屏观感的视频。拍屏视频通常同时包含屏幕外背景、斜拍透视畸变、手持抖动，以及屏幕内部播放视频、页面滚动、鼠标移动等真实内容变化。已有文档矫正、白板扫描、视频稳定化工作分别处理静态平面矫正或一般相机运动平滑，但直接逐帧检测屏幕角点会把检测误差放大成画面抽搐，直接用内部线条或文字也容易被动态内容误导。

本项目的核心假设是：电脑屏幕可以近似看作平面目标，屏幕平面到相机图像之间可由单应变换描述。方法上使用首帧屏幕四角点建立参考平面，再用 LK 光流、RANSAC 单应性估计、几何门控、坏帧插值和角点轨迹平滑，得到固定比例、固定分辨率的正面屏幕视频。

## Task and Goal

任务输入是一段拍摄电脑屏幕的视频，输出为只保留屏幕内容、透视拉正且时间上稳定的视频。项目目标不是做画质恢复或语义理解，而是聚焦传统图像处理中的几何归一化与稳定化：裁掉墙面和桌面背景，固定输出为 16:9 画布，抑制逐帧角点误差造成的平移、旋转、缩放和透视抖动，同时保留屏幕内部真实内容变化。

## Methodology

1. 首帧屏幕区域检测，自动失败时允许手动四角点初始化。
2. 对四角点排序并估计单应变换，将屏幕映射到固定矩形画布。
3. 在参考平面内选择稳定角点，用金字塔 Lucas-Kanade 光流跟踪。
4. 用 RANSAC 估计当前帧相对参考平面的单应性，拒绝离群匹配。
5. 根据内点数、内点比例、覆盖范围、面积变化和边长变化做几何门控。
6. 对不可靠帧先插值，再对角点轨迹做时域平滑，降低高频抖动。
7. 输出视频并用残余平移、旋转、尺度变化评价稳定性。

## Dataset and Experiment

当前 Proposal 阶段使用一段本地拍屏样例作为初步验证：`inputs/VID20260621024117.mp4`，分辨率 1920x1080，约 5.27 秒，317 帧，约 60 fps。最新结果位于 `runs/proposal_best_geometry_gate/VID20260621024117_normalized.mp4`，输出保持 1920x1080。后续 Final 阶段计划扩展到 3-5 段本地视频，覆盖静态桌面、网页滚动、屏幕内部播放视频、轻微反光、边缘遮挡和自动角点检测失败等情况。

主方法命令：

```bash
uv run scripts/normalize_screen.py inputs/VID20260621024117.mp4 \
  --tracker reference \
  --reference-profile low-latency \
  --write-tracker-debug \
  --write-trajectory-debug \
  --run-name proposal_best_geometry_gate
```

稳定性分析命令：

```bash
uv run scripts/analyze_stability.py \
  runs/proposal_best_geometry_gate/VID20260621024117_normalized.mp4 \
  --run-name analyze_proposal_best_geometry_gate
```

## Initial Results

最新 1080p 输出的整体残余运动较低：全片相邻帧残余平移 p95 为 0.146 px，残余旋转 p95 为 0.0047 deg，尺度变化 p95 为 0.000151。最后 2 秒的残余平移 p95 为 0.118 px，残余旋转 p95 为 0.0044 deg，尺度变化 p95 为 0.000118。视觉上，输出已基本去除墙面和桌面背景，并将斜拍屏幕转换为固定 16:9 画面。

## Expected Results

Final 阶段期望证明：参考平面跟踪 + 鲁棒几何门控 + 离线轨迹平滑，比逐帧屏幕检测和普通光流跟踪更稳定。报告将给出多视频对比、消融实验表格、关键帧截图、失败案例分析和运行命令，明确哪些场景能稳定处理，哪些场景仍需要手动初始化或会失败。

## Tentative Timeline / To-do List

- 已完成：方向固定、参考文献整理、纯传统视觉主流程、初步输出和稳定性分析。
- 下一步：固定 3-5 段实验视频，整理自动角点和手动角点配置。
- 随后：跑主方法、逐帧检测、普通光流、不同轨迹平滑窗口等消融实验。
- 最后：整理结果表、关键帧和失败案例，完成 Final 报告与演示视频。

## Key References

- Okatani & Deguchi, *Screen-to-Camera Homography Estimation*, ICCV 2003.
- Zhang & He, *Whiteboard Scanning and Image Enhancement*, 2007.
- Lucas & Kanade, *An Iterative Image Registration Technique*, 1981.
- Shi & Tomasi, *Good Features to Track*, CVPR 1994.
- Torr & Zisserman, *MLESAC*, CVIU 2000.
- Sánchez & Morel, *Motion Smoothing Strategies for Video Stabilization*, IPOL 2017.
- Grundmann et al., *Auto-Directed Video Stabilization with Robust L1 Optimal Camera Paths*, CVPR 2011.
- Guilluy et al., *A Performance Evaluation Framework for Video Stabilization Methods*, EUVIP 2018.
