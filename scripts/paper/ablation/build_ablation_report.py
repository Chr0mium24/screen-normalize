#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


METHOD_LABELS = {
    "proposed": "Full",
    "no_reliability_gates": "w/o reliability gates",
    "no_trajectory_smoothing": "w/o trajectory smoothing",
    "no_offline_repair": "w/o offline repair",
}
METHOD_ORDER = list(METHOD_LABELS)
CATEGORIES = ("static", "scrolling", "screen_video", "hard")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def number(value: object, digits: int = 3) -> str:
    if value is None or str(value) == "":
        return "—"
    return f"{float(value):.{digits}f}"


def tracker_percent(value: object) -> str:
    if value is None or str(value) == "":
        return "—"
    return f"{float(value) * 100:.1f}%"


def markdown_metric_table(rows: list[dict[str, str]]) -> str:
    lines = [
        "| 类别 | 变体 | Corner RMSE (px) ↓ | Quad IoU ↑ | Translation (px) ↓ | Edge preservation ↑ | Tracker 接受率 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    ordered = sorted(rows, key=lambda row: (row["category"], METHOD_ORDER.index(row["method"])))
    for row in ordered:
        lines.append(
            "| {category} | {label} | {rmse} | {iou} | {translation} | {edge} | {acceptance} |".format(
                category=row["category"],
                label=METHOD_LABELS[row["method"]],
                rmse=number(row.get("corner_rmse_px")),
                iou=number(row.get("quad_iou")),
                translation=number(row.get("translation_px")),
                edge=number(row.get("edge_preservation_index")),
                acceptance=tracker_percent(row.get("tracker_accept_ratio")),
            )
        )
    return "\n".join(lines)


def markdown_aggregate_table(rows: list[dict[str, str]]) -> str:
    lines = [
        "| 变体 | n | RMSE 中位数 [IQR] | IoU 中位数 [IQR] | Translation 中位数 [IQR] | Edge 中位数 [IQR] |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {label} | {n} | {rmse} [{rmse_iqr}] | {iou} [{iou_iqr}] | {translation} [{translation_iqr}] | {edge} [{edge_iqr}] |".format(
                label=METHOD_LABELS[row["method"]],
                n=row["n_clips"],
                rmse=number(row.get("corner_rmse_px_median")),
                rmse_iqr=number(row.get("corner_rmse_px_iqr")),
                iou=number(row.get("quad_iou_median")),
                iou_iqr=number(row.get("quad_iou_iqr")),
                translation=number(row.get("translation_px_median")),
                translation_iqr=number(row.get("translation_px_iqr")),
                edge=number(row.get("edge_preservation_index_median")),
                edge_iqr=number(row.get("edge_preservation_index_iqr")),
            )
        )
    return "\n".join(lines)


def markdown_issue_table(issues: list[dict]) -> str:
    lines = [
        "| 严重度 | 类别/clip | 检查 | 结论 |",
        "| --- | --- | --- | --- |",
    ]
    for issue in issues:
        lines.append(
            f"| {issue['severity']} | {issue['category']}/{issue['clip_id']} | "
            f"{issue['check']} | {issue['message']} |"
        )
    return "\n".join(lines)


def acceptance_rows(clip_rows: list[dict[str, str]]) -> list[dict[str, float | str]]:
    output: list[dict[str, float | str]] = []
    for category in CATEGORIES:
        row: dict[str, float | str] = {"category": category}
        for method in METHOD_ORDER:
            match = next(
                item for item in clip_rows if item["category"] == category and item["method"] == method
            )
            row[method] = float(match["tracker_accept_ratio"])
        output.append(row)
    return output


def acceptance_sql(rows: list[dict[str, float | str]]) -> str:
    values = ",".join(
        "('{category}',{proposed},{no_reliability_gates},{no_trajectory_smoothing},{no_offline_repair})".format(
            **row
        )
        for row in rows
    )
    return (
        f"SELECT * FROM (VALUES {values}) AS "
        "t(category,proposed,no_reliability_gates,no_trajectory_smoothing,no_offline_repair);"
    )


def build_artifact(results_dir: Path) -> dict:
    clip_rows = read_csv(results_dir / "ablation_clip_metrics.csv")
    summary_rows = read_csv(results_dir / "ablation_table.csv")
    quality = json.loads((results_dir / "ablation_quality.json").read_text(encoding="utf-8"))
    integrity_rows = read_csv(results_dir / "video_integrity.csv")

    issues = quality.get("issues", [])
    high_issues = sum(issue.get("severity") == "high" for issue in issues)
    medium_issues = sum(issue.get("severity") == "medium" for issue in issues)
    tbd_zh = quality["manuscript_gaps"]["manuscripts"]["paper_zh.md"]["tbd_tokens"]
    tbd_en = quality["manuscript_gaps"]["manuscripts"]["paper_en.md"]["tbd_tokens"]
    valid_videos = sum(row.get("frame_match") == "True" for row in integrity_rows)
    acceptance = acceptance_rows(clip_rows)

    sources = [
        {
            "id": "ablation-metrics",
            "label": "四类单 clip 消融指标",
            "type": "file",
            "path": "doc/archive/paper_results/2026-07-14-first-pass/results/ablation/ablation_clip_metrics.csv",
            "description": "四个代表 clip、full 与三个去模块变体的当前口径指标；geometry 排除初始化帧。",
        },
        {
            "id": "ablation-quality",
            "label": "消融数据质量与实验有效性检查",
            "type": "file",
            "path": "doc/archive/paper_results/2026-07-14-first-pass/results/ablation/ablation_quality.json",
            "description": "输出完整性、模块触发、几何失败、非确定性、样本量和论文占位项检查。",
        },
        {
            "id": "video-integrity",
            "label": "输出视频完整性检查",
            "type": "file",
            "path": "doc/archive/paper_results/2026-07-14-first-pass/results/ablation/video_integrity.csv",
            "description": "ffprobe 视频帧数与 method.json processed_frames 的逐方法核对。",
        },
    ]

    metric_table = markdown_metric_table(clip_rows)
    aggregate_table = markdown_aggregate_table(summary_rows)
    issue_table = markdown_issue_table(issues)

    blocks = [
        {
            "id": "title",
            "type": "markdown",
            "body": "# 四类单 Clip 消融实验与论文数据缺口",
            "layout": "full",
        },
        {
            "id": "technical-summary",
            "type": "markdown",
            "sourceId": "ablation-quality",
            "body": (
                "## 技术结论\n\n"
                "- [x] 当前范围完成：static、scrolling、screen_video、hard 各 1 个 clip，3 个新增消融变体全部运行；weak_border 排除。\n"
                f"- [x] 16/16 个方法产物、64/64 个指标 JSON 均存在且状态正常；{valid_videos}/16 个输出视频帧数与方法记录一致。\n"
                f"- [!] 计算完整不等于实验结论有效：共识别 {high_issues} 个高严重度和 {medium_issues} 个中严重度问题。\n"
                "- [!] 现阶段只能报告 **4 个配对 clip 的描述性 pilot**，不能给出强显著性或总体泛化结论。"
            ),
            "layout": "full",
        },
        {
            "id": "findings",
            "type": "markdown",
            "sourceId": "ablation-metrics",
            "body": (
                "## 结果显示门控在困难视频上抑制抖动，但可能冻结错误轨迹\n\n"
                "**scrolling/full 的 RMSE 为 715.858 px、IoU 为 0.490；hard/full 的 RMSE 为 129.916 px。** "
                "hard/full 仅接受 2/348 帧，说明低时域变化来自长期冻结，不能单独解释为稳定成功。\n\n"
                "关闭 reliability gates 后，hard 的 RMSE 降到 89.516 px，但 translation 上升到 7.442 px；"
                "scrolling 的 RMSE 进一步恶化到 910.435 px，translation 上升到 9.011 px。"
                "该模块表现为几何更新与时域抖动之间的取舍，而不是四类一致改善。"
            ),
            "layout": "full",
        },
        {
            "id": "acceptance-explanation",
            "type": "markdown",
            "sourceId": "ablation-metrics",
            "body": (
                "## Tracker 接受率揭示了失败机制\n\n"
                "图中比较每个代表 clip 的接受帧比例。hard/full 与两个保留门控的变体只有约 0.6% 帧被接受；"
                "scrolling 为约 34.4%。关闭门控后接受率接近 100%，但时域抖动和部分几何误差增加，"
                "因此接受率本身不是越高越好。"
            ),
            "layout": "full",
        },
        {"id": "acceptance-chart-block", "type": "chart", "chartId": "acceptance-chart", "layout": "full"},
        {
            "id": "clip-table",
            "type": "markdown",
            "sourceId": "ablation-metrics",
            "body": (
                f"## 逐 Clip 精确结果\n\n{metric_table}\n\n"
                "指标均按当前代码重新计算；geometry 排除初始化帧。"
                "频域指标保留在逐方法 JSON 和明细 CSV 中，因其为诊断量，不进入 Figure 7 主表。"
            ),
            "layout": "full",
        },
        {
            "id": "aggregate-table",
            "type": "markdown",
            "sourceId": "ablation-metrics",
            "body": (
                f"## 四 Clip 描述性汇总\n\n{aggregate_table}\n\n"
                "IQR 很大，尤其 RMSE，说明四类异质性强。总体中位数不能替代逐类结果，也不应配显著性星号。"
            ),
            "layout": "full",
        },
        {
            "id": "validity",
            "type": "markdown",
            "sourceId": "ablation-quality",
            "body": f"## 影响论文结论的实验有效性问题\n\n{issue_table}",
            "layout": "full",
        },
        {
            "id": "scope-method",
            "type": "markdown",
            "body": (
                "## 范围与方法定义\n\n"
                "- 分析单位：每类 1 个代表 clip，共 4 个配对 clip。\n"
                "- 方法：full proposed、w/o reliability gates、w/o trajectory smoothing、w/o offline repair。\n"
                "- full：复用历史 normalized video 与 estimated corners，仅用当前指标代码重新计算；初始化帧统一排除。\n"
                "- 聚合：先按 clip 读取方法 JSON，再跨 4 个 clip 报告中位数与 IQR；不同长度视频不按帧数加权。\n"
                "- Frequency：仅作为几何归一化/重采样诊断，不作为去摩尔纹性能证据。"
            ),
            "layout": "full",
        },
        {
            "id": "paper-gaps",
            "type": "markdown",
            "sourceId": "ablation-quality",
            "body": (
                "## 论文数据现在还缺什么\n\n"
                "- [x] **消融运行数据：** 4 clip × 4 variants 已完成。\n"
                "- [x] **Figure 7 数值底表：** `ablation_table.csv` 和逐 clip 明细已生成。\n"
                "- [ ] **Offline repair 的有效触发证据：** 当前四个 clip 没有可插值的内部拒绝区间；"
                "应替换为能触发该模块的现有代表 clip，或在论文中将该消融标为 inconclusive/删除。\n"
                "- [ ] **可靠的总体统计：** n=4 只能做描述性 pilot；若不扩大样本，正文必须明确限制，不报告显著性。\n"
                "- [ ] **独立时域真值：** 当前 translation/rotation/scale 来自方法自身轨迹，不能独立证明物理稳定。\n"
                "- [ ] **失败案例证据：** scrolling 跟踪漂移、hard 长期冻结已经是候选，但仍需截图、debug 行和人工审核说明。\n"
                "- [ ] **其他真实图：** Fig. 1、2、3、4、5、6、8 仍为占位图；Figure 7 也还需要正式绘图替换占位 SVG。\n"
                "- [ ] **复现元数据：** 硬件、Python/OpenCV/NumPy/FFmpeg 版本、Git commit、耗时边界和成功判据。\n"
                f"- [ ] **稿件回填：** 中文稿仍有 {tbd_zh} 个 TBD token，英文稿有 {tbd_en} 个；两稿各引用 8 个占位图。"
            ),
            "layout": "full",
        },
        {
            "id": "next-steps",
            "type": "markdown",
            "body": (
                "## 建议下一步\n\n"
                "1. [ ] 人工打开 scrolling 和 hard 的四变体 HTML/视频，确认漂移与冻结的可见表现，并固定失败截图。\n"
                "2. [ ] 决定 offline repair：从现有数据中换一个能产生内部拒绝区间的代表 clip，或把该消融写成未触发、不得下结论。\n"
                "3. [ ] 用本报告数值生成正式 Figure 7，但图注必须写 `n=4 paired clips; descriptive pilot`。\n"
                "4. [ ] 回填中英文 6.5 节，并同步把 consistency/failure recovery 改成真实模块名称。"
            ),
            "layout": "full",
        },
        {
            "id": "further-questions",
            "type": "markdown",
            "body": (
                "## 仍需回答的问题\n\n"
                "- hard 的冻结是否视觉上优于关闭门控后的抖动，还是只是把错误位置保持稳定？\n"
                "- scrolling 在第 227 帧后停止接受更新，主要拒绝原因是什么？\n"
                "- screen_video 的小幅跨运行差异是否需要通过固定 OpenCV RNG seed 消除？"
            ),
            "layout": "full",
        },
    ]

    chart = {
        "id": "acceptance-chart",
        "title": "Tracker 接受率（每类一个代表 clip）",
        "description": "Full 与三个消融变体；比例 0-1。接受率描述更新行为，不直接等同于质量。",
        "showDescription": True,
        "type": "bar",
        "intent": "comparison",
        "question": "门控和其他模块如何改变四类代表 clip 的 tracker 接受率？",
        "rationale": "四个离散类别比较四个同尺度比例，分组柱状图能直接显示 hard/scrolling 的冻结行为。",
        "dataset": "acceptance-rates",
        "encodings": {
            "x": {"field": "category", "type": "nominal"},
            "y": {
                "fields": METHOD_ORDER,
                "type": "quantitative",
            },
        },
        "palette": {"kind": "categorical", "name": "blue-gold"},
        "legend": {"position": "bottom", "interactive": False, "sort": "spec", "title": "变体"},
        "labels": {"values": "all"},
        "source": {
            "id": "acceptance-query",
            "label": "四类消融 tracker 接受率查询",
            "type": "query",
            "query": {
                "language": "sql",
                "engine": "DuckDB",
                "description": "从已审核的逐 clip 消融明细中选择四类四变体 tracker 接受率。",
                "sql": acceptance_sql(acceptance),
                "filters": ["每类仅一个预定代表 clip", "weak_border 排除", "full 与三个真实消融配置"],
                "metric_definitions": {
                    "tracker_accept_ratio": "debug.csv 中 accepted=true 的行数除以 tracker 行数。"
                },
            },
        },
        "layout": "full",
    }

    return {
        "surface": "report",
        "manifest": {
            "version": 1,
            "title": "四类单 Clip 消融实验与论文数据缺口",
            "description": "四类各一个代表 clip；weak_border 排除；full 复用历史输出并按当前口径重算指标。",
            "generatedAt": "2026-07-13T23:30:00+08:00",
            "blocks": blocks,
            "cards": [],
            "charts": [chart],
            "tables": [],
            "sources": sources,
        },
        "snapshot": {
            "version": 1,
            "status": "ready",
            "generatedAt": "2026-07-13T23:30:00+08:00",
            "datasets": {"acceptance-rates": acceptance},
        },
        "sources": sources,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the four-clip ablation report artifact.")
    parser.add_argument("--results-dir", type=Path, default=Path("doc/archive/paper_results/2026-07-14-first-pass/results/ablation"))
    args = parser.parse_args()

    artifact = build_artifact(args.results_dir)
    target = args.results_dir / "ablation_report_artifact.json"
    target.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
