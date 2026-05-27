import json
import os
import sys
from dataclasses import dataclass, field


def _base_dir() -> str:
    """Return the directory that contains templates/."""
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), "_internal")
    return os.path.dirname(os.path.abspath(__file__))


def _exe_dir() -> str:
    """Return the directory next to the exe (writable, for logs)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


_PREFS_PATH = os.path.join(_exe_dir(), "user_prefs.json")


def load_prefs() -> dict:
    try:
        with open(_PREFS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    except OSError as e:
        if sys.stdout is not None:
            print(f"[警告] 无法读取配置文件 {_PREFS_PATH}: {e}")
        return {}


def save_prefs(prefs: dict) -> None:
    """Save all preferences to user_prefs.json."""
    try:
        full_prefs = load_prefs()
        full_prefs.update(prefs)
        with open(_PREFS_PATH, "w", encoding="utf-8") as f:
            json.dump(full_prefs, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[警告] 无法保存配置文件 {_PREFS_PATH}: {e}")


def _get_prefs_value(key: str, default, prefs: dict):
    """Get value from prefs dict, returning default if key not present."""
    return prefs.get(key, default)


_USER_PREFS = load_prefs()


@dataclass
class AppConfig:
    # A visible window title keyword for your game client.
    window_title_keyword: str = _get_prefs_value("window_title_keyword", "洛克王国：世界", _USER_PREFS)

    # Reference resolution for template matching.
    # 2560x1600 is recommended for best matching accuracy.
    ref_width: int = _get_prefs_value("ref_width", 2560, _USER_PREFS)
    ref_height: int = _get_prefs_value("ref_height", 1600, _USER_PREFS)
    # Polling interval must be <= 5.0 seconds per user requirement.
    poll_interval_sec: float = _get_prefs_value("poll_interval_sec", 2.0, _USER_PREFS)

    # Key to press for gather action.
    press_key: str = _get_prefs_value("press_key", "x", _USER_PREFS)
    # Cooldown between action triggers.
    trigger_cooldown_sec: float = _get_prefs_value("trigger_cooldown_sec", 1.0, _USER_PREFS)

    # Detection settings.
    match_threshold: float = _get_prefs_value("match_threshold", 0.40, _USER_PREFS)
    use_edge_match: bool = _get_prefs_value("use_edge_match", True, _USER_PREFS)

    # Detection ROI: right-bottom quarter of the window.
    roi_left_ratio: float = 0.5
    roi_top_ratio: float = 0.5
    roi_width_ratio: float = 0.5
    roi_height_ratio: float = 0.5

    # Templates.
    template_dir: str = field(default_factory=lambda: os.path.join(_base_dir(), "templates"))
    template_pattern: str = "*.png"
    capture_template_name: str = "capture.png"
    pollute_capture_template_name: str = "pollute_capture.png"
    battle_end_template_names: tuple = ("elf_P.png", "missions.png", "map.png")

    # Teammate reconnect detection (non-battle state).
    reconnect_template_name: str = "qiudaidai.png"
    reconnect_accept_key: str = "f"
    reconnect_center_roi: tuple = (0.2, 0.2, 0.6, 0.6)  # (left, top, width, height)
    reconnect_threshold: float = 0.7

    # OCR spirit name detection ROI: top-right corner of the game window.
    ocr_roi_left_ratio: float = 0.85
    ocr_roi_top_ratio: float = 0.0
    ocr_roi_width_ratio: float = 0.15
    ocr_roi_height_ratio: float = 0.15

    # OCR preprocessing parameters.
    ocr_upscale_factor: float = 2.0
    ocr_fallback_text: str = "未知"

    # Pollution battle CSV log.
    pollute_log_path: str = field(default_factory=lambda: os.path.join(_exe_dir(), "logs", "pollute_log.csv"))

    # Runtime controls.


CONFIG = AppConfig()
