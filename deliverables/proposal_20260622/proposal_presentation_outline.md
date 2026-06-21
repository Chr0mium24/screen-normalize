# Proposal Presentation Outline

1. Title and Motivation
   - 手机拍屏视频存在背景、透视、手抖和动态内容干扰。
   - 项目目标是转成接近正常录屏观感的视频。

2. Problem Definition and Goal
   - 屏幕被建模为平面目标。
   - 输出固定 16:9、固定分辨率、时间稳定。

3. Methodology
   - 首帧角点/自动检测。
   - Homography 透视归一化。
   - LK 光流 + RANSAC 参考平面跟踪。
   - 几何门控、插值和平滑。

4. Dataset and Initial Result
   - 本地 1920x1080 拍屏样例。
   - 原始帧和归一化帧对比。

5. Evaluation
   - 残余平移、旋转、尺度变化。
   - 当前 1080p 输出最后 2 秒 translation p95 = 0.118 px。

6. Timeline and References
   - Proposal 阶段完成主流程。
   - Final 阶段做多视频实验、消融和失败案例。
