# SuperPoint + LightGlue 单应估计探针结果

测试时间：2026-06-22

## 目的

本次测试不是把模型直接接入最终视频处理流程，而是先回答一个问题：

> 学习式特征点和匹配器能否在拍屏视频中稳定估计屏幕平面 homography，并值得作为 Final 项目的模型分支？

新增脚本：

```bash
uv run scripts/probe_learned_homography.py <input-video>
```

脚本流程：

1. 从首帧检测或读取屏幕四角点；
2. 把首帧屏幕 warp 成固定 16:9 参考图；
3. 对参考图和抽样视频帧分别用 SuperPoint 提取关键点；
4. 用 LightGlue 匹配参考图和当前帧；
5. 用 RANSAC 从匹配点估计 reference-screen 到 current-frame 的 homography；
6. 输出接受率、匹配点数、RANSAC 内点数、重投影误差和覆盖范围。

## 抽样结果

| 输入视频 | 抽样帧 | 接受帧 | 接受率 | 匹配点中位数 | 内点中位数 | 内点比例中位数 | 重投影误差中位数 | 结论 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `VID20260621024117.mp4` | 32 | 32 | 1.000 | 935.5 | 670.0 | 0.714 | 1.887 px | 可稳定匹配 |
| `VID20260621031719.mp4` | 32 | 32 | 1.000 | 843.0 | 688.5 | 0.816 | 1.701 px | 可稳定匹配 |
| `testmoire.mp4` | 23 | 8 | 0.348 | 167.0 | 56.0 | 0.310 | 2.233 px | 不稳定，不适合直接驱动 |

输出目录：

```text
runs/probe_lightglue_vid24117_stride10/
runs/probe_lightglue_vid31719_stride10/
runs/probe_lightglue_testmoire_stride10/
```

## 和现有 LK baseline 的关系

对 `VID20260621031719.mp4` 的同一批抽样帧，已有 LK reference tracker 的 debug 数据来自：

```text
runs/debug_tracker_reference_mature/tracker_debug.csv
```

同帧粗略对比：

| 指标 | LK reference tracker | SuperPoint + LightGlue |
| --- | ---: | ---: |
| 内点数中位数 | 737.0 | 688.5 |
| 内点比例中位数 | 0.989 | 0.816 |
| 重投影误差中位数 | 0.168 px | 1.701 px |
| x 覆盖中位数 | 0.753 | 0.823 |
| y 覆盖中位数 | 0.934 | 0.933 |

这说明 SuperPoint + LightGlue 的匹配覆盖更宽，但几何精度目前不如已有 LK tracker。它不应该立刻替换现有主方法。

## 结论

SuperPoint + LightGlue 值得加入 Final 项目，但定位应该是：

- 作为 **学习式特征匹配分支**；
- 和传统 LK tracker 做对照实验；
- 不承诺直接提升当前最好结果；
- 不用于去反光、去摩尔纹或画质恢复；
- 必须继续使用 RANSAC、覆盖率检查、重投影误差和几何门控。

当前最合理的项目升级方式是：

```text
传统 LK + RANSAC baseline
        vs
SuperPoint/LightGlue + RANSAC model branch
        +
合成拍屏 benchmark 的真值评价
```

`testmoire.mp4` 的结果也说明：学习式匹配不是万能解。屏幕内容动态大、纹理变化强或画面质量差时，匹配数量和几何一致性会明显下降。因此 Final 报告中应把它作为可比较方法，而不是包装成一定更好的方法。
