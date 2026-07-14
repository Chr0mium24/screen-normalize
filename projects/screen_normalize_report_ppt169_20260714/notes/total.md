# 01_cover

This project normalizes the perspective of a physical display in real captured-screen video. The central result is a corner RMSE of 3.87 pixels, compared with more than 30 pixels for both the frame-wise and optical-flow baselines.

---

# 02_task_and_challenge

The hard part is not rectifying a single frame; it is keeping the screen plane stable while the camera and the content inside the screen move at the same time. Our key design choice is to let the physical border determine the homography and use internal optical flow only to diagnose conflicts.

---

# 03_current_pipeline

With the objective defined, this slide shows the complete pipeline. We initialize one quadrilateral, observe the four physical borders with local profiles, validate or recover the candidate, and finally smooth the trajectory before perspective normalization.

---

# 04_border_observation

The default estimator does not search the full image again on every frame. It samples narrow normal profiles around predicted edges, selects strong gradient responses, fits robust lines, and obtains updated corners from line intersections; LK motion remains a consistency check rather than the geometric driver.

---

# 05_method_comparison

The main difference among the three methods is the evidence they trust. Frame-wise detection restarts from the current image, optical flow propagates internal feature motion, while our method follows the physical border and invokes hold or redetection only when that evidence becomes unreliable.

---

# 06_evaluation_scope

The broader project set contains 50 videos and 14,985 frames, while the formal three-method ranking uses 10 annotated clips across five scene categories. The current comparable evidence covers corner accuracy, quadrilateral overlap, and temporal translation stability; detail and frequency-domain behavior are supporting observations rather than current numeric rankings.

---

# 07_overall_results

Across the annotated set, the proposed method wins all three aggregate metrics. It reduces corner RMSE to 3.87 pixels, raises quadrilateral IoU to 0.996, and lowers translation variation to 2.45 pixels per frame.

---

# 08_category_gains

The advantage becomes especially clear when internal scrolling or weak physical borders challenge the baselines. On scrolling clips the RMSE falls to 2.87 pixels, and on weak-border clips it remains at 9.35 pixels while both baselines exceed 155 pixels.

---

# 09_qualitative_results

The qualitative grid shows that the normalized view follows the physical display rather than the pixels moving inside it. On the hardest subset, frame-wise detection is slightly better in RMSE, but our method stays competitive in accuracy and gives the best temporal stability.

---

# 10_ablation_results

The ablation results show that trajectory smoothing is the only tested removal that changes this sequence directly. Removing it improves the instantaneous geometry slightly, but increases frame-to-frame variation from 0.752 to 1.430, so the complete method cuts that instability by about 47 percent.

---

# 11_ablation_interpretation

The equal rows are explained by execution counts, not by assuming that the safety modules have no value. After one initialization frame, the Profile observation is accepted on all 298 remaining frames, so the LK conflict branch, automatic redetection, and relaxed gates never alter the output.

---

# 12_limits_and_next_steps

The remaining failure modes occur when reflection, occlusion, or extreme low contrast makes the physical border ambiguous for a sustained period. The current gates, diagnostics, redetection, and hold behavior limit damage, while future work should improve adaptive search, multi-frame recovery, and confidence-aware output.

---

# 13_conclusion

The conclusion is simple: track the display, not the content moving inside it. A border-first pipeline produces the best aggregate geometry and stability, with its largest gains appearing exactly where frame-wise detection and optical flow are most easily confused.
