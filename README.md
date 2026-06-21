# screen-normalize

把手持拍摄的电脑屏幕视频转换成接近正常录屏的视频。

这是一个数字图像处理课程大作业项目。当前版本主要完成第一阶段：用传统计算机视觉方法从拍屏幕视频中识别屏幕平面、做透视矫正、裁切出屏幕内容，并把输出保存成稳定的 16:9 视频。第二阶段计划在频域特征上训练去摩尔纹模型，第三阶段把几何归一化和画质恢复串成完整流程。

## 项目目标

输入是一段手机或相机拍摄的电脑屏幕视频，画面中通常包含墙面、桌面、屏幕边框、透视变形、轻微手抖和摩尔纹。

目标输出是只保留屏幕内容的正常视频：

- 去掉屏幕外的墙面、桌面和边框；
- 把倾斜拍摄的屏幕透视校正成正面视角；
- 保持输出长宽比固定，默认输出 `1920x1080`；
- 尽量减少由于手持拍摄造成的画面晃动；
- 后续进一步消除拍屏幕产生的摩尔纹和频域条纹。

## 方法路线

### 阶段一：传统视觉几何归一化

当前已经基本完成。

这一阶段负责从原始视频中拿到稳定的屏幕画面：

1. 首帧自动检测屏幕区域，或用手动四角点兜底。
2. 对屏幕四角点排序为 `TL,TR,BR,BL`。
3. 用透视变换把屏幕平面映射到固定输出画布。
4. 用 Lucas-Kanade 光流跟踪屏幕内部特征点。
5. 用 RANSAC 估计参考平面到当前帧的单应性矩阵。
6. 用几何门控过滤异常更新，例如点数不足、内点比例过低、覆盖范围不足、重投影误差过大、面积或边长突变。
7. 每次运行自动写入 `runs/<时间>_<脚本名>/`，便于复现实验。

当前第一阶段可以作为 proposal 或中期结果展示：它已经能完成“拍屏幕视频到正面裁切视频”的核心流程。还需要在 final 阶段补充更多输入样例、失败案例和消融对比。

### 阶段二：频域去摩尔纹

尚未实现。

计划方向是把第一阶段得到的正面屏幕视频作为输入，再对屏幕内容做频域分析和学习式恢复：

1. 对归一化后的帧做 Fourier/DCT 等频域表示。
2. 分析摩尔纹在频谱中的高频峰值、周期纹理和颜色干扰。
3. 构造训练数据，可以使用拍屏幕帧和真实录屏帧作为近似配对，或使用合成摩尔纹数据做监督训练。
4. 训练轻量模型预测去摩尔纹后的图像，或预测频域 mask 后再回到图像域。
5. 与传统低通、带阻滤波、双边滤波等方法做对比。

FPANet 已作为第二阶段候选视频去摩尔纹模型接入到本项目的部署脚本中。它需要 NVIDIA CUDA 环境和 DCNv2 编译，具体见 `doc/fpanet-deployment.md`。

### 阶段三：完整视频恢复

尚未实现。

最终目标是串联：

```text
原始拍屏幕视频
  -> 屏幕检测和透视矫正
  -> 固定比例裁切
  -> 去摩尔纹和画质恢复
  -> 正常屏幕视频
```

## 当前结论

第一阶段已经差不多完成，理由是：

- 有完整可运行脚本 `scripts/normalize_screen.py`；
- 支持自动角点检测，也支持手动角点覆盖；
- 支持 `detect`、`flow`、`reference` 三种角点轨迹来源；
- 推荐的 `reference` 模式已经用光流、RANSAC 和门控把屏幕平面锁到参考帧；
- 支持输出 tracker debug CSV，便于解释每帧为什么接受或拒绝更新；
- 支持稳定性分析脚本 `scripts/analyze_stability.py`；
- 输出目录已经规范到 `runs/` 下，适合批量实验和报告记录。

但第一阶段还不能说完全结束：

- 自动检测目前对屏幕外观有假设，遇到边框颜色、反光或遮挡变化时可能需要手动四角点；
- 大面积播放视频、滚动页面或快速变化内容会干扰特征点跟踪；
- 去摩尔纹还没有做，输出仍可能有拍屏幕纹理；
- final report 里还需要系统展示不同输入、不同 tracker、是否手动角点、是否裁切的对比。

## 环境

本项目使用 `uv` 管理 Python 运行环境。脚本顶部已经写了依赖声明，直接用 `uv run` 执行即可。

```bash
uv run scripts/normalize_screen.py --help
```

还需要本机安装 `ffmpeg`，用于把处理后的帧重新编码成视频。

## 快速开始

把输入视频放到 `inputs/` 目录，例如：

```text
inputs/my_screen_video.mp4
```

推荐先用静态屏幕配置运行：

```bash
uv run scripts/normalize_screen.py inputs/my_screen_video.mp4 --tracker reference --reference-profile low-latency
```

输出文件会写到：

```text
runs/<时间>_normalize_screen/my_screen_video_normalized.mp4
```

如果希望固定输出目录名，使用 `--run-name`：

```bash
uv run scripts/normalize_screen.py inputs/my_screen_video.mp4 --tracker reference --reference-profile low-latency --run-name stage1_test
```

## 常用运行方式

自动检测屏幕并透视矫正：

```bash
uv run scripts/normalize_screen.py inputs/my_screen_video.mp4 --tracker reference --reference-profile low-latency
```

如果自动角点不准，手动指定第一帧四个角点，顺序是左上、右上、右下、左下：

```bash
uv run scripts/normalize_screen.py inputs/my_screen_video.mp4 --tracker reference --reference-profile low-latency --corners "124,116:1488,132:1516,850:145,934"
```

如果输出中还留有边框或播放器边缘，可以在透视矫正后裁切：

```bash
uv run scripts/normalize_screen.py inputs/my_screen_video.mp4 --tracker reference --reference-profile low-latency --crop-right 0.02 --crop-bottom 0.04
```

如果需要分析跟踪过程：

```bash
uv run scripts/normalize_screen.py inputs/my_screen_video.mp4 --tracker reference --reference-profile low-latency --write-tracker-debug --run-name debug_tracker
```

这会生成：

```text
runs/debug_tracker/tracker_debug.csv
```

## 关键参数

| 参数 | 作用 |
| --- | --- |
| `--tracker reference` | 推荐模式。把屏幕平面锁定到首帧参考平面，再用光流和 RANSAC 跟踪。 |
| `--reference-profile low-latency` | 适合静态或近静态屏幕内容，减少平滑滞后。 |
| `--reference-profile dynamic` | 适合内部内容变化更大的实验输入，但不作为当前静态主线默认方案。 |
| `--corners "x,y:x,y:x,y:x,y"` | 手动指定四个屏幕角点，覆盖自动检测。 |
| `--crop-left/top/right/bottom` | 透视矫正后按比例裁切输出画面。 |
| `--width`, `--height` | 设置输出分辨率，默认 `1920x1080`。 |
| `--run-name` | 固定本次运行的输出目录名。 |
| `--write-tracker-debug` | 输出每帧跟踪诊断信息。 |

## 稳定性评估

用 `scripts/analyze_stability.py` 分析输出视频中相邻帧的残余运动：

```bash
uv run scripts/analyze_stability.py runs/stage1_test/my_screen_video_normalized.mp4 --run-name analyze_stage1_test
```

它会生成：

```text
runs/analyze_stage1_test/stability_metrics.csv
runs/analyze_stage1_test/stability_summary.json
```

报告里可以重点使用这些指标：

- 残余平移量；
- 残余旋转角；
- 残余尺度变化；
- RANSAC 内点数量和内点比例；
- 最后几秒的稳定性统计。

这些指标不能完全代替主观视觉效果，但可以支持方法对比和消融实验。

## 目录结构

```text
.
├── README.md
├── doc/          # 论文、路线分析和方法笔记
├── inputs/       # 本地输入视频，默认不提交到 git
├── reference/    # 课程 proposal/final 模板和示例
├── runs/         # 每次运行生成的结果，默认不提交到 git
├── scripts/      # 视频处理和分析脚本
└── test/         # 预留测试目录
```

根目录只保留文件夹、`.gitignore` 和 `README.md`。输入视频和实验结果不要散落在根目录。

## 参考材料

- `reference/`：课程 proposal、cover letter、final report 和 presentation 示例。
- `doc/`：当前阅读和保存的相关论文，包括视频稳定、单应性估计、线段检测、消失点和相机路径平滑等方向。
- `doc/stabilization-roadmap.md`：从稳定化目标、失败原因、实验结果到后续路线的详细分析。
- `doc/fpanet-deployment.md`：FPANet CUDA 部署、数据集、权重和测试说明。

## 后续工作

下一步建议按课程交付顺序做：

1. 固定第一阶段实验集，选择 3-5 个拍屏幕视频作为样例。
2. 对每个样例保存原视频、阶段一输出、debug CSV 和稳定性指标。
3. 截图展示自动角点、手动角点、透视矫正前后对比。
4. 开始第二阶段摩尔纹建模，先实现传统频域 baseline，再训练轻量模型。
5. 在 final report 中把阶段一作为几何校正模块，把阶段二作为图像恢复模块。
