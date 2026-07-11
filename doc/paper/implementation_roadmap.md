# Result-driven Implementation Roadmap

本路线图以 `outline_zh.md` 和 `figure_plan.md` 中的最终论文为验收目标，从结果反推数据、实现和实验。

## 1. Dataset and Metadata

**最终结果：** Figure 2 和 Dataset 章节。

- 采集 50 个约 5 秒视频，5 类场景各 10 个。
- 由代码自动读取 clip ID、场景类别、分辨率、帧率和时长。
- 固定训练/调参与最终评估的数据边界，避免通过测试集选参。
- 生成类别分布、基础视频统计、类别示例和角点标注示例。
- 不维护设备、光照、拍摄角度或场景难度字段；这些因素只在人工定性分析中讨论。

## 2. Ground-truth Annotation

**最终结果：** corner error、quadrilateral IoU 和 aspect-ratio error。

- 定义 CSV/JSON schema：clip、frame、TL/TR/BR/BL 角点和标注状态。
- 为每类规定一致的关键帧抽样策略。
- 完成角点标注工具的导入、校验、修改和可视化功能。
- 对重复标注子集报告标注一致性或复核流程。

## 3. Proposal-complete Main Method

**最终结果：** Figure 1、主方法行和内容运动鲁棒性结论。

- 完成 edge filtering 与 LSD/Hough 物理边框检测。
- 定义四边组合、交点、几何有效性和 border confidence。
- 以边框运动为屏幕平面主证据，将 LK 内部特征用于一致性检查。
- 用 RANSAC、inlier ratio、角点偏差和覆盖率区分屏幕运动与内容运动。
- 实现低置信重检测、上一有效 homography 冻结、轨迹修复和时间平滑。
- 为 consistency check、failure recovery 和 temporal smoothing 增加独立消融开关。

## 4. Baselines and Reproducibility

**最终结果：** 三方法主表和 Figure 3–5。

- 固定 frame-wise detection、content optical flow 和 border-guided proposed method 的定义。
- 所有方法使用同一输入、目标画布、标注帧和评估代码。
- 保存每个 run 的命令、Git commit、参数、输出和评估 CSV/JSON。
- 添加阶段级计时，记录 CPU/GPU、视频分辨率和帧率。

## 5. Evaluation Dimensions

**最终结果：** 定量主表、Figure 4、6 和 supplementary metrics。

- **Geometry:** corner error、quadrilateral IoU、aspect-ratio error。
- **Temporal:** 平移、旋转和缩放变化；动态内容场景使用屏幕固定区域或标注几何避免内容运动污染。
- **Detail:** 在同一屏幕坐标和尺度上计算 average gradient magnitude 与 edge preservation index。
- **Frequency:** 对规则网格或高频伪影场景报告 2D FFT 主方向、正交误差和重采样前后的频谱变化，不宣称摩尔纹抑制。
- 指标实现先通过合成变换和自一致样例测试，再运行全数据集。

## 6. Figures, Tables, and Writing

**最终结果：** `figure_plan.md` 中的全部主图和表格。

- 每个 `TBD-*` 结果槽位必须映射到一个可复现的 CSV/JSON 字段。
- 图表只从结构化实验输出生成，不手工录入结果。
- 先完成 Results 的图表、caption 和结论，再写 Abstract 和 Discussion。
- 最终稿附 Data Availability、Code Availability、局限性和失败案例。

## Completion Gate

只有同时满足以下条件，才将最终论文视为完成：

1. 50 个视频、自动基础统计和类别归属完整。
2. 角点标注和质量复核完成。
3. 三种方法和三个核心模块消融在完整数据集上运行。
4. 几何、时域、细节和频域指标均有真实可追溯结果。
5. 全部 `TBD-*` 槽位由实验生成值替换，且图表、正文和附件数字一致。
