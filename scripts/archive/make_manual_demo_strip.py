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

from screen_normalize.manual_demo_cli import main
from screen_normalize.manual_demo_core import (
    FrameAnnotation,
    VideoMetadata,
    build_demo_strip,
    choose_frames,
    load_annotations,
    read_frame,
    read_metadata,
    save_annotations,
    warp_frame,
)


if __name__ == "__main__":
    main()
