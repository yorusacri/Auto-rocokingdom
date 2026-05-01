from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    # A visible window title keyword for your game client.
    window_title_keyword: str = "洛克王国：世界"

    # Reference resolution for template matching.
    # 2560x1600 is recommended for best matching accuracy.
    ref_width: int = 2560
    ref_height: int = 1600
    require_exact_resolution: bool = False

    # Polling interval must be <= 5.0 seconds per user requirement.
    poll_interval_sec: float = 2.0

    # Trigger exactly one key press on state transition.
    press_key: str = "x"
    # User requirement: If in battle, keep pressing X with 1.0s interval.
    trigger_cooldown_sec: float = 1.0

    # Input simulation method: "sendinput" (realistic, needs foreground) or "postmessage" (background, less stealth).
    input_method: str = "sendinput"

    # Escape mode uses physical mouse click only.
    # Keep game window and confirmation button visible when triggering escape.
    escape_click_method: str = "physical"

    # Detection settings.
    match_threshold: float = 0.40
    required_hits: int = 1
    release_misses: int = 2
    use_edge_match: bool = True

    # Detection ROI: right-bottom quarter of the window.
    roi_left_ratio: float = 0.5
    roi_top_ratio: float = 0.5
    roi_width_ratio: float = 0.5
    roi_height_ratio: float = 0.5

    # Templates.
    template_dir: str = "templates"
    template_pattern: str = "*.png"
    capture_template_name: str = "capture.png"
    pollute_capture_template_name: str = "pollute_capture.png"
    battle_end_template_names: tuple = ("elf_P.png", "missions.png", "heaths.png", "map.png")

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
    pollute_log_path: str = "logs/pollute_log.csv"

    # Runtime controls.


CONFIG = AppConfig()
