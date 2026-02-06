#!/usr/bin/env python3
"""
Update db.json with all MP4 files: filename, title (= filename stem), duration.
"""
import json
import subprocess
from pathlib import Path
from typing import Optional

def get_duration_seconds(video_path: Path) -> Optional[float]:
    """Return duration in seconds or None if unreadable. Tries OpenCV, mutagen, then ffprobe."""
    # 1. Try OpenCV (already in requirements for rename script)
    try:
        import cv2
        cap = cv2.VideoCapture(str(video_path))
        if cap.isOpened():
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            fps = cap.get(cv2.CAP_PROP_FPS)
            cap.release()
            if fps and fps > 0 and frame_count >= 0:
                return frame_count / fps
    except Exception:
        pass
    # 2. Try mutagen (works for many MP4 containers)
    try:
        from mutagen.mp4 import MP4
        m = MP4(str(video_path))
        if m.info and getattr(m.info, "length", None) is not None:
            return float(m.info.length)
    except Exception:
        pass
    # 3. Try ffprobe
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
            capture_output=True, text=True, timeout=10
        )
        if out.returncode == 0 and out.stdout.strip():
            return float(out.stdout.strip())
    except Exception:
        pass
    return None


def format_duration(seconds: float) -> str:
    """Format seconds as HH:MM:SS or MM:SS."""
    s = int(round(seconds))
    if s < 0:
        return "00:00"
    m, sec = divmod(s, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{sec:02d}"
    return f"{m:02d}:{sec:02d}"


def main():
    root = Path(__file__).resolve().parent
    mp4s = sorted(p for p in root.iterdir() if p.is_file() and p.suffix.upper() == ".MP4")

    list_ = []
    for p in mp4s:
        filename = p.name
        title = p.stem  # filename without extension
        duration_sec = get_duration_seconds(p)
        entry = {
            "filename": filename,
            "title": title,
        }
        if duration_sec is not None:
            entry["durationInSeconds"] = str(int(round(duration_sec)))
            entry["durationDisplay"] = format_duration(duration_sec)
        list_.append(entry)

    db = {
        "notes": "title and filename are different, because title could contain newlines  whie filename doesnot,and filename contains postfix but title doesnot",
        "hints": "display durationInSeconds in format of xx:xx, like 90secs should be displayed as 01:30",
        "list": list_,
    }
    out_path = root / "db.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(list_)} entries to {out_path}")


if __name__ == "__main__":
    main()
