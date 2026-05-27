import random
import threading
import time as _time
from typing import Dict, List, Tuple

import cv2
import numpy as np
import win32gui

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
    def __init__(self, mode: BaseMode, hwnd: int | None = None) -> None:
        self._mode = mode
        self._hwnd = hwnd
        self._paused = threading.Event()
        self._paused.set()
        self._stop_requested = False
        self._setup()

    def _setup(self) -> None:
        self._templates = load_templates()
        self._interval = normalize_poll_interval(CONFIG.poll_interval_sec)
        self._capture_template_key = normalize_template_name(CONFIG.capture_template_name)
        self._pollute_capture_template_key = normalize_template_name(CONFIG.pollute_capture_template_name)
        self._reconnect_template_key = normalize_template_name(CONFIG.reconnect_template_name)
        _loaded_keys = {normalize_template_name(t.name) for t in self._templates}

        self._battle_end_keys = {}
        for raw_name in CONFIG.battle_end_template_names:
            key = normalize_template_name(raw_name)
            roi = _BATTLE_END_ROI.get(key, (0.5, 0.0, 0.5, 0.5))
            self._battle_end_keys[key] = roi

        # Validate that config-referenced templates actually exist
        for ref_name in [self._capture_template_key, self._pollute_capture_template_key,
                         self._reconnect_template_key] + sorted(self._battle_end_keys):
            if ref_name not in _loaded_keys:
                print(f"[警告] 配置引用的模板未加载: {ref_name}，相关功能可能不可用")
        if self._reconnect_template_key not in _loaded_keys:
            print(f"[诊断] 同行检测模板未加载，同行重连功能已禁用")

        self._in_battle = False
        self._last_trigger_time = 0.0
        self._battle_count = 0
        self._pollute_count = 0
        self._last_action_template = ""
        self._last_action_score = 0.0
        self._last_end_name = ""
        self._last_end_score = 0.0
        self._last_reconnect_score = 0.0

    # ── Pause / Resume / Stop ──

    def pause(self) -> None:
        self._paused.clear()

    def resume(self) -> None:
        self._paused.set()

    def toggle_pause(self) -> bool:
        if self._paused.is_set():
            self.pause()
            return True
        else:
            self.resume()
            return False

    def switch_window(self, hwnd: int) -> None:
        self._hwnd = hwnd

    def stop(self) -> None:
        self._stop_requested = True
        self._paused.set()

    @property
    def is_paused(self) -> bool:
        return not self._paused.is_set()

    @property
    def is_running(self) -> bool:
        return not self._stop_requested

    def _wait_if_paused(self) -> None:
        while not self._stop_requested and not self._paused.is_set():
            _time.sleep(0.1)

    # ── Main loop ──

    def run(self) -> None:
        print(f"[{_ts()}] 检测器已启动（模式: {self._mode.label}），按 Ctrl+C 退出。")
        log_mode_start(self._mode.label)

        while not self._stop_requested:
            self._wait_if_paused()
            if self._stop_requested:
                break
            try:
                self._tick()
            except Exception as e:
                import traceback
                print(f"[{_ts()}] [错误] 循环异常: {e}")
                print(traceback.format_exc())
                _time.sleep(1.0)
            jitter = random.uniform(-self._interval * 0.15, self._interval * 0.15)
            _time.sleep(max(0.05, self._interval + jitter))

    def tick(self) -> dict:
        """Execute one iteration and return current state dict. For GUI mode."""
        self._wait_if_paused()
        if self._stop_requested:
            return self._snapshot()
        self._tick()
        return self._snapshot()

    def _snapshot(self) -> dict:
        return {
            "battle_count": self._battle_count,
            "pollute_count": self._pollute_count,
            "in_battle": self._in_battle,
            "action_template": self._last_action_template,
            "action_score": self._last_action_score,
            "end_name": self._last_end_name,
            "end_score": self._last_end_score,
            "reconnect_score": self._last_reconnect_score,
        }

    def _tick(self) -> None:
        if self._hwnd is not None:
            hwnd = self._hwnd
        else:
            hwnd = find_window_by_keyword(CONFIG.window_title_keyword)
            if hwnd is None:
                print(f"[{_ts()}] [警告] 未找到游戏窗口: {CONFIG.window_title_keyword}")
                return

        left, top, width, height = get_client_rect_on_screen(hwnd)
        if width <= 0 or height <= 0:
            actual_title = win32gui.GetWindowText(hwnd)
            print(f"[{_ts()}] [警告] 窗口尺寸无效: {width}x{height} ({actual_title})")
            return

        now = _time.time()
        scale = width / CONFIG.ref_width

        full_window_bgr = capture_window_bgr(hwnd)
        if not hasattr(self, '_capture_ok_logged'):
            if full_window_bgr.size <= 3:
                print(f"[诊断] 捕获图像数据为空，窗口可能被遮挡或未正确渲染")
            elif np.max(full_window_bgr) == 0:
                print(f"[诊断] 捕获图像全黑，窗口可能处于后台或最小化状态")
            self._capture_ok_logged = True

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

        _, _, _, all_matches = best_match_score(frame_processed, self._templates, scale=scale)

        capture_score = next(
            (s for n, s in all_matches if normalize_template_name(n) == self._capture_template_key),
            0.0,
        )
        pollute_capture_score = next(
            (s for n, s in all_matches if normalize_template_name(n) == self._pollute_capture_template_key),
            0.0,
        )

        # ── Battle-end detection ──
        roi_cache: Dict[tuple, object] = {}
        end_scores: List[Tuple[str, float]] = []
        for key, roi_params in self._battle_end_keys.items():
            cache_key = roi_params
            if cache_key not in roi_cache:
                roi_bgr = _extract_roi(full_window_bgr, width, height, *roi_params)
                roi_cache[cache_key] = preprocess(roi_bgr)
            roi_processed = roi_cache[cache_key]
            s = match_single(roi_processed, self._templates, key, scale=scale)
            end_scores.append((key, s))

        best_end_score = max((s for _, s in end_scores), default=0.0)
        best_end_name = max(end_scores, key=lambda x: x[1])[0] if end_scores else ""

        # Action score
        excluded_keys = set(self._battle_end_keys.keys()) | _ACTION_EXCLUDE_KEYS
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
        if not self._in_battle and is_hit:
            self._battle_count += 1
            print(
                f"[{_ts()}] >>> 战斗开始（第 {self._battle_count} 场）"
            )

            result = classify_battle(hwnd, self._templates, scale, width, height)

            is_pollute_battle = result.is_pollute
            if is_pollute_battle:
                self._pollute_count += 1
                log_pollute_battle(self._pollute_count, result.spirit_name)

            print(_SEP)
            print(
                f"[{_ts()}] >>> 判型完成（第 {self._battle_count} 场，"
                f"{'污染' if is_pollute_battle else '普通'}，"
                f"累计污染 {self._pollute_count} 次"
                f"{f'，精灵：{result.spirit_name}' if is_pollute_battle else ''}）"
            )

            event = BattleEvent(
                hwnd=hwnd,
                templates=self._templates,
                scale=scale,
                battle_count=self._battle_count,
                pollute_count=self._pollute_count,
                capture_score=result.capture_score,
                pollute_capture_score=result.pollute_capture_score,
                window_width=width,
                window_height=height,
                all_scores=all_matches,
                end_scores=end_scores,
            )
            self._mode.on_battle_start(event)

            self._in_battle = True

        # ── Battle end ──
        end_detected = best_end_score >= CONFIG.match_threshold
        if self._in_battle and end_detected:
            print(f"[{_ts()}] <<< 战斗结束（第 {self._battle_count} 场）")
            print(_SEP)

            event = BattleEvent(
                hwnd=hwnd,
                templates=self._templates,
                scale=scale,
                battle_count=self._battle_count,
                pollute_count=self._pollute_count,
                capture_score=capture_score,
                pollute_capture_score=pollute_capture_score,
                window_width=width,
                window_height=height,
                all_scores=all_matches,
                end_scores=end_scores,
            )
            self._mode.on_battle_end(event)
            self._in_battle = False

        # ── Teammate reconnect (non-battle) ──
        reconnect_score = 0.0
        if not self._in_battle:
            center_roi = CONFIG.reconnect_center_roi
            center_bgr = _extract_roi(full_window_bgr, width, height, *center_roi)
            center_gray = cv2.cvtColor(center_bgr, cv2.COLOR_BGR2GRAY)
            reconnect_score = match_single(center_gray, self._templates, self._reconnect_template_key, scale=scale)

            if reconnect_score >= CONFIG.reconnect_threshold:
                print(f"[{_ts()}] 触发: 同行确认 (F)")
                press_once(hwnd, CONFIG.reconnect_accept_key)

            non_battle_event = BattleEvent(
                hwnd=hwnd,
                templates=self._templates,
                scale=scale,
                battle_count=self._battle_count,
                pollute_count=self._pollute_count,
                capture_score=capture_score,
                pollute_capture_score=pollute_capture_score,
                window_width=width,
                window_height=height,
                all_scores=all_matches,
                end_scores=end_scores,
            )
            self._mode.on_non_battle_no_action(non_battle_event)

        event = BattleEvent(
            hwnd=hwnd,
            templates=self._templates,
            scale=scale,
            battle_count=self._battle_count,
            pollute_count=self._pollute_count,
            capture_score=capture_score,
            pollute_capture_score=pollute_capture_score,
            window_width=width,
            window_height=height,
            all_scores=all_matches,
            end_scores=end_scores,
        )

        # ── Action within battle ──
        action_taken = ""
        cooldown_ready = (now - self._last_trigger_time) >= CONFIG.trigger_cooldown_sec

        if self._in_battle and is_hit and cooldown_ready:
            extra_cooldown = self._mode.on_action(event, is_hit, action_score)
            if extra_cooldown is not None:
                self._last_trigger_time = now + extra_cooldown
            else:
                self._last_trigger_time = now
            action_taken = "触发"

        # ── Per-tick summary ──
        if self._in_battle:
            status = action_taken if action_taken else "待触发"
            print(f"[{_ts()}] 战斗中 | {status}")
        else:
            if action_template:
                print(f"[{_ts()}] 待机中...")
            # else: nothing detected, silence to reduce noise

        self._last_action_template = action_template
        self._last_action_score = action_score
        self._last_end_name = best_end_name
        self._last_end_score = best_end_score
        self._last_reconnect_score = reconnect_score
