"""Guild-only workflow. Dry run by default; --run enables input."""
import argparse
import ctypes
from datetime import datetime, timezone
import json
import sys
import time
import cv2
import numpy as np
from detect_activity import ROOT, detect, read_image
from guild_status import activity_page, guild_state, guild_active, world_visible
from guild_accept import observe
from window_guard import require_foreground
from open_activity import stable_target, save_image


def dialog_detector(expected):
    """Verify dialog state without modifying the workflow's logging timer."""
    def inner(frame):
        state, match = observe(frame)
        if state != expected:
            raise RuntimeError("NPC dialog changed.")
        return match
    return inner


def should_open_activity(go_sent,talk_sent,accept_sent,npc_scores):
    return not (go_sent or talk_sent or accept_sent) and npc_scores.get("talk_score",0)<.90


def completion_candidate(seen_active, missing_frames):
    return seen_active and missing_frames >= 3


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run",action="store_true")
    p.add_argument("--image",help="Read-only status check from an image")
    p.add_argument("--timeout",type=int,default=1800,help="Whole workflow limit, seconds")
    a=p.parse_args(argv)
    if a.image:
        print(json.dumps(guild_state(read_image(a.image)),indent=2))
        return
    if sys.platform!="win32":
        raise RuntimeError("Live workflow requires Windows.")
    u=ctypes.windll.user32
    try:u.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except AttributeError:u.SetProcessDPIAware()
    u.GetForegroundWindow.restype=ctypes.c_void_p
    import pyautogui as pg
    import mss
    pg.FAILSAFE=True
    foreground=None
    deadline=time.monotonic()+max(1,a.timeout)+5
    def check():
        if u.GetAsyncKeyState(0x1B)&0x8000:raise RuntimeError("Cancelled by Esc.")
        pg.failSafeCheck()
        if foreground is not None:
            require_foreground(u, foreground, pg.failSafeCheck)
        if time.monotonic()>deadline:raise RuntimeError("Workflow timeout; NOT completed.")
    def wait(seconds):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            check()
            time.sleep(min(.1,max(0,end-time.monotonic())))
    print("Guild workflow v0.14. Switch to game within 5 seconds.")
    print("INPUT ENABLED. Hold Esc or use mouse corner to stop." if a.run else "READ ONLY.")
    wait(5)
    foreground=u.GetForegroundWindow()
    cls=getattr(mss,"MSS",None) or mss.mss
    with cls() as cap:
        mon=next(m for m in cap.monitors[1:] if m["left"]==0 and m["top"]==0)
        if tuple(pg.size())!=(mon["width"],mon["height"]):
            raise RuntimeError("Mouse/capture dimensions differ.")
        def grab():
            check()
            return np.asarray(cap.grab(mon))[:,:,:3].copy()
        def report(state,frame,error=None):
            npc_diagnostics={}
            observe(frame, npc_diagnostics)
            save_image("guild_workflow_last.png",frame)
            path=ROOT/"captures/guild_run_result.json"
            path.write_text(json.dumps({"state":state,"time_utc":datetime.now(timezone.utc).isoformat(),
                                        "completion_verified":state=="completed",
                                        "observation":guild_state(frame),"npc_detection":npc_diagnostics,"error":error},indent=2),encoding="utf-8")
            print(state)
            return {"state":state,"completion_verified":state=="completed","foreground":foreground}
        def click_match(detector):
            first=detector(grab())
            wait(.3)
            second=detector(grab())
            target=stable_target(first,second)
            check()
            pg.click(*target)
            wait(1)
        activity_template=read_image(ROOT/"assets/templates/activity.png")
        def open_menu():
            click_match(lambda f:detect(f,activity_template))
            end=time.monotonic()+10
            while time.monotonic()<end:
                frame=grab()
                if activity_page(frame):return frame
                wait(.5)
            raise RuntimeError("Activity menu did not open; no retry.")
        def scan_menu():
            # Scroll only on a verified activity page. Search up then down, bounded.
            for delta in [0,6,6,-3,-3,-3,-3,-3,-3]:
                frame=grab()
                if not activity_page(frame):raise RuntimeError("Activity page lost.")
                if delta:
                    check()
                    pg.moveTo(round(mon["width"]*.45),round(mon["height"]*.55),duration=.15)
                    pg.scroll(delta)
                    wait(.6)
                    frame=grab()
                state=guild_state(frame)
                if state["state"] in ("pending","completed"):
                    wait(.3)
                    second=guild_state(grab())
                    if second["state"]==state["state"]:return second
            raise RuntimeError("Guild card not verified after bounded scrolling.")
        def go_detector(frame):
            s=guild_state(frame)
            if s["state"]!="pending":raise RuntimeError("Guild Go no longer verified.")
            return s["score"],s["go_box"]
        try:
            frame=grab()
            if not a.run:
                report(guild_state(frame)["state"],frame)
                print("Use --run to enable Guild workflow.")
                return
            started= guild_active(frame)
            go_sent=False
            talk_sent=False
            accept_sent=False
            missing=0
            last_npc_log=0.0
            phase_deadline=time.monotonic()+120
            while True:
                frame=grab()
                if activity_page(frame):
                    card=scan_menu()
                    if card["state"]=="completed":
                        return report("completed",grab())
                    if started or accept_sent or go_sent:
                        raise RuntimeError("Guild still pending after verification; paused without restarting.")
                    click_match(go_detector)
                    go_sent=True
                    phase_deadline=time.monotonic()+120
                    continue
                if guild_active(frame):
                    if not started:print("Guild quest observed. Waiting for game Auto.")
                    started=True
                    missing=0
                    wait(5)
                    continue
                if started:
                    # Loading, dialogs and hidden HUD cannot count as disappearance.
                    missing=missing+1 if world_visible(frame) else 0
                    if completion_candidate(started,missing):
                        open_menu()
                        continue
                    wait(5)
                    continue
                npc_scores={}
                state,m=observe(frame,npc_scores)
                if time.monotonic()-last_npc_log>=10:
                    print('NPC detection:',state,json.dumps(npc_scores),flush=True)
                    last_npc_log=time.monotonic()
                if state=="talk" and not talk_sent:
                    stable_target(dialog_detector("talk")(frame),dialog_detector("talk")(grab()))
                    check()
                    print("Guild NPC verified; sending F.",flush=True)
                    pg.press("f")
                    talk_sent=True
                    phase_deadline=time.monotonic()+60
                    wait(1)
                    continue
                if state=="confirm" and not accept_sent:
                    click_match(dialog_detector("confirm"))
                    accept_sent=True
                    phase_deadline=time.monotonic()+120
                    print("Accept click sent; waiting to observe active Guild quest.")
                    continue
                if should_open_activity(go_sent,talk_sent,accept_sent,npc_scores) and world_visible(frame):
                    open_menu()
                    continue
                if time.monotonic()>phase_deadline:
                    raise RuntimeError("Timed out waiting for travel/dialog/active quest. Not completed.")
                wait(.5)
        except Exception as error:
            # A stopped or unknown run must never leave a current success record.
            report("stopped_unverified",np.asarray(cap.grab(mon))[:,:,:3].copy(),str(error))
            raise


if __name__=="__main__":
    main()
