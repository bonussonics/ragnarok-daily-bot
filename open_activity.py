"""Find activity twice, click once on primary Windows monitor, save result."""
import argparse
import ctypes
import sys
import time

from detect_activity import ROOT, detect, read_image
import cv2
import numpy as np


def stable_target(first, second):
    score1, box1 = first
    score2, box2 = second
    if min(score1, score2) < 0.90:
        raise RuntimeError("Activity not confidently detected twice. No click.")
    if max(abs(a-b) for a, b in zip(box1, box2)) > 5:
        raise RuntimeError("Activity moved between frames. No click.")
    x, y, w, h = box2
    return x + w // 2, y + h // 2


def save_image(name, frame):
    path = ROOT / "captures" / name
    path.parent.mkdir(exist_ok=True)
    ok, data = cv2.imencode(".png", frame)
    if not ok:
        raise RuntimeError("Could not encode screenshot")
    data.tofile(str(path))
    print(path)


def main(task="activity"):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--click", action="store_true", help="Send exactly one click")
    args = parser.parse_args()
    if sys.platform != "win32":
        raise RuntimeError("This click test is for Windows.")
    user32 = ctypes.windll.user32
    # Set physical pixel coordinates before importing mouse/capture libraries.
    try:
        user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except AttributeError:
        user32.SetProcessDPIAware()
    user32.GetForegroundWindow.restype = ctypes.c_void_p
    import pyautogui
    import mss
    pyautogui.FAILSAFE = True
    print(f"{task} test v0.4. Switch to game in 5 seconds.")
    print("Exactly one click enabled." if args.click else "Dry run: no click.")
    print("Hold Esc or move mouse to a primary-screen corner to cancel.")
    def check():
        if user32.GetAsyncKeyState(0x1B) & 0x8000:
            raise RuntimeError("Cancelled by Esc.")
        pyautogui.failSafeCheck()
    for _ in range(50):
        check()
        time.sleep(0.1)
    foreground = user32.GetForegroundWindow()
    template = read_image(ROOT / "assets/templates/activity.png")
    detector = detect
    if task == "guild":
        from guild_daily import detect_guild
        detector = detect_guild
    capture_class = getattr(mss, "MSS", None) or mss.mss
    with capture_class() as capture:
        monitor = next((m for m in capture.monitors[1:]
                        if m["left"] == 0 and m["top"] == 0), None)
        if monitor is None:
            raise RuntimeError("Primary monitor not found.")
        if tuple(pyautogui.size()) != (monitor["width"], monitor["height"]):
            raise RuntimeError("Capture/mouse coordinate sizes differ. No click.")
        def grab():
            return np.asarray(capture.grab(monitor))[:, :, :3].copy()
        first = detector(grab(), template)
        time.sleep(0.25)
        frame = grab()
        second = detector(frame, template)
        center = stable_target(first, second)
        print(f"Scores: {first[0]:.4f}, {second[0]:.4f}; target: {center}")
        save_image(f"{task}_before_click.png", frame)
        check()
        if user32.GetForegroundWindow() != foreground:
            raise RuntimeError("Foreground window changed. No click.")
        if not args.click:
            print("Dry run complete. Add --click to test one click.")
            return
        pyautogui.click(*center)
        time.sleep(2)
        save_image(f"{task}_after_click.png", grab())
        if task == "guild":
            print("Waiting 20 seconds for travel; no further input will be sent.")
            for _ in range(200):
                check()
                time.sleep(0.1)
            save_image("guild_after_travel.png", grab())
        print("One click sent. Inspect screenshots; task completion is not verified.")


if __name__ == "__main__":
    main()
