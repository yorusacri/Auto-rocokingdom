import random
import time
import traceback

import interception
import win32gui

_interception_ready = False
_interception_failed_logged = False
_click_failed_logged = False


def _ensure_interception():
    global _interception_ready, _interception_failed_logged
    if not _interception_ready:
        try:
            interception.auto_capture_devices()
            _interception_ready = True
        except Exception as e:
            if not _interception_failed_logged:
                print(f"[错误] Interception 驱动初始化失败: {e}")
                print(traceback.format_exc())
                _interception_failed_logged = True
            raise


def press_once(hwnd: int, key: str) -> None:
    """按下并释放一个键（驱动级）。"""
    if not key:
        return
    _ensure_interception()
    interception.key_down(key, delay=0)
    time.sleep(random.uniform(0.04, 0.10))
    interception.key_up(key, delay=0)


def click_at(hwnd: int, x: int | None = None, y: int | None = None) -> bool:
    """在窗口客户区坐标 (x, y) 处点击（驱动级）。不传坐标则在当前位置点击。"""
    global _click_failed_logged
    try:
        _ensure_interception()
        if x is not None and y is not None:
            sx, sy = win32gui.ClientToScreen(hwnd, (x, y))
            interception.click(
                sx + random.randint(-2, 2),
                sy + random.randint(-2, 2),
                delay=random.uniform(0.05, 0.12),
            )
        else:
            interception.mouse_down("left")
            time.sleep(random.uniform(0.20, 0.40))
            interception.mouse_up("left")
        return True
    except Exception as e:
        if not _click_failed_logged:
            print(f"[错误] 输入操作失败: {e}")
            print(traceback.format_exc())
            _click_failed_logged = True
        return False
