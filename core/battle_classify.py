"""战斗开始时的延迟判型模块。

检测到战斗开始后，等待一小段时间让战斗 UI 完全加载，
再重新截图做类型判定和精灵 OCR，避免过渡帧导致误判。
"""

import time as _time
from dataclasses import dataclass
from typing import List

import cv2

from config import CONFIG
from core.capture import capture_window_bgr
from core.ocr import recognize_spirit_name
from core.vision import Template, best_match_score, normalize_template_name, preprocess
from core.window import get_client_rect_on_screen


@dataclass
class ClassifyResult:
    is_pollute: bool
    capture_score: float
    pollute_capture_score: float
    spirit_name: str


def classify_battle(
    hwnd: int,
    templates: List[Template],
    scale: float,
    width: int,
    height: int,
) -> ClassifyResult:
    """战斗开始后的延迟判型。

    等待 0.5s 后重新截图，对 capture/pollute_capture 重新匹配，
    并在污染战斗时做精灵名称 OCR。
    """
    _time.sleep(0.5)

    full_bgr = capture_window_bgr(hwnd)

    # 重新匹配战斗类型模板（使用与 engine 相同的 ROI）
    roi_l = max(0, min(width - 1, int(width * CONFIG.roi_left_ratio)))
    roi_t = max(0, min(height - 1, int(height * CONFIG.roi_top_ratio)))
    roi_w = max(1, min(width - roi_l, int(width * CONFIG.roi_width_ratio)))
    roi_h = max(1, min(height - roi_t, int(height * CONFIG.roi_height_ratio)))

    frame_bgr = full_bgr[roi_t:roi_t + roi_h, roi_l:roi_l + roi_w]
    frame_processed = preprocess(frame_bgr)
    _, _, _, all_matches = best_match_score(frame_processed, templates, scale=scale)

    capture_key = normalize_template_name(CONFIG.capture_template_name)
    pollute_key = normalize_template_name(CONFIG.pollute_capture_template_name)

    capture_score = 0.0
    pollute_capture_score = 0.0
    for name, score in all_matches:
        key = normalize_template_name(name)
        if key == capture_key:
            capture_score = score
        elif key == pollute_key:
            pollute_capture_score = score

    is_pollute = pollute_capture_score > capture_score

    spirit_name = ""
    if is_pollute:
        spirit_name = recognize_spirit_name(full_bgr, width, height)

    return ClassifyResult(
        is_pollute=is_pollute,
        capture_score=capture_score,
        pollute_capture_score=pollute_capture_score,
        spirit_name=spirit_name,
    )
