"""Read-only activity button detector. Does not send keyboard/mouse input."""
import argparse
import json
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent


def read_image(path):
    image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Cannot read image: {path}")
    return image


def detect(frame, template):
    height, width = frame.shape[:2]
    if abs(width / height - 2048 / 1280) > 0.01:
        raise ValueError(f"Expected 16:10 capture, got {width}x{height}. A different aspect ratio needs recalibration.")
    scale_x, scale_y = width / 2048, height / 1280
    reference = cv2.resize(frame, (2048, 1280), interpolation=cv2.INTER_AREA)
    # Search menu area, not fixed button coordinates.
    left, top, right, bottom = 1120, 10, 1770, 230
    gray = cv2.cvtColor(reference[top:bottom, left:right], cv2.COLOR_BGR2GRAY)
    needle = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    scores = cv2.matchTemplate(gray, needle, cv2.TM_CCOEFF_NORMED)
    _, score, _, point = cv2.minMaxLoc(scores)
    x, y = point[0] + left, point[1] + top
    h, w = needle.shape
    x1, y1 = round(x * scale_x), round(y * scale_y)
    x2, y2 = round((x + w) * scale_x), round((y + h) * scale_y)
    return float(score), (x1, y1, x2 - x1, y2 - y1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, help="Offline screenshot; otherwise capture live")
    parser.add_argument("--monitor", type=int, default=1)
    parser.add_argument("--delay", type=float, default=5)
    args = parser.parse_args()
    origin = (0, 0)
    if args.image:
        frame = read_image(args.image)
    else:
        import mss
        print(f"Switch to game within {args.delay} seconds. No clicks will be sent.")
        time.sleep(max(0, args.delay))
        capture_class = getattr(mss, "MSS", None)
        if capture_class is None:  # Compatibility with older MSS releases.
            capture_class = mss.mss
        with capture_class() as capture:
            if not 1 <= args.monitor < len(capture.monitors):
                raise ValueError("Invalid monitor index")
            monitor = capture.monitors[args.monitor]
            origin = (monitor["left"], monitor["top"])
            frame = np.asarray(capture.grab(monitor))[:, :, :3].copy()
    template = read_image(ROOT / "assets/templates/activity.png")
    score, (x, y, w, h) = detect(frame, template)
    found = score >= 0.85
    result = {
        "capture_size": [frame.shape[1], frame.shape[0]],
        "found": found, "score": round(score, 4),
        "candidate_box": [x, y, w, h],
        "screen_center": [origin[0] + x + w // 2, origin[1] + y + h // 2] if found else None,
        "note": "Match score is not a probability. Read-only; verify green box visually.",
    }
    output = ROOT / "captures"
    output.mkdir(exist_ok=True)
    color = (0, 255, 0) if found else (0, 0, 255)
    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
    cv2.putText(frame, f"Activity: {score:.3f} {'FOUND' if found else 'NOT FOUND'}",
                (1120, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    ok, encoded = cv2.imencode(".png", frame)
    if not ok:
        raise RuntimeError("Failed to encode debug image")
    encoded.tofile(str(output / "activity_debug.png"))
    (output / "activity_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print(f"Inspect: {output / 'activity_debug.png'}")


if __name__ == "__main__":
    main()
