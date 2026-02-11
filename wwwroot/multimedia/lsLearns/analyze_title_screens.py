#!/usr/bin/env python3
"""
Analyze how long the static title screen lasts (in frames) at the start
of each MP4 file in the lsLearns/videos folder.

Heuristic:
- Read the first frame as the "title" reference.
- For subsequent frames, compute mean absolute difference vs the first frame.
- As soon as the difference exceeds a small threshold, we consider that
  motion/content has started, and the title screen ended on the previous frame.
"""

import os
from pathlib import Path

import cv2
import numpy as np


VIDEO_DIR = Path(__file__).parent / "videos"


def analyze_title_screen(video_path: Path, max_seconds: float = 10.0, diff_threshold: float = 2.0) -> tuple[float, int]:
    """
    Return (fps, static_frames) where:
    - fps: detected frames per second (float)
    - static_frames: how many initial frames are (nearly) identical to the first frame.

    - max_seconds: safety cap so we don't scan entire long videos.
    - diff_threshold: mean absolute difference threshold (0-255 scale).
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"{video_path.name}: could not open video")
        return 0.0, -1

    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    if fps <= 0:
        fps = 25.0  # reasonable fallback

    max_frames = int(max_seconds * fps)

    ret, first = cap.read()
    if not ret or first is None:
        print(f"{video_path.name}: could not read first frame")
        cap.release()
        return fps, -1

    first_gray = cv2.cvtColor(first, cv2.COLOR_BGR2GRAY)

    static_frames = 1  # count the very first frame
    frame_idx = 1

    while frame_idx < max_frames:
        ret, frame = cap.read()
        if not ret or frame is None:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(first_gray, gray)
        mean_diff = float(np.mean(diff))
        if mean_diff > diff_threshold:
            # Motion/content started at this frame
            break
        static_frames += 1
        frame_idx += 1

    cap.release()
    return fps, static_frames


def main() -> None:
    if not VIDEO_DIR.is_dir():
        print(f"Video directory not found: {VIDEO_DIR}")
        return

    files = sorted(
        f for f in VIDEO_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in {".mp4", ".m4v"}
    )
    if not files:
        print("No .mp4/.m4v files found in lsLearns/videos/")
        return

    print("Title screen static frame counts and FPS (per file):")
    for f in files:
        fps, frames = analyze_title_screen(f)
        print(f"- {f.name}: {frames} frame(s), fps ~ {fps:.2f}")


if __name__ == "__main__":
    main()

