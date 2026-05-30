"""Force Edge browser for manual testing.  No source code changes.

Usage: uv run python tests/manual_test_edge.py

Patches eel.chrome.find_path() to return None so Eel falls back to Edge.
"""
import os
import sys

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import eel.chrome
import eel.browsers

_stderr = sys.stderr


def _log(msg: str) -> None:
    _stderr.write(f"[test] {msg}\n")
    _stderr.flush()


def _fake_find_path():
    _log("chrome.find_path() → 返回 None (模拟 Chrome 未安装)")
    return None


if __name__ == "__main__":
    _log("=== 手动测试：强制使用 Edge 浏览器 ===")

    eel.browsers._browser_paths.pop("chrome", None)
    eel.chrome.find_path = _fake_find_path
    _log("已 patch chrome.find_path")
    _log("原始 sys.stdout type: %s" % type(sys.stdout).__name__)

    from core.gui import run_gui

    _log("正在启动 run_gui()...")

    try:
        run_gui()
    except Exception as exc:
        _log(f"异常: {type(exc).__name__}: {exc}")
        import traceback
        traceback.print_exc(file=_stderr)
        raise
