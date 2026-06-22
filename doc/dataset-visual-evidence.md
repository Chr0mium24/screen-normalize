# 公开 demoiréing 数据集视觉证据

## 结论

不建议写成“这些数据集都没有直接拍屏”。更准确、更不容易被质疑的说法是：

> LCDMoire、UHDM、VDmoire 和 RawVDemoiré 都证明了拍屏去摩尔纹是一个真实且重要的恢复问题；但它们的 benchmark 输入通常已经被合成、裁剪、配对、对齐或受控采集，评估重点是 moiré-to-clean 的图像/视频恢复。真实应用中，手机首先拿到的是包含背景、屏幕边框、透视倾斜和手持抖动的完整拍屏视频，因此还需要本项目处理的前置步骤：屏幕定位、透视归一化和时域稳定。

如果做 proposal 或答辩图，最有说服力的排法是：左侧放这些公开数据集的官方样例或采集/对齐流程图，右侧放本项目自己的原始输入帧，例如 `deliverables/proposal_20260622/assets/input_frame_4s.jpg` 和归一化结果。这样能直接说明“它们从已配对/已对齐恢复开始，我们补的是恢复之前的几何前处理”。

## 推荐图源

| 数据集 | 推荐使用的官方图 | 图能说明什么 | 建议配文 |
| --- | --- | --- | --- |
| LCDMoire / AIM 2019 | Figure 3: https://ar5iv.labs.arxiv.org/html/1911.02498/assets/x4.png<br>Figure 2 pipeline: https://ar5iv.labs.arxiv.org/html/1911.02498/assets/x3.png | 这是 synthetic image pairs；样例展示 clean、moire 和 moire pattern，而不是完整手机拍摄场景视频。论文也写明最后会 align clean image with moire image and crop out the image pair。 | “Synthetic paired image benchmark: clean/moiré crops, not full captured-screen video stabilization.” |
| UHDM | Dataset overview: https://xinyu-andy.github.io/uhdm-page/images/dataset.png<br>Moiré sample: https://xinyu-andy.github.io/uhdm-page/images/uhdm/moire/0225_moire.jpg<br>Result sample: https://xinyu-andy.github.io/uhdm-page/images/uhdm/ours/test_0225_moire.jpg | UHDM 是更真实的 4K 拍屏图像对，但任务仍然是 image demoiréing benchmark。项目页说明默认 benchmark 会处理 center-cropped 4K images；它不是从任意完整手持视频中检测屏幕并稳定。 | “Real 4K image pairs for demoiréing; closer to real capture, but still image restoration rather than screen-plane tracking.” |
| CVPR 2022 Video Demoiréing / VDmoire | Dataset pipeline: https://daipengwa.github.io/VDmoire_ProjectPage/images/pipeline.png<br>Video comparison: https://daipengwa.github.io/VDmoire_ProjectPage/images/vdmoire.gif | 这是最接近视频的对比对象，但项目页明确写了 data collection pipeline 保证 spatial/temporal alignment；Data_v1 中 input moire frames 和 clean frames 用 homography matrix 对齐，Data_v2 又用 RAFT optical flow 细化。 | “Hand-held video demoiréing dataset, but the benchmark provides aligned moiré/clean frame pairs.” |
| RawVDemoiré | Dataset image: https://github.com/tju-chengyijia/VD_raw/raw/main/imgs/dataset_show.png<br>Video results: https://github.com/tju-chengyijia/VD_raw/raw/main/imgs/sota_video.png<br>Image results: https://github.com/tju-chengyijia/VD_raw/raw/main/imgs/sota_img.png | 论文强调 well-aligned raw video demoiréing dataset；仓库说明数据被整理成 `gt_raw`、`gt_rgb`、`moire_raw`、`moire_rgb` 四类帧。它适合证明“对齐后的 raw/sRGB 恢复”很重要，但不是完整场景几何归一化任务。 | “Well-aligned raw/sRGB moiré and ground-truth frames for restoration after acquisition/alignment.” |

## 建议放进报告的对比句

中文：

> 公开拍屏去摩尔纹数据集通常把问题定义为已裁剪、已配对或已对齐的 moiré-to-clean 恢复任务。例如 LCDMoire 是合成图像对，UHDM 是 4K 图像对，VDmoire 通过 homography/RAFT 保证视频帧对齐，RawVDemoiré 则构建 well-aligned raw/sRGB 帧对。相比之下，本项目处理的是更前面的真实应用输入：包含屏幕外背景、透视倾斜和手持抖动的完整拍屏视频，并输出稳定的屏幕坐标系视频，供后续 demoiréing、OCR 或归档使用。

英文：

> Public captured-screen demoiréing datasets usually formulate the task as cropped, paired, or aligned moiré-to-clean restoration. LCDMoire is a synthetic paired-image benchmark, UHDM provides 4K image pairs, VDmoire aligns moiré and clean video frames with homography and optical flow refinement, and RawVDemoiré provides well-aligned raw/sRGB frame pairs. Our project targets the preceding application step: converting a full phone-captured screen video with background, perspective distortion, and hand shake into a rectified and temporally stable screen-coordinate video for downstream restoration.

## 图像使用提醒

这些图片来自论文项目页或官方仓库。放进课程报告/PPT 时应在图注里标明数据集和来源链接；如果不确定授权，优先使用网页链接或截图加引用，不要把原图无说明地混入本项目自有实验结果。RawVDemoiré 仓库还明确说明数据集面向 academic purpose，并采用 CC BY-NC-SA 4.0 相关许可。
