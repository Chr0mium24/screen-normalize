# 应用端链路叙事：从拍屏捕获矫正到视频去摩尔纹

## 核心定位

这个项目不应该只讲成一个“把视频裁成屏幕区域”的几何 demo。更合理的故事是：

> 现有拍屏图像/视频去摩尔纹工作通常建立在较受控的实验室采集和已对齐数据上；而在真实应用中，用户拿到的是一段手持拍摄的完整场景视频，里面包含屏幕外背景、倾斜视角、边框、手抖和屏幕内部动态内容。因此，在去摩尔纹和画质恢复之前，需要先完成屏幕内容捕获矫正、透视归一化和时域稳定化。

也就是说，本项目补的是应用端链路前半段：

```text
真实手持拍屏视频
  -> 屏幕区域检测
  -> 透视矫正
  -> 屏幕平面跟踪
  -> 时域稳定
  -> 接近录屏视角的屏幕视频
  -> 后续可接视频去摩尔纹 / 颜色校正 / 细节恢复
```

现有 video demoiréing 论文可以作为后续恢复模块的参考；本项目则强调它们之前缺少的真实场景预处理：从完整拍摄画面中定位、拉正并稳定屏幕内容。

## 与拍屏去摩尔纹论文的关系

已有拍屏恢复论文证明了“拍屏图像和视频恢复”是真实问题，但它们大多不把任意真实场景中的屏幕边框检测作为核心任务。

- **Video Demoiréing with Relation-Based Temporal Consistency, CVPR 2022**  
  论文研究手持拍屏视频中的摩尔纹去除和时间一致性。项目页说明数据集中输入 moiré frames 和输出 clean frames 通过 homography matrix 对齐，后续版本又用 RAFT optical flow 细化对齐。因此它重点解决的是已对齐拍屏内容的恢复，而不是从完整真实画面中自动找到屏幕四边形。  
  Source: https://arxiv.org/abs/2204.02957  
  Project: https://daipengwa.github.io/VDmoire_ProjectPage/

- **Direction-aware Video Demoiréing with Temporal-guided Bilateral Learning, AAAI 2024**  
  论文面向拍摄屏幕时产生的图像/视频摩尔纹，方法包含去摩尔纹、对齐、颜色校正和细节恢复。这里的 alignment 主要服务于视频恢复网络和相邻帧信息聚合，不等同于通用场景下的屏幕检测和透视归一化。  
  Source: https://arxiv.org/abs/2308.13388  
  Code: https://github.com/rebeccaeexu/DTNet

- **Recaptured Raw Screen Image and Video Demoiréing via Channel and Spatial Modulations, NeurIPS 2023**  
  论文构建 raw domain 的拍屏图像/视频去摩尔纹数据集，并通过插入 alternating patterns 做更可靠的时序对齐。它同样说明研究重点是已采集、已对齐或可控对齐数据上的去摩尔纹，而不是真实用户视频里的屏幕定位和稳定。  
  Source: https://arxiv.org/abs/2310.20332  
  Code: https://github.com/tju-chengyijia/VD_raw

因此，本项目可以被表述为这些拍屏恢复方法的前置模块：

```text
本项目：真实场景屏幕捕获矫正与稳定
后续模块：视频去摩尔纹、颜色校正、细节恢复
```

这个定位比单独说“视频稳定化”更完整，也避免和现有 video demoiréing 论文正面重复。

## 与 log-homography 视频稳定论文的关系

**Cinematic-L1 Video Stabilization with a Log-Homography Model** 做的是通用手持视频稳定化。它的目标是把普通手持视频中的抖动相机运动优化成更像三脚架、匀速平移或稳定器拍摄的平滑相机路径。

这篇论文的关键点包括：

- 用 full homography 表示帧间运动，而不是只用 affine 变换，因此能处理一定的透视变化；
- 把 homography 映射到 log-homography space，使相机路径优化更接近线性问题；
- 通过 L1 优化惩罚稳定后运动的一阶、二阶、三阶导数，鼓励静止镜头、匀速平移和平滑加速；
- 在优化中加入 crop constraints 和 distortion constraints，控制稳定化带来的裁切和形变。

本项目不需要完整复现这篇论文的凸优化框架，但可以引用它来支撑视频稳定化部分的理论依据：

> 拍屏视频中的屏幕平面运动可以表示为一条 homography 轨迹；对这条轨迹做时域平滑和异常抑制，可以去除手持拍摄和逐帧估计误差造成的高频抖动。

二者关系可以这样写：

| Cinematic-L1 论文 | 本项目 |
| --- | --- |
| 通用手持视频稳定 | 拍屏视频中的屏幕平面稳定 |
| 稳定整个相机视角 | 稳定屏幕所在平面 |
| full homography + log-space 路径优化 | homography 估计 + 几何门控 + 轨迹平滑 |
| 输出更平滑的普通视频 | 输出接近录屏视角的屏幕内容视频 |

Source: https://arxiv.org/abs/2011.08144

## 最终报告中的推荐表述

可以把项目故事压缩成下面这段：

> Existing screen image/video demoiréing methods show that camera-captured screens are a real restoration problem, but many of them rely on controlled acquisition or pre-aligned screen content. In real user scenarios, the captured video first contains background, monitor borders, perspective distortion, camera shake, and dynamic screen content. Therefore, before demoiréing or detail restoration, an application-level preprocessing stage is needed to detect the screen plane, rectify it to a frontal view, and stabilize its homography trajectory over time. Our project focuses on this missing front-end stage and can be connected with video demoiréing modules as a complete screen video restoration pipeline.

中文版本：

> 现有拍屏图像和视频去摩尔纹方法证明了拍屏恢复问题的价值，但这些工作多依赖受控采集或已对齐的屏幕内容。在真实应用中，用户输入首先是一段包含背景、屏幕边框、透视倾斜、手持抖动和动态屏幕内容的完整视频。因此，在去摩尔纹、颜色校正和细节恢复之前，需要一个应用端预处理阶段，对屏幕平面进行检测、透视归一化和时域稳定。本项目聚焦于补全这一前置链路，并可与后续视频去摩尔纹模块组成完整的拍屏视频恢复系统。
