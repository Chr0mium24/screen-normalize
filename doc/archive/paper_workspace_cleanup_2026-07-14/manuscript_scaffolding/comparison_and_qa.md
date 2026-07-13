# Sample Comparison and Manuscript QA

## 1. Structural comparison

| Requirement | Course final report example | Teacher sample | Current bilingual manuscript | Decision |
| --- | --- | --- | --- | --- |
| Abstract and keywords | present | present | present | aligned |
| Introduction and explicit contributions | separate related work/contribution subsections | contribution embedded in argument | explicit four-item contribution list | aligned with course report |
| Technical algorithm detail | main body, equations and subsections | Methods section after Results | Section 3, equations and reproducible gates | course format retained |
| Implementation details | standalone short section | detailed Methods | distributed across Sections 3 and 5 | acceptable; avoids duplicated prose |
| Dataset and experiment design | Sections 4.1 onward | Results plus Methods | Sections 4 and 5 | aligned |
| Results-led argument | limited | strong, dense multi-panel evidence | complete insertion-ready Results contracts | ready once formal data exist |
| Discussion and limitations | brief | extensive | separate interpretation, limits, future work | upgraded toward teacher sample |
| Data/code statements | absent | present | present | teacher-sample practice adopted |
| Author contributions | absent | present | placeholder present | teacher-sample practice adopted |
| References | numbered | journal style | numbered, 18 primary sources | aligned with course format |
| Bilingual parity | not applicable | not applicable | same 41 headings, equations, claims and result slots | required project deliverable |

## 2. Intentional differences

1. The teacher sample places Methods after Results because it follows a journal article format. The course example places the algorithm before experiments. This report follows the course order because readers need the screen-tracking definitions before interpreting the metrics.
2. The teacher sample is evidence-complete. This manuscript is a pre-results version, so it uses explicit `[TBD-*]` contracts instead of simulated plots, numbers, significance markers, or directional claims.
3. The teacher sample contains dense multi-panel figures. Figure locations and argumentative roles are specified here, but images are omitted as requested.
4. The current code does not implement the proposal's full LSD/Hough border-dominant tracker. The manuscript describes the executable reference-anchored tracker and records border guidance as future work.

## 3. Content QA

### Evidence and claim audit

- Literature claims are supported by 18 retained or directly verified primary papers.
- Equations correspond to implemented geometry, tracking, filtering, and metric operations.
- No pilot number is presented as a formal paper result.
- Frequency diagnostics are explicitly separated from demoiréing performance.
- Dataset completion, annotation counts, hardware, parameters, results, and author contributions remain visible placeholders.
- The temporal metric dependence on the estimated trajectory is disclosed in Experiments, Results, and Limitations.

### Reproducibility audit

- Method IDs and baseline definitions match `runner.py`.
- Inputs and annotation schema match `annotations.py`.
- Output filenames match the implemented run structure.
- Geometry, detail, and frequency definitions match the metric modules.
- The manuscript does not claim an implemented border-versus-content consistency module.

## 4. Language polish applied

- Replaced broad novelty language with bounded engineering claims.
- Removed claims such as “significant,” “robust,” or “effective” where formal results are absent.
- Defined every main symbol at first use and placed formulas next to aggregation definitions.
- Replaced generic future-work statements with specific failure modes and implementable extensions.
- Kept English and Chinese terminology consistent: rectification/矫正, screen plane/屏幕平面, reference-anchored tracking/参考帧锚定跟踪, residual alignment/残余对齐, and frequency diagnostics/频域诊断.
- Converted the Results section from an outline into complete neutral prose that can be filled from one reviewed run.

## 5. Researchwrite QA score

| Dimension | Score / 10 | Rationale |
| --- | ---: | --- |
| Research question clarity | 8.5 | explicit question and bounded task |
| Scientific tension | 8.2 | clean-screen restoration assumptions contrasted with full-scene handheld input |
| Evidence matching | 8.4 | implementation and proposal-only claims separated; result claims deferred |
| Logical chain | 8.6 | problem, mechanism, metrics, result contracts, and limitations map directly |
| Method reproducibility | 8.1 | implemented stages and gates are specified; final numeric parameters remain pending |
| Contribution specificity | 7.8 | concrete workflow and tracker contribution without unsupported novelty language |
| Risk boundary | 9.0 | metric dependence, dynamic content, initialization, occlusion, and resampling risks stated |
| Language quality | 8.3 | concise technical prose with parallel bilingual terminology |
| **Mean** | **8.36** | suitable as a polished pre-results manuscript |

## 6. Remaining completion gates

The manuscript is not a final evidence-complete paper until all of the following are resolved:

1. complete and review five categories with ten formal clips each;
2. annotate keyframes and record annotation quality control;
3. define an independent primary temporal measure;
4. decide whether to implement the proposal-complete border-guided method or formally revise the method claim;
5. run baselines, proposed method, and code-matched ablations on fixed subsets;
6. replace every `[TBD-*]` item from one reviewed run;
7. insert figures and tables, then cross-check every value against structured run output.

