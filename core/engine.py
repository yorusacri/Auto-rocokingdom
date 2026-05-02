import random
import time as _time
from typing import Dict, List, Tuple

import cv2

from config import CONFIG
from core.battle_classify import classify_battle
from core.capture import capture_window_bgr
from core.input import press_once
from core.pollute_logger import log_mode_start, log_pollute_battle
from core.vision import (
    Template,
    best_match_score,
    load_templates,
    normalize_poll_interval,
    normalize_template_name,
    preprocess,
    match_single,
)

# Templates excluded from action detection scoring
_ACTION_EXCLUDE_KEYS = {
    "yes.png",             # escape mode click position only
    "qiudaidai.png",       # teammate reconnect only
    "capture.png",         # battle type classification only
    "pollute_capture.png", # battle type classification only
}

from core.util import _ts
from core.window import find_window_by_keyword, get_client_rect_on_screen
from modes.base import BaseMode, BattleEvent

_SEP = "══════════════════════════════════════════════════════════"

_BATTLE_END_ROI = {
    "elf_p.png": (0.5, 0.0, 0.5, 0.5),
    "missions.png": (0.5, 0.0, 0.5, 0.5),
    "map.png": (0.5, 0.0, 0.5, 0.5),
}


def _extract_roi(full_bgr, width: int, height: int, left_r: float, top_r: float, w_r: float, h_r: float):
    l = max(0, int(width * left_r))
    t = max(0, int(height * top_r))
    w = max(1, min(width - l, int(width * w_r)))
    h = max(1, min(height - t, int(height * h_r)))
    return full_bgr[t:t + h, l:l + w]


class Engine:
    def __init__(self, mode: BaseMode) -> None:
        self._mode = mode

    def run(self) -> None:
        print(f"[{_ts()}] 检测器已启动（模式: {self._mode.label}），按 Ctrl+C 退出。")
        log_mode_start(self._mode.label)

        templates = load_templates()
        interval = normalize_poll_interval(CONFIG.poll_interval_sec)
        capture_template_key = normalize_template_name(CONFIG.capture_template_name)
        pollute_capture_template_key = normalize_template_name(CONFIG.pollute_capture_template_name)
        reconnect_template_key = normalize_template_name(CONFIG.reconnect_template_name)
        loaded_template_keys = {normalize_template_name(t.name) for t in templates}

        battle_end_keys = {}
        for raw_name in CONFIG.battle_end_template_names:
            key = normalize_template_name(raw_name)
            roi = _BATTLE_END_ROI.get(key, (0.5, 0.0, 0.5, 0.5))
            battle_end_keys[key] = roi

        if self._mode.name == "smart":
            if capture_template_key not in loaded_template_keys:
                print(f"[{_ts()}] [警告] 智能模式缺少普通战斗模板: {CONFIG.capture_template_name}")
            if pollute_capture_template_key not in loaded_template_keys:
                print(f"[{_ts()}] [警告] 智能模式缺少污染战斗模板: {CONFIG.pollute_capture_template_name}")

        in_battle = False
        last_trigger_time = 0.0
        battle_count = 0
        pollute_count = 0

        while True:
            hwnd = find_window_by_keyword(CONFIG.window_title_keyword)
            if hwnd is None:
                print(f"[{_ts()}] [警告] 未找到游戏窗口: {CONFIG.window_title_keyword}")
                _time.sleep(interval)
                continue

            left, top, width, height = get_client_rect_on_screen(hwnd)
            if width <= 0 or height <= 0:
                print(f"[{_ts()}] [警告] 窗口尺寸无效: {width}x{height}")
                _time.sleep(interval)
                continue

            scale = width / CONFIG.ref_width

            full_window_bgr = capture_window_bgr(hwnd)

            roi_left = int(width * CONFIG.roi_left_ratio)
            roi_top = int(height * CONFIG.roi_top_ratio)
            roi_w = int(width * CONFIG.roi_width_ratio)
            roi_h = int(height * CONFIG.roi_height_ratio)

            roi_left = max(0, min(width - 1, roi_left))
            roi_top = max(0, min(height - 1, roi_top))
            roi_w = max(1, min(width - roi_left, roi_w))
            roi_h = max(1, min(height - roi_top, roi_h))

            frame_bgr = full_window_bgr[roi_top:roi_top + roi_h, roi_left:roi_left + roi_w]
            frame_processed = preprocess(frame_bgr)

            _, _, _, all_matches = best_match_score(frame_processed, templates, scale=scale)

            capture_score = next(
                (s for n, s in all_matches if normalize_template_name(n) == capture_template_key),
                0.0,
            )
            pollute_capture_score = next(
                (s for n, s in all_matches if normalize_template_name(n) == pollute_capture_template_key),
                0.0,
            )

            # ── Battle-end detection ──
            roi_cache: Dict[tuple, object] = {}
            end_scores: List[Tuple[str, float]] = []
            for key, roi_params in battle_end_keys.items():
                cache_key = roi_params
                if cache_key not in roi_cache:
                    roi_bgr = _extract_roi(full_window_bgr, width, height, *roi_params)
                    roi_cache[cache_key] = preprocess(roi_bgr)
                roi_processed = roi_cache[cache_key]
                s = match_single(roi_processed, templates, key, scale=scale)
                end_scores.append((key, s))

            best_end_score = max((s for _, s in end_scores), default=0.0)
            best_end_name = max(end_scores, key=lambda x: x[1])[0] if end_scores else ""

            # Action score
            excluded_keys = set(battle_end_keys.keys()) | _ACTION_EXCLUDE_KEYS
            action_score = -1.0
            action_template = ""
            for tpl_name, tpl_score in all_matches:
                tpl_key = normalize_template_name(tpl_name)
                if tpl_key in excluded_keys:
                    continue
                if tpl_score > action_score:
                    action_score = tpl_score
                    action_template = tpl_name

            is_hit = action_score >= CONFIG.match_threshold

            # ── Battle start ──
            if not in_battle and is_hit:
                battle_count += 1
                print(
                    f"[{_ts()}] >>> 战斗开始（第 {battle_count} 场，初始分数"
                    f" capture={capture_score:.3f} pollute_capture={pollute_capture_score:.3f}）"
                )

                # 延迟 0.5s 后重新截图判型，避免过渡帧误判
                result = classify_battle(hwnd, templates, scale, width, height)

                is_pollute_battle = result.is_pollute
                if is_pollute_battle:
                    pollute_count += 1
                    log_pollute_battle(pollute_count, result.spirit_name)

                print(_SEP)
                print(
                    f"[{_ts()}] >>> 判型完成（第 {battle_count} 场，"
                    f"{'污染' if is_pollute_battle else '普通'}，"
                    f"累计污染 {pollute_count} 次"
                    f"{f'，精灵：{result.spirit_name}' if is_pollute_battle else ''}）"
                    f"  [capture={result.capture_score:.3f} pollute_capture={result.pollute_capture_score:.3f}]"
                )

                event = BattleEvent(
                    hwnd=hwnd,
                    templates=templates,
                    scale=scale,
                    battle_count=battle_count,
                    pollute_count=pollute_count,
                    capture_score=result.capture_score,
                    pollute_capture_score=result.pollute_capture_score,
                    window_width=width,
                    window_height=height,
                )
                self._mode.on_battle_start(event)

                in_battle = True

            # ── Battle end ──
            end_detected = best_end_score >= CONFIG.match_threshold
            if in_battle and end_detected:
                print(f"[{_ts()}] <<< 战斗结束（第 {battle_count} 场，{best_end_score:.3f} by {best_end_name}）")
                print(_SEP)

                event = BattleEvent(
                    hwnd=hwnd,
                    templates=templates,
                    scale=scale,
                    battle_count=battle_count,
                    pollute_count=pollute_count,
                    capture_score=capture_score,
                    pollute_capture_score=pollute_capture_score,
                    window_width=width,
                    window_height=height,
                )
                self._mode.on_battle_end(event)
                in_battle = False

            # ── Per-tick display ──
            if in_battle:
                print(
                    f"[{_ts()}] 行动检测: {action_template}={action_score:.3f}  "
                    f"结束检测: {best_end_name}={best_end_score:.3f}"
                    f"{' ← 触发' if end_detected else ''}"
                )
            else:
                # ── Teammate reconnect ──
                center_roi = CONFIG.reconnect_center_roi
                center_bgr = _extract_roi(full_window_bgr, width, height, *center_roi)
                center_gray = cv2.cvtColor(center_bgr, cv2.COLOR_BGR2GRAY)
                reconnect_score = match_single(center_gray, templates, reconnect_template_key, scale=scale)

                print(f"[{_ts()}] 行动检测: {action_template}={action_score:.3f}  同行检测: {reconnect_score:.3f}")

                if reconnect_score >= CONFIG.reconnect_threshold:
                    print(f"[{_ts()}] 检测到同行请求，按 F 确认（qiudaidai={reconnect_score:.3f}）")
                    press_once(hwnd, CONFIG.reconnect_accept_key)

            event = BattleEvent(
                hwnd=hwnd,
                templates=templates,
                scale=scale,
                battle_count=battle_count,
                pollute_count=pollute_count,
                capture_score=capture_score,
                pollute_capture_score=pollute_capture_score,
                window_width=width,
                window_height=height,
            )

            # ── Action within battle ──
            now = _time.time()
            cooldown_ready = (now - last_trigger_time) >= CONFIG.trigger_cooldown_sec

            if in_battle and is_hit and cooldown_ready:
                extra_cooldown = self._mode.on_action(event, is_hit, action_score)
                if extra_cooldown is not None:
                    last_trigger_time = now + extra_cooldown
                else:
                    last_trigger_time = now

            jitter = random.uniform(-interval * 0.15, interval * 0.15)
            _time.sleep(max(0.05, interval + jitter))
