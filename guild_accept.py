"""Talk to Guild daily NPC, then accept once. Does not verify quest completion."""
import argparse
import ctypes
import sys
import time
import cv2
import numpy as np
from detect_activity import ROOT, read_image
from open_activity import save_image, stable_target


def observe(frame, diagnostics=None):
    height, width = frame.shape[:2]
    if abs(width / height - 1.6) > 0.01:
        raise ValueError("Expected 16:10 game capture.")
    gray = cv2.cvtColor(cv2.resize(frame, (2048, 1280)), cv2.COLOR_BGR2GRAY)
    def find(name, roi):
        x1, y1, x2, y2 = roi
        t = cv2.cvtColor(read_image(ROOT / f"assets/templates/{name}.png"), cv2.COLOR_BGR2GRAY)
        result = cv2.matchTemplate(gray[y1:y2, x1:x2], t, cv2.TM_CCOEFF_NORMED)
        _, score, _, (x, y) = cv2.minMaxLoc(result)
        x, y = x+x1, y+y1
        h, w = t.shape
        sx, sy = width/2048, height/1280
        a, b = round(x*sx), round(y*sy)
        return score, (a, b, round((x+w)*sx)-a, round((y+h)*sy)-b)
    accept = find("guild_accept", (1320, 740, 1850, 1020))
    identity = find("guild_dialog_npc", (700, 990, 1300, 1120))
    if min(accept[0], identity[0]) >= 0.90:
        return "confirm", (min(accept[0], identity[0]), accept[1])
    talk = find("guild_talk", (1000, 550, 1650, 850))
    nearby = find("guild_nearby_npc", (600, 550, 1500, 1000))
    nearby_alt = find("guild_nearby_npc_alt", (600, 550, 1500, 1000))
    nearby = max((nearby, nearby_alt), key=lambda m:m[0])
    if diagnostics is not None:
        diagnostics.update(talk_score=float(talk[0]), npc_score=float(nearby[0]),
                           accept_score=float(accept[0]), dialog_npc_score=float(identity[0]))
    if min(talk[0], nearby[0]) >= 0.90:
        return "talk", (min(talk[0], nearby[0]), talk[1])
    # Background-independent fallback: same NPC yellow glyphs, strong talk text,
    # and Guild map title must all be present. Report click-target score separately.
    color=cv2.resize(frame,(2048,1280))
    def yellow(image):
        binary=cv2.inRange(cv2.cvtColor(image,cv2.COLOR_BGR2HSV),
                           np.array([20,120,150]),np.array([40,255,255]))
        return cv2.dilate(binary,np.ones((3,3),np.uint8))
    label=read_image(ROOT/'assets/templates/guild_nearby_npc_alt.png')
    mask=yellow(color)[550:1000,600:1500]
    glyph_score=0.0
    glyph_scale=1.0
    for scale in np.arange(.85,1.251,.025):
        scaled=cv2.resize(label,None,fx=float(scale),fy=float(scale))
        _,score,_,_=cv2.minMaxLoc(cv2.matchTemplate(mask,yellow(scaled),cv2.TM_CCOEFF_NORMED))
        if score>glyph_score:
            glyph_score=float(score); glyph_scale=float(scale)
    scene=find('guild_scene',(1750,0,1980,100))
    if diagnostics is not None:
        diagnostics.update(npc_yellow_score=float(glyph_score),guild_scene_score=float(scene[0]),npc_scale=glyph_scale)
    if talk[0]>=.90 and glyph_score>=.80 and scene[0]>=.90:
        if diagnostics is not None: diagnostics['talk_evidence']='yellow_npc_and_guild_scene'
        return 'talk',talk
    return "unknown", None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--click", action="store_true")
    args = parser.parse_args()
    if sys.platform != "win32":
        raise RuntimeError("Live input requires Windows.")
    user32 = ctypes.windll.user32
    try:
        user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except AttributeError:
        user32.SetProcessDPIAware()
    user32.GetForegroundWindow.restype = ctypes.c_void_p
    import mss
    import pyautogui
    pyautogui.FAILSAFE = True
    def check():
        if user32.GetAsyncKeyState(0x1B) & 0x8000:
            raise RuntimeError("Cancelled by Esc.")
        pyautogui.failSafeCheck()
    print("Guild accept v0.5. Switch to game in 5 seconds. Hold Esc to cancel.")
    print("Input enabled: at most one F and one accept click." if args.click else "Dry run; no input.")
    for _ in range(50):
        check()
        time.sleep(0.1)
    foreground = user32.GetForegroundWindow()
    capture_class = getattr(mss, "MSS", None) or mss.mss
    with capture_class() as capture:
        monitor = next(m for m in capture.monitors[1:] if m["left"] == 0 and m["top"] == 0)
        if tuple(pyautogui.size()) != (monitor["width"], monitor["height"]):
            raise RuntimeError("Capture and mouse coordinates differ.")
        def grab():
            return np.asarray(capture.grab(monitor))[:, :, :3].copy()
        previous = None
        pressed_f = False
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            check()
            if user32.GetForegroundWindow() != foreground:
                raise RuntimeError("Foreground changed; stopped.")
            frame = grab()
            state, match = observe(frame)
            if state == "unknown":
                previous = None
                time.sleep(0.25)
                continue
            if previous and previous[0] == state:
                try:
                    target = stable_target(previous[1], match)
                except RuntimeError:
                    previous = (state, match)
                    continue
                save_image("guild_before_accept.png", frame)
                print(f"Verified state: {state}; target: {target}; score: {match[0]:.4f}")
                if not args.click:
                    return
                check()
                if user32.GetForegroundWindow() != foreground:
                    raise RuntimeError("Foreground changed; stopped.")
                if state == "talk" and not pressed_f:
                    pyautogui.press("f")
                    pressed_f = True
                    previous = None
                    time.sleep(0.5)
                    continue
                if state == "confirm":
                    pyautogui.click(*target)
                    # No further game inputs after accepting.
                    for _ in range(50):
                        check()
                        time.sleep(0.1)
                    after = grab()
                    save_image("guild_after_accept.png", after)
                    if observe(after)[0] == "confirm":
                        print("Confirm still visible. Acceptance NOT verified; no retry.")
                    else:
                        print("Confirm no longer detected. Inspect image; quest start/completion not verified.")
                    return
            previous = (state, match)
            time.sleep(0.25)
        save_image("guild_accept_timeout.png", grab())
        raise RuntimeError("Timed out waiting for verified Guild dialog. No further input.")


if __name__ == "__main__":
    main()
