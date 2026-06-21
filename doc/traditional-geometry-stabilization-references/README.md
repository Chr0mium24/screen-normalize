# 传统几何归一化与稳定化参考文献

本目录收集“基于传统图像处理的拍屏视频几何归一化与稳定化”方向的可引用论文。当前项目不把图像恢复或深度模型作为主线，参考文献也按传统视觉流程组织。

下载时间：2026-06-21

## 建议主线

报告可以按下面逻辑引用：

1. 拍屏幕视频可以近似为“相机拍摄平面目标”，因此适合用四角点和单应变换做几何归一化。
2. 屏幕边界、文档边界、白板边界都属于相似问题，可以借鉴文档/白板矫正方法。
3. 逐帧检测角点容易抖动，所以要用特征跟踪、RANSAC 和轨迹平滑。
4. 屏幕上的水平/竖直结构可以作为线段和消失点证据，但不能被动态文字或视频内容逐帧驱动。
5. 稳定化本质是估计相机运动轨迹并滤除高频抖动，最终输出固定比例的正面屏幕视频。

## 必读文献

### 屏幕、文档和白板透视矫正

- `screen_to_camera_homography_estimation_iccv2003.pdf`  
  Okatani & Deguchi, *Screen-to-Camera Homography Estimation*, ICCV 2003.  
  用来支撑“屏幕平面到相机图像之间可用 homography 建模”。  
  Source: https://perso.telecom-paristech.fr/bloch/VOIR/iccv03/0774_okatani.pdf

- `whiteboard_scanning_image_enhancement_2007.pdf`  
  Zhang & He, *Whiteboard Scanning and Image Enhancement*.  
  用来支撑“自动定位平面区域、裁切、矩形化、增强”的白板扫描流程。  
  Source: https://www.microsoft.com/en-us/research/wp-content/uploads/2016/11/Digital-Signal-Processing.pdf

- `mobile_document_perspective_rectification_vanishing_point_2007.pdf`  
  Lu & Tan, *Perspective Rectification for Mobile Phone Camera-Based Documents Using a Hybrid Approach to Vanishing Point Detection*, CBDAR 2007.  
  用来支撑“手机拍摄平面内容时，可以用消失点和文本/结构方向做透视校正”。  
  Source: https://imlab.jp/cbdar2007/proceedings/papers/O3-1.pdf

- `perspective_correction_camera_document_analysis_2005.pdf`  
  Jagannathan et al., *Perspective Correction Methods for Camera Based Document Analysis*, 2005.  
  用来补充文档图像透视校正的传统方法背景。  
  Source: https://cvit.iiit.ac.in/images/ConferencePapers/2005/jagannathan05Perspective.pdf

### 特征跟踪和参考平面估计

- `lucas_kanade_iterative_image_registration_1981.pdf`  
  Lucas & Kanade, *An Iterative Image Registration Technique with an Application to Stereo Vision*, 1981.  
  用来支撑 LK 光流/图像配准的基础思想。  
  Source: https://publications.ri.cmu.edu/storage/publications/pub_files/pub3/lucas_bruce_d_1981_1/lucas_bruce_d_1981_1.pdf

- `shi_tomasi_good_features_to_track_1994.pdf`  
  Shi & Tomasi, *Good Features to Track*, CVPR 1994.  
  用来支撑角点/特征点选择。  
  Source: https://users.cs.duke.edu/~tomasi/papers/shi/TR_93-1399_Cornell.pdf

- `bouguet_pyramidal_lk_feature_tracker.pdf`  
  Bouguet, *Pyramidal Implementation of the Lucas Kanade Feature Tracker*.  
  用来解释金字塔 LK 跟踪为什么能处理较大位移。  
  Source: https://robots.stanford.edu/cs223b04/algo_tracking.pdf

- `mlesac_robust_estimator_image_geometry_2000.pdf`  
  Torr & Zisserman, *MLESAC: A New Robust Estimator with Application to Estimating Image Geometry*, CVIU 2000.  
  用来支撑 RANSAC 类鲁棒估计在单应性和图像几何估计中的作用。  
  Source: https://www.robots.ox.ac.uk/~vgg/publications/2000/Torr00/torr00.pdf

### 线段和消失点

- `lsd_line_segment_detector_ipol2012.pdf`  
  Grompone von Gioi et al., *LSD: a Line Segment Detector*, IPOL 2012.  
  用来支撑线段检测方法。  
  Source: https://www.ipol.im/pub/art/2012/gjmr-lsd/article.pdf

- `vanishing_point_detection_point_alignments_ipol2017.pdf`  
  Lezama et al., *Finding Vanishing Points via Point Alignments in Image Primal and Dual Domains*, IPOL 2017.  
  用来支撑用直线/点对齐估计消失点。  
  Source: https://www.ipol.im/pub/art/2017/148/article_lr.pdf

- `vanishing_points_correct_camera_rotation_crv2005.pdf`  
  Gallagher, *Using Vanishing Points To Correct Camera Rotation In Images*, CRV 2005.  
  用来支撑用消失点估计相机方向和旋转校正。  
  Source: https://chenlab.ece.cornell.edu/people/Andy/publications/Andy_files/rotation_crv2005.pdf

### 视频稳定化和轨迹平滑

- `motion_smoothing_strategies_video_stabilization_ipol2017.pdf`  
  Sánchez & Morel, *Motion Smoothing Strategies for Video Stabilization*, IPOL 2017.  
  用来支撑“估计相机运动、平滑轨迹、重新 warp”的稳定化主流程。  
  Source: https://www.ipol.im/pub/art/2017/209/revisions/2022-01-01/article.pdf

- `l1_optimal_camera_paths_cvpr2011.pdf`  
  Grundmann et al., *Auto-Directed Video Stabilization with Robust L1 Optimal Camera Paths*, CVPR 2011.  
  用来支撑鲁棒相机路径优化和平滑。  
  Source: https://research.google.com/pubs/archive/37041.pdf

- `cinematic_l1_log_homography_wacv2021.pdf`  
  Bradley et al., *Cinematic-L1 Video Stabilization with a Log-Homography Model*, WACV 2021.  
  用来支撑 homography 参数轨迹平滑和更现代的视频稳定化表述。  
  Source: https://openaccess.thecvf.com/content/WACV2021/papers/Bradley_Cinematic-L1_Video_Stabilization_With_a_Log-Homography_Model_WACV_2021_paper.pdf

- `video_stabilization_evaluation_framework_euvip2018.pdf`  
  Guilluy et al., *A Performance Evaluation Framework for Video Stabilization Methods*, EUVIP 2018.  
  用来支撑稳定化指标设计和结果评价。  
  Source: https://www.laurentoudre.fr/publis/GBO-EUVIP-18.pdf

### 频域残余配准

- `fft_registration_reddy_chatterji_1996.pdf`  
  Reddy & Chatterji, *An FFT-Based Technique for Translation, Rotation, and Scale-Invariant Image Registration*, 1996.  
  用来支撑用频域相位相关估计归一化后的小残余平移/旋转/尺度。  
  Source: https://dev.ipol.im/~reyotero/bib/bib_all/1996_Reddy_Chatterji_fft_based_trans_rot_scale_invar_registr.pdf

## 可选补充

- `fast_document_perspective_rectification_mobile_cvprw2014.pdf`  
  Williem et al., *Fast and Robust Perspective Rectification of Document Images on a Smartphone*, CVPR Workshops 2014.  
  可作为移动端文档透视矫正的补充案例。  
  Source: https://openaccess.thecvf.com/content_cvpr_workshops_2014/W03/papers/Williem_Fast_and_Robust_2014_CVPR_paper.pdf

- `realtime_joint_camera_orientation_vanishing_points_cvpr2015.pdf`  
  可作为消失点和相机方向估计的补充资料。  
  Source: https://openaccess.thecvf.com/content_cvpr_2015/papers/Lee_Real-Time_Joint_Estimation_2015_CVPR_paper.pdf

## 写报告时的推荐引用组合

如果篇幅有限，优先引用以下 8 篇：

1. `screen_to_camera_homography_estimation_iccv2003.pdf`
2. `whiteboard_scanning_image_enhancement_2007.pdf`
3. `mobile_document_perspective_rectification_vanishing_point_2007.pdf`
4. `lucas_kanade_iterative_image_registration_1981.pdf`
5. `shi_tomasi_good_features_to_track_1994.pdf`
6. `mlesac_robust_estimator_image_geometry_2000.pdf`
7. `lsd_line_segment_detector_ipol2012.pdf`
8. `motion_smoothing_strategies_video_stabilization_ipol2017.pdf`
9. `l1_optimal_camera_paths_cvpr2011.pdf`
