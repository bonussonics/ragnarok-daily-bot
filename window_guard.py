"""Pause inputs during brief focus loss. Never activate or trust another window."""
import ctypes
import time


def window_info(user32, hwnd):
    title=ctypes.create_unicode_buffer(256)
    cls=ctypes.create_unicode_buffer(128)
    pid=ctypes.c_ulong()
    user32.GetWindowTextW(ctypes.c_void_p(hwnd),title,len(title))
    user32.GetClassNameW(ctypes.c_void_p(hwnd),cls,len(cls))
    user32.GetWindowThreadProcessId(ctypes.c_void_p(hwnd),ctypes.byref(pid))
    return f'handle={hwnd}, pid={pid.value}, class={cls.value!r}, title={title.value!r}'


def require_foreground(user32, expected, failsafe, grace=2.0):
    current=user32.GetForegroundWindow()
    if current==expected: return
    print('Focus temporarily lost; input paused.',flush=True)
    end=time.monotonic()+grace
    while time.monotonic()<end:
        if user32.GetAsyncKeyState(0x1B)&0x8000: raise RuntimeError('Cancelled by Esc.')
        failsafe()
        if user32.GetForegroundWindow()==expected:
            print('Original game window regained focus.',flush=True)
            return
        time.sleep(.1)
    current=user32.GetForegroundWindow()
    raise RuntimeError('Foreground changed; stopped. Expected '+window_info(user32,expected)
                       +'; actual '+window_info(user32,current))
