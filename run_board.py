"""Quest Board workflow v0.10. Read only unless --run is supplied."""
import argparse
import ctypes
from datetime import datetime, timezone
import json
import sys
import time
import numpy as np
from detect_activity import ROOT, read_image, detect
from guild_status import activity_page, world_visible
from board_status import board_state
from open_activity import stable_target, save_image


class BoardStateChanged(RuntimeError):
    pass


def verified_click(detector, grab, wait, guard, send_click):
    # Re-observe only before input. Never retry a click or swallow cancellation,
    # foreground loss, or input errors. Eight pairs bound transient UI waiting.
    for _ in range(8):
        try:
            first = detector(grab())
            wait(.3)
            second = detector(grab())
        except BoardStateChanged:
            wait(.3)
            continue
        point = stable_target(first, second)
        guard()
        send_click(*point)
        wait(1)
        return
    raise BoardStateChanged('Board state did not stabilize; no click.')


def main(argv=None, *, expected_foreground=None, start_delay=5):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',action='store_true')
    p.add_argument('--image',help='Offline read-only image test')
    p.add_argument('--timeout',type=int,default=1800)
    p.add_argument('--reopen-activity',action='store_true',help='Close verified activity page and reopen before Board')
    a=p.parse_args(argv)
    if a.image:
        print(json.dumps(board_state(read_image(a.image)),indent=2)); return
    if sys.platform!='win32': raise RuntimeError('Live capture requires Windows.')
    u=ctypes.windll.user32
    try: u.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except AttributeError: u.SetProcessDPIAware()
    u.GetForegroundWindow.restype=ctypes.c_void_p
    import mss
    import pyautogui as pg
    pg.FAILSAFE=True
    foreground=expected_foreground
    deadline=time.monotonic()+max(1,a.timeout)+5
    def guard():
        if u.GetAsyncKeyState(0x1B)&0x8000: raise RuntimeError('Cancelled by Esc.')
        pg.failSafeCheck()
        if foreground is not None and u.GetForegroundWindow()!=foreground:
            raise RuntimeError('Foreground changed; stopped.')
        if time.monotonic()>deadline: raise RuntimeError('Timeout; completion not verified.')
    def wait(seconds):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            guard(); time.sleep(min(.1,max(0,end-time.monotonic())))
    print(f'Board workflow v0.10. Starting in {start_delay} seconds.')
    print('INPUT ENABLED. Hold Esc or move mouse to corner to stop.' if a.run else 'READ ONLY.')
    wait(start_delay); guard(); foreground=u.GetForegroundWindow()
    cls=getattr(mss,'MSS',None) or mss.mss
    with cls() as cap:
        mon=next((m for m in cap.monitors[1:] if m['left']==0 and m['top']==0),None)
        if mon is None or tuple(pg.size())!=(mon['width'],mon['height']):
            raise RuntimeError('Primary capture/mouse dimensions differ.')
        def grab():
            guard(); return np.asarray(cap.grab(mon))[:,:,:3].copy()
        def report(state,frame,error=None):
            save_image('board_workflow_last.png',frame)
            data={'state':state,'completion_verified':state=='completed',
                  'observation':board_state(frame),'error':error,
                  'time_utc':datetime.now(timezone.utc).isoformat()}
            (ROOT/'captures/board_run_result.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
            print(json.dumps(data,indent=2))
            return data
        def click(detector):
            verified_click(detector,grab,wait,guard,pg.click)
        def target(expected):
            def inner(f):
                s=board_state(f)
                if s['state']!=expected: raise BoardStateChanged('Board state changed; no click.')
                return s['score'],s['box']
            return inner
        def open_menu():
            t=read_image(ROOT/'assets/templates/activity.png')
            click(lambda f:detect(f,t))
            for _ in range(20):
                if activity_page(grab()): return
                wait(.5)
            raise RuntimeError('Activity did not open; no repeated click.')
        def scan():
            for delta in (0,6,6,-3,-3,-3,-3,-3,-3):
                if not activity_page(grab()): raise RuntimeError('Activity page lost.')
                if delta:
                    guard(); pg.moveTo(mon['width']*.45,mon['height']*.55,.15)
                    pg.scroll(delta); wait(.6)
                s=board_state(grab())
                if s['state'] in ('pending','completed'):
                    wait(.3)
                    if board_state(grab())['state']==s['state']: return s
            raise RuntimeError('Board card not verified after bounded scrolling.')
        try:
            f=grab()
            if not a.run: report(board_state(f)['state'],f); return
            if a.reopen_activity:
                if not activity_page(grab()):
                    raise RuntimeError('Expected Activity page at Guild handoff.')
                guard(); pg.press('esc'); wait(2)
                if activity_page(grab()) or not world_visible(grab()):
                    raise RuntimeError('World not verified after closing Activity.')
                open_menu()
            go_sent=start_sent=confirm_sent=False
            phase_end=time.monotonic()+120
            while True:
                f=grab(); s=board_state(f); state=s['state']
                if activity_page(f):
                    card=scan()
                    if card['state']=='completed': return report('completed',grab())
                    if confirm_sent:
                        # Activity is still pending: close this verified page and
                        # allow the game's automatic work to continue.
                        guard(); pg.press('esc'); wait(2)
                        if activity_page(grab()): raise RuntimeError('Could not close activity page.')
                        wait(30); continue
                    if go_sent or start_sent: raise RuntimeError('Unexpected return to pending activity.')
                    click(target('pending')); go_sent=True
                    print('Go sent. Waiting for automatic travel.')
                    phase_end=time.monotonic()+120; continue
                if state=='confirm' and not confirm_sent:
                    click(target('confirm')); confirm_sent=True
                    save_image('board_after_confirm.png',grab())
                    print('Confirm sent. Waiting for game Auto; not yet completed.')
                    wait(30); continue
                if state=='start' and not start_sent and not confirm_sent:
                    click(target('start')); start_sent=True
                    save_image('board_after_start.png',grab())
                    phase_end=time.monotonic()+20; continue
                if world_visible(f):
                    if confirm_sent: open_menu(); continue
                    if not go_sent and not start_sent: open_menu(); continue
                if not confirm_sent and time.monotonic()>phase_end:
                    raise RuntimeError('Travel/start/confirmation not observed in time.')
                wait(2)
        except Exception as error:
            report('stopped_unverified',np.asarray(cap.grab(mon))[:,:,:3].copy(),str(error))
            raise


if __name__=='__main__': main()
