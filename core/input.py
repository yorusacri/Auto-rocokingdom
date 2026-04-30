import random
import time

try:
    import win32gui
except ImportError:
    win32gui = None

import ctypes
import ctypes.wintypes
import win32api
import win32con

# ---------- SendInput 常量 ----------
INPUT_KEYBOARD = 1
INPUT_MOUSE = 0
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_EXTENDEDKEY = 0x0001

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_ABSOLUTE = 0x8000

# 需要 EXTENDEDKEY 标志的虚拟键码
_EXTENDED_VK = {
    win32con.VK_RCONTROL, win32con.VK_RMENU,
    win32con.VK_INSERT, win32con.VK_DELETE,
    win32con.VK_HOME, win32con.VK_END,
    win32con.VK_PRIOR, win32con.VK_NEXT,
    win32con.VK_LEFT, win32con.VK_UP,
    win32con.VK_RIGHT, win32con.VK_DOWN,
    win32con.VK_NUMLOCK, win32con.VK_SNAPSHOT,
    win32con.VK_DIVIDE, win32con.VK_LWIN, win32con.VK_RWIN,
}


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.wintypes.WORD),
        ("wScan", ctypes.wintypes.WORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.wintypes.LONG),
        ("dy", ctypes.wintypes.LONG),
        ("mouseData", ctypes.wintypes.DWORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.wintypes.DWORD),
        ("union", _INPUT_UNION),
    ]


def _send_input(*inputs: INPUT):
    arr = (INPUT * len(inputs))(*inputs)
    ctypes.windll.user32.SendInput(len(arr), arr, ctypes.sizeof(INPUT))


def _rand_delay(lo: float = 0.03, hi: float = 0.08) -> float:
    return random.uniform(lo, hi)


def press_once(hwnd: int, key: str) -> None:
    if win32gui is None:
        return

    if key.lower() == "esc":
        vk_code = win32con.VK_ESCAPE
    elif len(key) == 1:
        vk_code = win32api.VkKeyScan(key) & 0xFF
    else:
        return

    scan_code = win32api.MapVirtualKey(vk_code, 0)
    flags_down = KEYEVENTF_SCANCODE
    flags_up = KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP
    if vk_code in _EXTENDED_VK:
        flags_down |= KEYEVENTF_EXTENDEDKEY
        flags_up |= KEYEVENTF_EXTENDEDKEY

    down = INPUT()
    down.type = INPUT_KEYBOARD
    down.union.ki.wVk = vk_code
    down.union.ki.wScan = scan_code
    down.union.ki.dwFlags = flags_down

    up = INPUT()
    up.type = INPUT_KEYBOARD
    up.union.ki.wVk = vk_code
    up.union.ki.wScan = scan_code
    up.union.ki.dwFlags = flags_up

    _send_input(down)
    time.sleep(_rand_delay(0.04, 0.10))
    _send_input(up)


def click_at(hwnd: int, x: int, y: int) -> bool:
    if win32gui is None:
        return True

    try:
        screen_pos = win32gui.ClientToScreen(hwnd, (x, y))
        sw = ctypes.windll.user32.GetSystemMetrics(0)
        sh = ctypes.windll.user32.GetSystemMetrics(1)

        # SendInput + ABSOLUTE 需要归一化到 0-65535
        abs_x = int(screen_pos[0] * 65535 / (sw - 1))
        abs_y = int(screen_pos[1] * 65535 / (sh - 1))

        # 带随机偏移，模拟手指不精确
        abs_x += random.randint(-2, 2)
        abs_y += random.randint(-2, 2)

        move = INPUT()
        move.type = INPUT_MOUSE
        move.union.mi.dx = abs_x
        move.union.mi.dy = abs_y
        move.union.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE

        down = INPUT()
        down.type = INPUT_MOUSE
        down.union.mi.dwFlags = MOUSEEVENTF_LEFTDOWN

        up = INPUT()
        up.type = INPUT_MOUSE
        up.union.mi.dwFlags = MOUSEEVENTF_LEFTUP

        _send_input(move)
        time.sleep(_rand_delay(0.05, 0.12))
        _send_input(down)
        time.sleep(_rand_delay(0.04, 0.09))
        _send_input(up)
        return True
    except Exception:
        return False
