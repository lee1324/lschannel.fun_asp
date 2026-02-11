#!/usr/bin/env python3
"""
Extract the first frame of each MP4 in videos/ and save as covers_generated/xxx_cover.png.
Crops to 640x360 (16:9 aspect ratio) - takes center portion to match content frame size.
Uses ffmpeg if available, otherwise OpenCV (cv2). For OpenCV: pip install opencv-python-headless
"""
import json
import os
import shutil
import subprocess
import sys

# Cover size: 640x360 (16:9 aspect ratio) to match content frame size
COVER_WIDTH = 640
COVER_HEIGHT = 360

def load_cover_offsets():
    """Load coverOffset values from db.json"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "db.json")
    offsets = {}
    if os.path.exists(db_path):
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'list' in data:
                    for item in data['list']:
                        filename = item.get('filename', '')
                        # Handle both "coverOffet" (typo) and "coverOffset" (correct)
                        offset = item.get('coverOffset') or item.get('coverOffet', 0)
                        offsets[filename] = int(offset)
        except Exception as e:
            print(f"Warning: Could not load cover offsets from db.json: {e}")
    return offsets

def has_ffmpeg():
    return shutil.which("ffmpeg") is not None

def extract_with_ffmpeg(mp4: str, out: str, width: int = 640, height: int = 360, offset_y: int = 0) -> bool:
    try:
        # Extract frame and crop portion to cover size (16:9 aspect ratio)
        # Move view down by offset_y pixels (see lower portion of frame), then crop
        # Crop filter: crop=out_w:out_h:x:y
        # x = horizontal center: (iw-ow)/2
        # y = vertical center offset downward: (ih-oh)/2 + offset_y
        y_pos = f"(ih-{height})/2+{offset_y}"
        r = subprocess.run(
            ["ffmpeg", "-y", "-i", mp4, "-vframes", "1", 
             "-vf", f"crop={width}:{height}:(iw-{width})/2:{y_pos}", "-q:v", "2", out],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return r.returncode == 0 and os.path.isfile(out)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False

def extract_with_opencv(mp4: str, out: str, width: int = 640, height: int = 360, offset_y: int = 0) -> bool:
    try:
        import cv2
    except ImportError:
        return False
    cap = cv2.VideoCapture(mp4)
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        return False
    # Crop portion of frame to match cover size, with vertical offset upward
    h, w = frame.shape[:2]
    if w < width or h < height:
        # If frame is smaller than target, scale it up first
        scale = max(width / w, height / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        h, w = frame.shape[:2]
    # Crop with offset: center horizontally, offset downward vertically (move view down)
    start_x = (w - width) // 2
    start_y = (h - height) // 2 + offset_y
    # Ensure coordinates are within bounds
    start_y = max(0, min(start_y, h - height))
    start_x = max(0, min(start_x, w - width))
    cropped = frame[start_y:start_y + height, start_x:start_x + width]
    return cv2.imwrite(out, cropped)

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
    
    # Load cover offsets from db.json
    cover_offsets = load_cover_offsets()
    print(f"Loaded cover offsets for {len(cover_offsets)} videos from db.json")
    
    mp4_files = [f for f in os.listdir(video_dir) if f.lower().endswith((".mp4", ".m4v"))]
    if not mp4_files:
        print("No .mp4 files found in videos/.")
        return
    for mp4 in sorted(mp4_files):
        base, _ = os.path.splitext(mp4)
        mp4_path = os.path.join(video_dir, mp4)
        out_path = os.path.join(out_dir, base + "_cover.png")
        # Get cover offset for this video (default to 0 if not found)
        offset_y = cover_offsets.get(mp4, 0)
        print(f"Extracting: {mp4} (offset: {offset_y}px up) -> {out_path}")
        ok = False
        if has_ffmpeg():
            ok = extract_with_ffmpeg(mp4_path, out_path, COVER_WIDTH, COVER_HEIGHT, offset_y)
        if not ok:
            ok = extract_with_opencv(mp4_path, out_path, COVER_WIDTH, COVER_HEIGHT, offset_y)
        if not ok:
            print("  FAILED")
        else:
            print("  OK")
    print("Done.")

if __name__ == "__main__":
    main()
