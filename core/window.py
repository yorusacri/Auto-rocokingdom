import ctypes
from typing import List, Optional, Tuple

import win32gui

from config import CONFIG

# DPI Awareness
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass


def find_window_by_keyword(keyword: str) -> Optional[int]:
    matches = _enum_matching_windows(keyword)
    if not matches:
        return None
    # 标题最短的最可能是主窗口
    return min(matches, key=lambda m: len(m[1]))[0]


def list_windows_by_keyword(keyword: str) -> List[Tuple[int, str, Tuple[int, int, int, int]]]:
    """Return all matching windows with (hwnd, title, (x, y, w, h))."""
    results: List[Tuple[int, str, Tuple[int, int, int, int]]] = []
    for hwnd, title in _enum_matching_windows(keyword):
        rect = get_client_rect_on_screen(hwnd)
        results.append((hwnd, title, rect))
    return results


def _enum_matching_windows(keyword: str) -> list[tuple[int, str]]:
    matches: list[tuple[int, str]] = []

    def _enum_handler(hwnd: int, _ctx: object) -> None:
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        if title and keyword in title:
            matches.append((hwnd, title))

    win32gui.EnumWindows(_enum_handler, None)
    return matches


def get_client_rect_on_screen(hwnd: int) -> Tuple[int, int, int, int]:
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    client_w = right - left
    client_h = bottom - top
    screen_left, screen_top = win32gui.ClientToScreen(hwnd, (0, 0))
    return screen_left, screen_top, client_w, client_h
