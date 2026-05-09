import random
import time

import pydirectinput as pdi
import win32api
import win32con
import win32gui

from config import CONFIG


def _rand_delay(lo: float = 0.03, hi: float = 0.08) -> float:
    return random.uniform(lo, hi)


def _resolve_vk(key: str) -> int | None:
    if key.lower() == "esc":
        return win32con.VK_ESCAPE
    if len(key) == 1:
        return win32api.VkKeyScan(key) & 0xFF
    return None


# ── SendInput 方式 ──

def _press_sendinput(hwnd: int, vk_code: int) -> None:
    pdi.keyDown(vk_code)
    time.sleep(_rand_delay(0.04, 0.10))
    pdi.keyUp(vk_code)


def _click_sendinput(hwnd: int, x: int | None = None, y: int | None = None) -> bool:
    if x is not None and y is not None:
        screen_pos = win32gui.ClientToScreen(hwnd, (x, y))
        pdi.moveTo(screen_pos[0], screen_pos[1])
        time.sleep(_rand_delay(0.03, 0.10))
    pdi.mouseDown()
    time.sleep(_rand_delay(0.10, 0.20))
    pdi.mouseUp()
    return True


# ── PostMessage 方式（可后台，拟真度低） ──

def _press_postmessage(hwnd: int, vk_code: int) -> None:
    scan_code = win32api.MapVirtualKey(vk_code, 0)
    lparam_down = 1 | (scan_code << 16)
    lparam_up = 1 | (scan_code << 16) | (1 << 30) | (1 << 31)

    win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, vk_code, lparam_down)
    time.sleep(_rand_delay(0.03, 0.08))
    win32gui.PostMessage(hwnd, win32con.WM_KEYUP, vk_code, lparam_up)


# ── 公共入口 ──

def press_once(hwnd: int, key: str) -> None:
    vk_code = _resolve_vk(key)
    if vk_code is None:
        return
    if CONFIG.input_method == "postmessage":
        _press_postmessage(hwnd, vk_code)
    else:
        _press_sendinput(hwnd, vk_code)


def click_at(hwnd: int, x: int | None = None, y: int | None = None) -> bool:
    try:
        return _click_sendinput(hwnd, x, y)
    except Exception:
        return False
