"""Home entry v0.9: open expanded bottom-right menu before running.
Only Home and Return Home are clicked. Farming is not implemented yet.
"""
import argparse
import ctypes
import json
import sys
import time
import numpy as np
from detect_activity import ROOT, read_image
from home_status import home_state
from open_activity import stable_target, save_image


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',action='store_true')
    p.add_argument('--image',help='Offline detection only')
    a=p.parse_args()
    if a.image:
        print(json.dumps(home_state(read_image(a.image)),indent=2)); return
    if sys.platform!='win32': raise RuntimeError('Live capture requires Windows.')
    u=ctypes.windll.user32
    try: u.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except AttributeError: u.SetProcessDPIAware()
    u.GetForegroundWindow.restype=ctypes.c_void_p
    import mss
    import pyautogui as pg
    pg.FAILSAFE=True
    foreground=None
    def guard():
        if u.GetAsyncKeyState(0x1B)&0x8000: raise RuntimeError('Cancelled by Esc.')
        pg.failSafeCheck()
        if foreground is not None and u.GetForegroundWindow()!=foreground:
            raise RuntimeError('Foreground changed; stopped.')
    def wait(seconds):
        end=time.monotonic()+seconds
        while time.monotonic()<end:
            guard(); time.sleep(.1)
    print('Home entry v0.9. Open bottom-right expanded menu; switch to game in 5 seconds.')
    print('INPUT ENABLED: at most two clicks. Esc or mouse corner stops.' if a.run else 'READ ONLY.')
    wait(5); foreground=u.GetForegroundWindow()
    cls=getattr(mss,'MSS',None) or mss.mss
    with cls() as cap:
        mon=next((m for m in cap.monitors[1:] if m['left']==0 and m['top']==0),None)
        if mon is None or tuple(pg.size())!=(mon['width'],mon['height']):
            raise RuntimeError('Primary capture/mouse dimensions differ.')
        def grab():
            guard(); return np.asarray(cap.grab(mon))[:,:,:3].copy()
        def report(state,error=None):
            f=np.asarray(cap.grab(mon))[:,:,:3].copy()
            save_image('home_workflow_last.png',f)
            data={'state':state,'completion_verified':False,'observation':home_state(f),'error':error}
            (ROOT/'captures/home_run_result.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
            print(json.dumps(data,indent=2))
        def click(expected):
            first=home_state(grab()); wait(.3); second=home_state(grab())
            if first['state']!=expected or second['state']!=expected:
                raise RuntimeError('Home target changed; no click.')
            point=stable_target((first['score'],first['box']),(second['score'],second['box']))
            guard(); pg.click(*point); wait(1)
        try:
            state=home_state(grab())['state']
            if not a.run: report(state); return
            if state=='home_menu':
                click('home_menu')
                for _ in range(20):
                    if home_state(grab())['state']=='return_home': break
                    wait(.5)
                else: raise RuntimeError('Home page not verified; no repeated click.')
            elif state!='return_home':
                raise RuntimeError('Open expanded menu showing Home, or Home main page.')
            click('return_home')
            wait(20)
            report('return_sent_unverified')
            print('Entry test stopped. Review home_workflow_last.png; food and farming not started.')
        except Exception as error:
            report('stopped_unverified',str(error)); raise


if __name__=='__main__': main()
