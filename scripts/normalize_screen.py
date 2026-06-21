#!/usr/bin/env python3
# /// script
# dependencies = [
#   "numpy>=2.2.0",
#   "opencv-python-headless>=4.12.0.88",
# ]
# ///

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from screen_normalize.cli import main
from screen_normalize.common import (
    DEFAULT_FALLBACK_CORNERS,
    create_run_directory,
    open_capture,
    parse_corners,
    project_root,
)
from screen_normalize.detection import detect_screen_corners
from screen_normalize.geometry import (
    detected_corners_are_valid,
    geometry_update_is_reasonable,
    homography_inlier_screen_coverage,
    homography_median_reprojection_error,
    order_corners,
)


if __name__ == "__main__":
    main()
