#!/usr/bin/env python3
"""
Extract the first frame of each MP4 in videos/ and save as covers_generated/xxx_cover.png.
Uses ffmpeg if available, otherwise OpenCV (cv2). For OpenCV: pip install opencv-python-headless
"""
import os
import shutil
import subprocess
import sys

def has_ffmpeg():
    return shutil.which("ffmpeg") is not None

def extract_with_ffmpeg(mp4: str, out: str) -> bool:
    try:
        r = subprocess.run(
            ["ffmpeg", "-y", "-i", mp4, "-vframes", "1", "-q:v", "2", out],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return r.returncode == 0 and os.path.isfile(out)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False

def extract_with_opencv(mp4: str, out: str) -> bool:
    try:
        import cv2
    except ImportError:
        return False
    cap = cv2.VideoCapture(mp4)
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        return False
    return cv2.imwrite(out, frame)

def _has_opencv():
    try:
        import cv2
        return True
    except ImportError:
        return False

def main():
    if not has_ffmpeg() and not _has_opencv():
        print("Neither ffmpeg nor OpenCV (cv2) is available.")
        print("Install one of them:")
        print("  ffmpeg:  brew install ffmpeg   (macOS)  or  sudo dnf install ffmpeg   (CentOS)")
        print("  OpenCV: pip3 install opencv-python-headless")
        sys.exit(1)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    video_dir = os.path.join(script_dir, "videos")
    out_dir = os.path.join(script_dir, "covers_generated")
    os.makedirs(out_dir, exist_ok=True)
    if not os.path.isdir(video_dir):
        print("No videos/ folder found.")
        return
    mp4_files = [f for f in os.listdir(video_dir) if f.lower().endswith(".mp4")]
    if not mp4_files:
        print("No .mp4 files found in videos/.")
        return
    for mp4 in sorted(mp4_files):
        base, _ = os.path.splitext(mp4)
        mp4_path = os.path.join(video_dir, mp4)
        out_path = os.path.join(out_dir, base + "_cover.png")
        print("Extracting:", mp4, "->", out_path)
        ok = False
        if has_ffmpeg():
            ok = extract_with_ffmpeg(mp4_path, out_path)
        if not ok:
            ok = extract_with_opencv(mp4_path, out_path)
        if not ok:
            print("  FAILED")
        else:
            print("  OK")
    print("Done.")

if __name__ == "__main__":
    main()
