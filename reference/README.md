# Project Reference Pack

这个文件夹用于搬到另一个已经完成的项目里，快速整理课程 proposal 和 final submission 参考材料。下面的结论基于当前仓库里的课程模板、cover letter 和 example 文件。

## 目录结构

```text
reference/
├── proposal/
│   ├── proposal_template.docx
│   ├── proposal_template-5-10pages-3mins.pptx
│   ├── example_proposal_presentation.pdf
│   └── your_group_id_cover_letter.docx
└── final/
    ├── example_final_report_video_stabilization.pdf
    └── example_final_presentation_video_stabilization.pptx
```

## 一共要交哪些东西

从模板看，项目成绩由三部分组成：

| 部分 | 占比 | 需要准备的材料 |
| --- | ---: | --- |
| Proposal | 20% | 一页 proposal 文档、proposal presentation、cover letter 初稿信息 |
| Paper | 50% | 最终项目论文/报告，建议按课程 LaTeX/report template 输出 PDF |
| Presentation | 30% | 最终答辩 PPT 或 PDF |
| Bonus | 额外 | 视课程要求，通常来自额外实验、代码完整性、demo 或更强结果 |

实际提交时建议准备这 5 类文件：

1. `proposal_template.docx` 改出来的 one-page proposal。
2. `proposal_template-5-10pages-3mins.pptx` 改出来的 proposal presentation。
3. `your_group_id_cover_letter.docx` 改出来的 cover letter。
4. 最终 paper/report PDF。
5. 最终 presentation PPT/PDF。

如果老师或 TA 另有 LMS/Blackboard/邮件要求，以课程平台的最终通知为准。

## Proposal 文档怎么写

`proposal_template.docx` 要求最多一页，核心结构是：

```text
Names & IDs
Title

Description:
- Task and goal
- Dataset and experiment
- Expected results

Tentative Timeline / To-do lists
```

写法建议：

- `Task and goal`：一句话说明输入、输出和任务目标。例如“输入低光图像，输出增强后的清晰图像”。
- `Motivation / novelty`：说明为什么现有方法不够好，你的方法想补什么不足。
- `Pipeline`：用 3-5 个步骤写清楚方法，不要只写“train a model”。
- `Dataset and experiment`：写数据集、训练/测试划分、baseline、评价指标。
- `Expected results`：写预期可视化效果和指标提升方向。
- `Timeline`：按日期列调查、代码、实验、写报告、做 PPT。

## Proposal PPT 怎么写

`proposal_template-5-10pages-3mins.pptx` 的文件名说明 proposal presentation 建议是 5-10 页、3 分钟左右。可以按这个顺序做：

1. Title + team members。
2. Motivation：为什么这个问题值得做。
3. Goal：输入输出是什么，最终要实现什么。
4. Related work / existing methods：已有方法和不足。
5. Methodology：你的 pipeline。
6. Dataset：数据来源、规模、样例。
7. Experiment plan：baseline、ablation、metrics。
8. Initial results 或 feasibility：已有初步结果，没有就放样例和计划。
9. Timeline：后续任务安排。

示例 proposal `example_proposal_presentation.pdf` 的结构更短，主要是：

```text
Title + Motivation
Goal and Methodology
Dataset and Initial Results
```

可以学习它的写法：先讲真实问题，再讲具体目标，再按 pipeline 写方法，最后放数据和初步结果图。

## Cover Letter 怎么填

`your_group_id_cover_letter.docx` 的学生部分需要填：

- Paper ID
- Student Name
- Topic Area
- Title
- Abstract，200-300 words

Abstract 建议按这个顺序写：

```text
Problem and limitation of existing methods.
Proposed method and main pipeline.
Dataset and experiment setting.
Expected or measured result.
```

## 本文件夹里的参考文件

| 文件 | 用途 |
| --- | --- |
| `proposal/proposal_template.docx` | 一页 proposal 正文模板 |
| `proposal/proposal_template-5-10pages-3mins.pptx` | proposal 答辩 PPT 模板 |
| `proposal/example_proposal_presentation.pdf` | 课程给的 proposal 示例 |
| `proposal/your_group_id_cover_letter.docx` | cover letter 模板 |
| `final/example_final_report_video_stabilization.pdf` | 往届 final report 示例 |
| `final/example_final_presentation_video_stabilization.pptx` | 往届 final presentation 示例 |

## 搬到另一个项目后的使用顺序

1. 先用 `proposal_template.docx` 写一页 proposal。
2. 再用同一套内容压缩成 5-10 页 proposal PPT。
3. 把 proposal 的核心内容扩成 cover letter 里的 200-300 words abstract。
4. 后续 final paper 可以参考 `example_final_report_video_stabilization.pdf` 的章节结构。
5. 后续 final presentation 可以参考 `example_final_presentation_video_stabilization.pptx` 的讲述节奏。
