<h1>面向真实场景拍屏视频恢复的屏幕捕获矫正与时域稳定化</h1>

<p class="meta"><strong>Group ID:</strong> TODO &nbsp; | &nbsp; <strong>成员:</strong> 温镕硕 Rongshuo Wen (Leader, 124020369), 温璧华 Bihua Wen (124090670), 刘明睿 Ruiming Liu (124090375)</p>

<div class="abstract">
  <strong>问题背景。</strong> 现有拍屏去摩尔纹数据集证明了屏幕恢复需求真实存在，但它们通常面向受控采集、裁剪、配对或已经时空对齐的屏幕内容。真实手机拍屏视频还包含屏幕外背景、透视倾斜、手持晃动、弱边框和屏幕内部动态内容。本项目关注的正是进入去摩尔纹、OCR 或归档之前缺失的前置几何归一化链路。
</div>

<div class="grid">
<div class="card">

## 任务与目标

输入是一段完整手机拍电脑屏幕的视频。输出是一段固定比例、正面视角、时域稳定的屏幕内容视频。目标是尽量去除屏幕外背景，校正透视变形，降低帧间抖动，并为后续 video demoiréing、OCR 或归档提供稳定的屏幕坐标系输入。

</div>
<div class="card">

## 方法

- 首帧自动检测或手动指定屏幕四角点。
- 用 homography 将屏幕透视矫正到 16:9 画布。
- 在参考平面上使用 Lucas-Kanade 光流跟踪特征点。
- 通过 RANSAC 和几何门控拒绝不可靠更新。
- 对轨迹插值和平滑，并用残余运动指标评价稳定性。

</div>
<div class="card">

## 数据计划

Final 阶段计划自采测试集：**5 类场景 x 每类 10 段 x 每段约 5 秒**。场景包括静态网页/文档、滚动网页、屏幕内播放视频、PPT 或弱边框低纹理页面，以及 4K/摩尔纹/反光难例。公开 demoiréing 数据集作为相关工作证据，而不是直接作为本前置对齐任务的主 benchmark。

</div>
<div class="card">

## 评价指标

评价脚本估计归一化后相邻帧之间的残余仿射运动。主要指标包括 residual translation p95、residual rotation p95 和 residual scale-delta p95。Tracker accept ratio、RANSAC inliers、inlier ratio 和 feature coverage 用于解释失败原因。残余运动越低，说明输出视频越稳定。

</div>
<div class="card wide">

## 初步实验

当前使用一段本地 1920x1080、317 帧的拍屏视频做同视频消融。下表衡量归一化输出中的残余帧间运动，不等价于有 ground truth 的重建误差。

| 方法 | 最后 2 秒平移 p95 | 最后 2 秒旋转 p95 | 解释 |
| --- | ---: | ---: | --- |
| 逐帧检测角点 | 1.927 px | 0.0425 deg | 抖动基线 |
| 普通光流跟踪 | 1.929 px | 0.0263 deg | 旋转略低，但仍不稳定 |
| 参考平面跟踪 | <span class="best">0.118 px</span> | <span class="best">0.0044 deg</span> | 残余稳定性最好 |

</div>
<div class="card wide">

## 预期结果与计划

预期结果是一个传统几何视觉前处理链路，将真实拍屏视频转换为稳定、拉正、接近录屏视角的屏幕坐标系视频。Proposal 阶段已经确定应用叙事，实现核心归一化流程，并完成初步消融。Final 阶段将补齐 50 段自采测试集、方法消融、角点和跟踪可视化，以及成功和失败场景分析。

</div>
</div>

<p class="footer">源文件和证据保存在 deliverables/proposal_20260622/。当前草稿保留 Group ID 占位，拿到正式组号后再替换。</p>
