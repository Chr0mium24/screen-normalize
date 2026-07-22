# 4.5 频域信号保持实验缺口分析

日期：2026-07-22

## 结论

如果第 4.5 节采用基于峰集合的 **Moiré Spectral Preservation Score (MSPS)**，当前项目还不能直接产出实测结果。现有代码已经能做 reference-based 频域诊断，但它比较的是整体 FFT 结构、能量比和方向直方图，还没有实现“检测摩尔纹峰 -> 峰属性提取 -> Hungarian Matching -> 综合保真分数”的流程。

因此，现在缺两类东西：

1. 数据上缺少可稳定检测摩尔纹峰的成组样本，以及每帧原始区域、追踪输出、几何变换之间的可追溯记录。
2. 代码上缺少 MSPS 的峰检测、峰属性、峰集合匹配、异常峰统计、批处理输出和论文图表生成模块。

## 当前已有基础

项目已有下列相关基础，可以复用：

| 类型 | 文件 | 现状 |
|---|---|---|
| 全局频域保持指标 | `screen_normalize/metrics/frequency_preservation.py` | 已实现 log-FFT 相似度、高频能量比、方向直方图相似度、宽频带能量比 |
| 频域规则性诊断 | `screen_normalize/metrics/frequency.py`、`screen_normalize/experiments/evaluation.py` | 已能在单个 normalized video 上检测频谱主方向、正交性和轴对齐 |
| 频域 demo 结果 | `doc/current/paper/frequency_preservation_demo_2026-07-14.md` | 已在 `scrolling_01` 的 4 个标注帧上跑通过 reference-based FFT 诊断 |
| 4.5 算法设想 | `doc/current/paper/revision_logs/2026-07-19-signal-preservation-diagnostic-implementation-plan.md` | 已提出三元输入 `(R_t_raw, R_t_track, T_t)` 和几何补偿方向 |
| 论文占位正文 | `doc/current/paper/manuscript/paper_zh_v3.md` | 第 4.5 节已有设计性描述，但不是完整实测结果 |

已有指标适合作为 baseline diagnostic，但不能替代 MSPS。原因是它仍然依赖区域级 FFT 分布，对峰轻微平移、旋转和尺度变化不够稳健。

## 现在差什么数据

### 1. 明显摩尔纹样本

需要采集或筛选屏幕拍摄视频，要求肉眼和 FFT 中都能看到稳定摩尔纹峰。建议至少包含：

| 场景 | 最低数量 | 用途 |
|---|---:|---|
| 静止屏幕、静止相机 | 1 段 | 建立 MSPS 上限和重复性基线 |
| 轻微手持抖动 | 1 段 | 检查稳定/追踪是否引入新峰或峰宽扩散 |
| 屏幕平移或相机平移 | 1 段 | 检查峰位置在补偿后是否保持 |
| 屏幕旋转或相机绕光轴旋转 | 1 段 | 检查峰方向补偿 |
| 远近变化或缩放变化 | 1 段 | 检查峰半径随尺度反比变化 |
| 弱边界或透视变化 | 1 段 | 检查真实困难条件下 MSPS 是否下降 |

最小可交付版本可以先用 2 段视频：静止基线 + 当前论文代表性滚动/弱边界片段。但如果要把第 4.5 写成有说服力的实验证据，建议至少 5 到 6 段。

### 2. 每帧 reference 输入

MSPS 需要逐帧比较“真实追踪输出”和“原始拍屏信号中对应区域”。每个采样帧至少要保存：

```text
frame_000123_raw_region.png
frame_000123_tracked.png
frame_000123_transform.json
```

`raw_region` 不是整张原始帧，而是原始帧中屏幕目标对应区域。`tracked` 是当前真实管线输出，不能为了实验单独关闭裁剪、缩放、透视矫正或稳定。

### 3. 几何变换记录

每个采样帧必须能追溯从原始区域到追踪输出的几何关系。最低要求：

```json
{
  "frame_index": 123,
  "timestamp_sec": 4.1,
  "raw_region_corners": [[x1, y1], [x2, y2], [x3, y3], [x4, y4]],
  "tracked_size": [width, height],
  "homography_raw_to_track": [[...], [...], [...]]
}
```

如果代码暂时不能直接导出完整 homography，也至少要导出：

| 字段 | 原因 |
|---|---|
| `raw_region_corners` | 用来把原始帧 warp 到追踪输出坐标系 |
| `tracked_size` | 保证 FFT 采样网格一致 |
| `scale` 或局部尺度估计 | 预测频谱半径变化 |
| `rotation_deg` 或局部方向估计 | 预测频谱方向变化 |
| `method_id` | 区分 `frame_wise`、`optical_flow`、`proposal_border` |

### 4. 人工核验标注

至少要有一个小型人工核验表，用来确认采样帧中是否真的存在可见摩尔纹峰：

```text
clip_id,frame,moire_visible,peak_count_expected,usable,notes
scrolling_01,148,yes,2,yes,"two symmetric diagonal peaks"
```

这不是为了训练算法，而是为了避免把普通文本边缘、屏幕内容纹理或压缩噪声误当作摩尔纹峰。

### 5. 负样本

需要 1 到 2 段弱摩尔纹或无明显摩尔纹样本。用途是检验 MSPS 的 `status` 逻辑：当 reference 中没有稳定峰时，结果应标记为 `skipped/no_stable_reference_peaks`，不能硬算一个看似精确的分数。

## 现在差什么代码实现

### 1. 新建诊断模块

建议新建：

```text
screen_normalize/diagnostics/spectral_peaks.py
screen_normalize/diagnostics/moire_msps.py
```

`spectral_peaks.py` 负责通用峰检测和峰属性提取；`moire_msps.py` 负责 reference/track 对比和 MSPS 计算。这样能避免继续把新逻辑塞进已有 `metrics/frequency_preservation.py`，也能控制单文件长度。

### 2. 峰检测函数

需要实现：

```python
detect_spectral_peaks(image, config) -> list[SpectralPeak]
```

每个峰至少包含：

```python
SpectralPeak(
    x: float,
    y: float,
    radius: float,
    angle_deg: float,
    energy: float,
    width_px: float,
    prominence: float,
)
```

关键实现点：

| 项目 | 要求 |
|---|---|
| 灰度化 | 与现有频域代码一致，使用 float32 |
| 窗函数 | 使用 Hanning window 降低边界泄漏 |
| DC 屏蔽 | 屏蔽中心低频区域 |
| 局部极大值 | 用 dilation 或 connected components 找峰 |
| 峰能量 | 取局部窗口内 power sum，而不是单像素值 |
| 峰宽 | 用局部二阶矩或半高宽估计 |
| 对称峰处理 | FFT 实图像会产生中心对称峰，需要合并或成对记录 |

### 3. 峰集合匹配

需要实现：

```python
match_peak_sets(reference_peaks, tracked_peaks, config) -> PeakMatchResult
```

匹配代价建议包含：

```text
cost = wp * normalized_position_distance
     + wa * normalized_angle_distance
     + we * abs(log(energy_track / energy_ref))
     + ww * abs(width_track - width_ref) / width_ref
```

注意：当前 `pyproject.toml` 没有 `scipy`。如果使用真正的 Hungarian Matching，有两个选择：

| 方案 | 代价 |
|---|---|
| 添加 `scipy>=1.14` 并使用 `scipy.optimize.linear_sum_assignment` | 实现最稳，依赖增加 |
| 不加依赖，实现小规模峰集合的穷举/动态规划匹配 | 依赖少，但需要限制峰数量，例如最多 8 到 12 个峰 |

建议先加 `scipy`，因为这是论文实验代码，Hungarian Matching 是标准实现，风险低。

### 4. 几何补偿

需要实现：

```python
predict_tracked_peak(reference_peak, transform) -> PredictedPeak
```

最低版本可以先在图像中心附近用 homography 的局部 Jacobian 近似仿射变换，得到频域中的方向和尺度变化。对于 2D 仿射矩阵 `A`，空间坐标变换为：

```text
x_track = A x_raw
```

频率坐标按逆转置变换：

```text
f_track ∝ A^{-T} f_raw
```

这一步是第 4.5 的关键。如果没有几何补偿，MSPS 仍会把真实缩放/旋转误判成频谱破坏。

### 5. MSPS 指标计算

需要实现逐帧输出：

```text
matched_peak_count
missing_peak_count
new_peak_count
mean_position_error_px
mean_frequency_radius_error
mean_angle_error_deg
mean_energy_delta_db
mean_width_relative_error
msps
status
reason
```

分数建议写成距离惩罚形式：

```text
MSPS = clamp(1 - (
  alpha * d_position
  + beta * d_energy
  + gamma * d_width
  + delta * new_peak_rate
  + eta * missing_peak_rate
), 0, 1)
```

这里应使用加号累积惩罚，而不是减号。`d_position` 也应使用欧氏距离：

```text
d_p = sqrt((x_ref - x_track)^2 + (y_ref - y_track)^2)
```

如果沿用 `1 - (alpha d_p - beta d_E - ...)`，能量误差越大反而可能提高分数，符号不合理。

### 6. 批处理入口

建议新增：

```text
scripts/diagnostics/run_moire_msps.py
```

输入：

```text
uv run python scripts/diagnostics/run_moire_msps.py \
  --input-dir runs/<run_id>/diagnostic_inputs \
  --output-dir runs/<run_id>/moire_msps
```

输出：

```text
moire_msps_rows.csv
moire_msps_summary.csv
moire_msps_summary.json
figures/<clip_id>_<frame>_peaks.png
```

### 7. 数据导出脚本

建议新增：

```text
scripts/diagnostics/export_moire_msps_inputs.py
```

职责：

1. 读取原始视频、归一化结果和调试轨迹。
2. 按采样帧导出 `raw_region`、`tracked` 和 `transform.json`。
3. 保证所有方法的输出尺寸一致。
4. 保存 manifest，记录每帧是否导出成功。

### 8. 论文图表生成

建议新增或扩展：

```text
scripts/paper/build_signal_preservation_figure.py
```

图 6 应至少包含：

| 面板 | 内容 |
|---|---|
| A | 原始区域、追踪输出、reference/track FFT |
| B | reference peaks 与 tracked peaks 的匹配连线 |
| C | MSPS、位置误差、能量变化、峰宽变化的条形图 |
| D | 新峰/丢峰案例帧 |

论文表格建议放：

```text
doc/current/paper/results/moire_msps/
```

如果保持当前结构，也可以先放在：

```text
runs/<run_id>/moire_msps/
```

再由 `scripts/paper/` 复制或汇总到 manuscript figures。

### 9. 单元测试和合成验证

需要新增：

```text
tests/test_moire_msps.py
```

最低测试：

| 测试 | 预期 |
|---|---|
| 相同正弦条纹图 | MSPS 接近 1 |
| 峰平移 1 到 2 px | 匹配后位置误差小，不产生大量新峰 |
| 人工旋转图像 | 几何补偿后方向误差下降 |
| 人工缩放图像 | 几何补偿后半径误差下降 |
| 模糊图像 | 能量下降、峰宽变大 |
| 新增周期条纹 | `new_peak_count > 0`，MSPS 下降 |
| 无稳定峰图像 | `status = skipped` |

## 推荐实施顺序

1. 固化数据协议：定义 `diagnostic_inputs/manifest.csv` 和 `transform.json` schema。
2. 实现合成图上的 `detect_spectral_peaks`，先不接真实视频。
3. 实现小规模 Hungarian Matching 和 MSPS，跑通单元测试。
4. 实现 homography 局部 Jacobian 的频域补偿。
5. 写 `export_moire_msps_inputs.py`，从现有 run 中导出真实三元输入。
6. 写 `run_moire_msps.py`，产出逐帧 CSV、汇总 CSV/JSON、峰匹配可视化。
7. 在 1 个静止基线和 1 个代表性片段上 smoke test。
8. 扩展到 5 到 6 类场景，生成第 4.5 实验表和图 6。
9. 更新 `paper_zh_v3.md`：把当前设计性文字替换为实测结果，同时保留“不衡量去摩尔纹，只衡量拍屏信号保持”的边界。

## 第 4.5 能写到什么程度

在完成上述实现前，第 4.5 只能写成“指标设计与实验协议”，不能写成完整结果。可以安全表述：

```text
本文设计 MSPS 作为频域信号保持诊断，避免直接比较 FFT 像素差值造成的峰位移敏感问题。该指标检测 reference 与 tracking output 的摩尔纹峰集合，并在几何补偿后比较峰位置、能量、峰宽和新增峰。
```

完成真实数据和代码后，才能写：

```text
在 N 段视频、M 个采样帧上，Proposed 的 MSPS 中位数为 ...，新增峰率为 ...，能量变化为 ... dB。
```

## 最小可交付版本

如果时间有限，建议先做 MVP：

| 项目 | MVP 选择 |
|---|---|
| 数据 | `scrolling_01` + 1 段静止摩尔纹基线 |
| 峰数量 | 每帧最多保留 8 个 reference peaks 和 12 个 tracked peaks |
| 匹配 | 使用 `scipy.optimize.linear_sum_assignment` |
| 几何补偿 | 先用中心局部仿射近似 |
| 输出 | `moire_msps_rows.csv`、`moire_msps_summary.csv`、3 到 5 张峰匹配可视化 |
| 论文 | 第 4.5 写成 preliminary diagnostic，不作为主排名指标 |

这个 MVP 足够证明 MSPS 方案可运行，也能指出现有 FFT 全图比较的不足；但还不足以作为强结论证明“算法完全保持摩尔纹”。

