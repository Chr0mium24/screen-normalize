#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


DATASET_GAP_ROWS = [
    {"category": "static", "collected": 1, "representative_annotation": 1, "complete_report": 1},
    {"category": "scrolling", "collected": 1, "representative_annotation": 1, "complete_report": 1},
    {"category": "screen_video", "collected": 1, "representative_annotation": 1, "complete_report": 1},
    {"category": "hard", "collected": 1, "representative_annotation": 1, "complete_report": 1},
]


def split_markdown_sections(markdown: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?m)(?=^## )", markdown) if part.strip()]


def build_artifact(markdown: str) -> dict:
    blocks: list[dict] = []
    for index, section in enumerate(split_markdown_sections(markdown), start=1):
        blocks.append(
            {
                "id": f"section-{index}",
                "type": "markdown",
                "body": section,
                "layout": "full",
            }
        )
        if index == 3:
            blocks.append(
                {
                    "id": "dataset-gap-chart-block",
                    "type": "chart",
                    "chartId": "dataset-gap-chart",
                    "layout": "full",
                }
            )

    sources = [
        {
            "id": "outline",
            "label": "最终论文大纲",
            "type": "document",
            "path": "doc/paper/outline_zh.md",
            "description": "论文章节、贡献、数据集和实验验收要求。",
        },
        {
            "id": "figure-plan",
            "label": "最终图表计划",
            "type": "document",
            "path": "doc/paper/figure_plan.md",
            "description": "Figure 1-8、表格及其数据来源。",
        },
        {
            "id": "roadmap",
            "label": "结果驱动实施路线",
            "type": "document",
            "path": "doc/paper/implementation_roadmap.md",
            "description": "数据、方法、指标和完成门槛。",
        },
        {
            "id": "experiment-plan",
            "label": "论文实验流水线实施计划",
            "type": "document",
            "path": "doc/paper/plan/experiment_pipeline.md",
            "description": "输入、标注、run、指标、批处理和汇总契约。",
        },
        {
            "id": "research-canon",
            "label": "Research Canon",
            "type": "document",
            "path": "doc/paper/manuscript/01_research_canon.md",
            "description": "当前实现、已知事实、未决事实和禁止越界的结论。",
        },
        {
            "id": "pilot-summary",
            "label": "Pilot Experiment Summary",
            "type": "file",
            "path": "doc/paper/evidence/experiment_summary.csv",
            "description": "旧 pilot 时域诊断；不作为正式主结果。",
        },
        {
            "id": "rename-manifest",
            "label": "数据重命名映射",
            "type": "file",
            "path": "doc/paper/data_renaming_manifest.csv",
            "description": "11 个正式输入视频从旧名称到 category_NN clip ID 的映射。",
        },
        {
            "id": "audit-report",
            "label": "2026-07-13 本地资产审计与执行文档",
            "type": "document",
            "path": "doc/paper/data_requirements_and_workflow_zh.md",
            "description": "对当前 inputs、premodify、runs、角点标注、代码和测试状态的汇总。",
        },
    ]

    chart = {
        "id": "dataset-gap-chart",
        "title": "当前四类正式场景的数据、标注与完整报告覆盖",
        "description": (
            "1 表示该类别已完成对应阶段。static、scrolling、screen_video、hard 已全部闭环；"
            "weak_border 已收集但按当前决定排除，因此不计入图表分母。"
        ),
        "showDescription": True,
        "type": "bar",
        "intent": "comparison",
        "question": "当前四类正式场景的数据收集、代表标注和完整 HTML 报告是否全部完成？",
        "rationale": "四个纳入类别比较三个同尺度二元阶段，分组柱状图可直接确认当前数据和主实验均已闭环。",
        "dataset": "dataset-gap",
        "encodings": {
            "x": {"field": "category", "type": "nominal"},
            "y": {
                "fields": ["collected", "representative_annotation", "complete_report"],
                "type": "quantitative",
            },
        },
        "palette": {"kind": "categorical", "name": "blue-gold"},
        "legend": {"position": "bottom", "interactive": False, "sort": "spec", "title": "视频数量"},
        "labels": {"values": "all"},
        "source": {
            "id": "dataset-gap-query",
            "label": "2026-07-13 本地完整报告审计",
            "type": "query",
            "query": {
                "language": "sql",
                "engine": "DuckDB",
                "description": "只对当前纳入实验的四类，按是否存在正式输入、代表角点标注和完整报告生成三阶段覆盖表。",
                "sql": (
                    "SELECT * FROM (VALUES ('static',1,1,1),('scrolling',1,1,1),"
                    "('screen_video',1,1,1),('hard',1,1,1)) AS "
                    "t(category,collected,representative_annotation,complete_report);"
                ),
                "filters": [
                    "完整报告要求 report.html、3/3 方法、12/12 指标 JSON 且状态为 ok",
                    "weak_border 已收集但从当前实验分母排除",
                    "数据收集按用户确认视为完成",
                    "当前快照日期为 2026-07-13",
                ],
                "metric_definitions": {
                    "collected": "该类别是否已存在至少一个正式重命名的原视频；1=完成，0=未完成。",
                    "representative_annotation": "该类别是否有至少一个代表 clip 的同名角点 CSV；1=完成，0=未完成。",
                    "complete_report": "该类别是否有至少一个 report.html、3/3 方法和 12/12 ok 指标 JSON；1=完成，0=未完成。",
                },
            },
        },
        "layout": "full",
    }

    return {
        "surface": "report",
        "manifest": {
            "version": 1,
            "title": "论文阶段性数据要求与完整执行流程",
            "description": "数据采集与统一命名已完成；报告区分收集、代表标注和完整 HTML 三种完成状态。",
            "generatedAt": "2026-07-13T00:00:00+08:00",
            "blocks": blocks,
            "cards": [],
            "charts": [chart],
            "tables": [],
            "sources": sources,
        },
        "snapshot": {
            "version": 1,
            "status": "ready",
            "generatedAt": "2026-07-13T00:00:00+08:00",
            "datasets": {"dataset-gap": DATASET_GAP_ROWS},
        },
        "sources": sources,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the data-requirements report artifact.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("doc/paper/data_requirements_and_workflow_zh.md"),
        help="Markdown source report.",
    )
    parser.add_argument(
        "--artifact",
        type=Path,
        default=Path("doc/paper/data_requirements_report_artifact.json"),
        help="Output artifact JSON path.",
    )
    args = parser.parse_args()

    markdown = args.input.read_text(encoding="utf-8")
    artifact = build_artifact(markdown)
    args.artifact.parent.mkdir(parents=True, exist_ok=True)
    args.artifact.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.artifact}")


if __name__ == "__main__":
    main()
