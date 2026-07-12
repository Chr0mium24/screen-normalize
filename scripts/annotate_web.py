#!/usr/bin/env python3
from __future__ import annotations

import argparse
import threading
import webbrowser
from pathlib import Path

from screen_normalize.annotation_web import browser_url, serve


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="在浏览器中批量标注视频屏幕四角。")
    parser.add_argument("--input", type=Path, default=Path("inputs"))
    parser.add_argument("--frames-per-clip", type=int, default=5)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.frames_per_clip <= 0:
        raise SystemExit("--frames-per-clip 必须为正整数")
    server = serve(args.input, args.host, args.port, args.frames_per_clip)
    url = browser_url(args.host, server.server_port)
    print(f"人工标注页面：{url}")
    print("按 Ctrl+C 停止服务。")
    if not args.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
