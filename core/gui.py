"""Eel-based GUI backend for Auto-Roco.

Runs the Engine in a background thread, captures stdout for the log panel,
and pushes state updates to the frontend via Eel's websocket bridge.
"""

import os
import sys
import threading
import time as _time

import eel

from config import CONFIG
from core.engine import Engine
from core.pollute_logger import log_mode_start
from core.util import _ts

_engine: Engine | None = None
_engine_thread: threading.Thread | None = None
_stdout_buffer: list[str] = []
_stdout_lock = threading.Lock()
_original_stdout = sys.stdout


class _TeeStdout:
    """Writes to both original stdout and an internal buffer for the GUI log."""

    def __init__(self, original):
        self._original = original
        self._line = ""

    def write(self, s: str) -> None:
        self._original.write(s)
        self._original.flush()
        with _stdout_lock:
            self._line += s
            if "\n" in self._line:
                parts = self._line.split("\n")
                self._line = parts[-1]
                for line in parts[:-1]:
                    if line.strip():
                        _stdout_buffer.append(line)

    def flush(self) -> None:
        self._original.flush()


def _drain_log() -> list[str]:
    with _stdout_lock:
        lines = _stdout_buffer[:]
        _stdout_buffer.clear()
    return lines


def _classify_log_level(line: str) -> str:
    if "战斗开始" in line:
        return "battle-start"
    if "战斗结束" in line:
        return "battle-end"
    if "污染" in line and ("判型" in line or "精灵" in line):
        return "pollute"
    if "警告" in line or "错误" in line:
        return "warning"
    if "检测到同行" in line:
        return "info"
    return "info"


def _engine_thread_func(engine: Engine) -> None:
    sys.stdout = _TeeStdout(_original_stdout)
    try:
        print(f"[{_ts()}] 检测器已启动（模式: {engine._mode.label}），按暂停按钮可暂停。")
        while engine.is_running:
            engine.tick()
            jitter = 0  # GUI mode: timing is handled by the spawned loop
            _time.sleep(max(0.05, engine._interval * 0.3))
    except Exception as e:
        print(f"[{_ts()}] [错误] 引擎异常: {e}")
    finally:
        sys.stdout = _original_stdout


# ═══════════════════════════════════════════════════════════════
# Eel-exposed functions — called from JavaScript
# ═══════════════════════════════════════════════════════════════

def _find_mode_cls(name: str):
    """Find a mode class by its ``name`` property."""
    from modes import MODE_REGISTRY
    for cls in MODE_REGISTRY.values():
        if cls().name == name:
            return cls
    return MODE_REGISTRY["1"]


@eel.expose
def start_engine(hwnd: int, mode_key: str = "smart",
                 pollute_action: str = "gather",
                 normal_action: str = "escape") -> None:
    global _engine, _engine_thread

    try:
        if _engine is not None:
            stop_engine()

        if mode_key == "smart":
            from modes.smart import SmartMode
            mode = SmartMode(pollute_action=pollute_action,
                             normal_action=normal_action)
        else:
            cls = _find_mode_cls(mode_key)
            mode = cls()

        if hwnd is None or hwnd == 0:
            eel.addLog("error", "无效的窗口句柄，请刷新窗口列表后重新选择")
            return

        # Resolve window title for logging
        import win32gui
        win_title = win32gui.GetWindowText(hwnd) or f"HWND={hwnd}"

        with _stdout_lock:
            _stdout_buffer.clear()

        _engine = Engine(mode, hwnd=hwnd)
        print(f"[{_ts()}] [GUI] 已选择窗口: {win_title}")
        log_mode_start(mode.label)
        _engine_thread = threading.Thread(target=_engine_thread_func,
                                          args=(_engine,), daemon=True)
        _engine_thread.start()
        eel.setRunning(True)
    except Exception as exc:
        import traceback
        eel.addLog("error", f"启动引擎失败: {exc}")
        traceback.print_exc()


@eel.expose
def stop_engine() -> None:
    global _engine, _engine_thread
    if _engine is not None:
        eel.addLog("info", "引擎已停止")
        _engine.stop()
        _engine = None
    _engine_thread = None
    eel.setRunning(False)


@eel.expose
def toggle_pause() -> None:
    if _engine is None:
        return
    paused = _engine.toggle_pause()
    eel.setPausedUI(paused)
    if paused:
        eel.addLog("pause", "⏸ 引擎已暂停")
    else:
        eel.addLog("resume", "▶ 引擎已恢复")


@eel.expose
def set_mode(mode_key: str) -> None:
    if _engine is not None:
        eel.addLog("warning", "运行中无法切换模式，请先停止引擎再切换")

@eel.expose
def switch_window(hwnd: int) -> None:
    if _engine is not None:
        _engine.switch_window(hwnd)
        import win32gui
        title = win32gui.GetWindowText(hwnd) or str(hwnd)
        eel.addLog("info", f"已切换目标窗口: {title}")


@eel.expose
def set_pollute_action(action: str) -> None:
    if _engine is not None and hasattr(_engine._mode, 'set_pollute_action'):
        _engine._mode.set_pollute_action(action)
        eel.addLog("info", f"污染行为已切换: {action}")


@eel.expose
def set_normal_action(action: str) -> None:
    if _engine is not None and hasattr(_engine._mode, 'set_normal_action'):
        _engine._mode.set_normal_action(action)
        eel.addLog("info", f"普通行为已切换: {action}")


@eel.expose
def get_settings() -> dict:
    """Return current config values for the settings panel."""
    return {
        "match_threshold": CONFIG.match_threshold,
        "poll_interval_sec": CONFIG.poll_interval_sec,
    }

@eel.expose
def save_settings(match_threshold: float, poll_interval_sec: float) -> None:
    """Save detection settings to user_prefs.json (takes effect on next start)."""
    from config import save_prefs
    save_prefs({
        "match_threshold": match_threshold,
        "poll_interval_sec": poll_interval_sec,
    })
    eel.addLog("info", f"设置已保存: 阈值={match_threshold}, 间隔={poll_interval_sec}s（需重启引擎生效）")

@eel.expose
def get_gui_prefs() -> dict:
    """Return saved GUI preferences (mode, actions)."""
    from config import load_prefs
    prefs = load_prefs()
    return {
        "mode": prefs.get("gui_mode", "smart"),
        "pollute_action": prefs.get("gui_pollute_action", "gather"),
        "normal_action": prefs.get("gui_normal_action", "escape"),
    }

@eel.expose
def save_gui_prefs(mode: str, pollute_action: str, normal_action: str) -> None:
    """Persist GUI mode/action preferences."""
    from config import save_prefs
    save_prefs({
        "gui_mode": mode,
        "gui_pollute_action": pollute_action,
        "gui_normal_action": normal_action,
    })

@eel.expose
def list_windows() -> None:
    """Push matching game windows to the frontend via on_windows_listed callback."""
    print(f"[{_ts()}] [GUI] list_windows 被调用")
    try:
        from core.window import list_windows_by_keyword
        windows = list_windows_by_keyword(CONFIG.window_title_keyword)
        print(f"[{_ts()}] [GUI] 找到 {len(windows)} 个匹配窗口")
        result = []
        for hwnd, title, (x, y, w, h) in windows:
            result.append({
                "hwnd": hwnd,
                "title": title,
                "x": x, "y": y,
                "width": w, "height": h,
            })
        print(f"[{_ts()}] [GUI] 准备推送 {len(result)} 个窗口到前端...")
        eel.onWindowsListed(result)
        print(f"[{_ts()}] [GUI] 推送完成")
    except Exception as exc:
        import traceback
        print(f"[{_ts()}] [GUI] list_windows 异常: {exc}")
        traceback.print_exc()
        try:
            eel.onWindowsListed([])
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════
# Background loop: push log + stats to frontend
# ═══════════════════════════════════════════════════════════════

def _push_loop() -> None:
    """Spawned by Eel; runs alongside the engine thread."""
    while True:
        # Push log lines
        lines = _drain_log()
        for line in lines:
            level = _classify_log_level(line)
            eel.addLog(level, line)

        # Push stats
        if _engine is not None:
            state = _engine._snapshot()
            eel.updateStats(state)

        eel.sleep(0.3)


# ═══════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════

def run_gui() -> None:
    if getattr(sys, "frozen", False):
        # PyInstaller onedir: data next to exe
        _web_dir = os.path.join(os.path.dirname(sys.executable), "web")
        if not os.path.isdir(_web_dir):
            # Fallback: _MEIPASS for onefile, or CWD
            _base = getattr(sys, "_MEIPASS", os.getcwd())
            _web_dir = os.path.join(_base, "web")
    else:
        _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _web_dir = os.path.join(_base, "web")
    _idx = os.path.join(_web_dir, "index.html")
    if not os.path.isfile(_idx):
        raise FileNotFoundError(
            f"未找到 {_idx}\n"
            f"请确认 web/ 文件夹与 exe 在同一目录"
        )
    eel.init(_web_dir)
    eel.spawn(_push_loop)
    eel.start("index.html", mode="chrome", size=(1050, 720),
              port=0, block=True)
