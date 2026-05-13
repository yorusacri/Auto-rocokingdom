import random
import time

import interception
import win32gui

_init = False


def _init():
    global _init
    if not _init:
        interception.auto_capture_devices()
        _init = True


def press_once(hwnd: int, key: str) -> None:
    """按下并释放一个键（驱动级，无需前台窗口）。"""
    if not key:
        return
    _init()
    interception.key_down(key, delay=0)
    time.sleep(random.uniform(0.04, 0.10))
    interception.key_up(key, delay=0)


def click_at(hwnd: int, x: int, y: int) -> bool:
    """在窗口客户区坐标 (x, y) 处点击（驱动级）。"""
    try:
        _init()
        sx, sy = win32gui.ClientToScreen(hwnd, (x, y))
        interception.click(
            sx + random.randint(-2, 2),
            sy + random.randint(-2, 2),
            delay=random.uniform(0.05, 0.12),
        )
        return True
    except Exception:
        return False
