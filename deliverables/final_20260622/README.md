# Final Deliverable Pack

本目录整理 final submission 可以直接引用的材料。

## 文件

| 文件 | 用途 |
| --- | --- |
| `final_report.md` | 英文 final report 初稿，按课程示例的 paper/report 风格组织 |
| `experiment_summary.csv` | 所有 final 实验的指标表，可复制到报告或 PPT |
| `run_manifest.md` | 每个数字对应的 `uv run` 命令、run 目录和分析目录 |
| `final_presentation_outline.md` | 8-10 页 final presentation 结构 |

本机另有 `runs/final_visuals/`，里面放了 `static_*`、`scroll_*`、`screenvideo_*`、`testmoire_*` 的 input/reference 关键帧。截图是本地 evidence，不提交到 git。

## 最重要的结论

1. 项目定位是“真实拍屏视频恢复的前置几何链路”，不是完整去摩尔纹模型。
2. 静态网页样例中，reference tracking 把 last-2s translation p95 从 detect 的 1.423 px 降到 0.078 px。
3. 滚动网页和屏幕内视频说明动态内容会影响普通光流和残余运动指标，因此要结合 tracker debug 解释。
4. `testmoire.mp4` 是明确失败边界：4K 摩尔纹导致可靠 reference points 几乎消失，适合放在 failure analysis。

## 提交建议

最终提交时建议把 `final_report.md` 转成 PDF，并在 PPT 中放：

- 原始视频关键帧；
- normalized 输出关键帧；
- 三视频消融表；
- 4K moire failure case；
- 应用链路图。

视频和 `runs/` 结果默认不进 git，但本机已经有对应目录。报告中的每个 run 名都可以在 `runs/` 下找到。
