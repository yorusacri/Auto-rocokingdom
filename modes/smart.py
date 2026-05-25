import time
from typing import Optional

from config import CONFIG
from core.capture import capture_window_bgr
from core.input import click_at, press_once
from core.util import _ts
from core.vision import best_yes_score_and_loc
from modes.base import BaseMode, BattleEvent

ACTION_OPTIONS = {
    "1": ("gather", "只聚能（按 X）"),
    "2": ("escape", "逃跑（按 ESC + 确认）"),
    "3": ("skill1_gather", "释放技能1后聚能（按 1，再按 X）"),
    "4": ("none", "不操作"),
}


class SmartMode(BaseMode):
    def __init__(self, pollute_action: str = "gather", normal_action: str = "escape") -> None:
        self._pollute_action = pollute_action
        self._normal_action = normal_action
        self._current_action: Optional[str] = None
        self._skill1_used = False

    def set_pollute_action(self, action: str) -> None:
        self._pollute_action = action

    def set_normal_action(self, action: str) -> None:
        self._normal_action = action

    @property
    def name(self) -> str:
        return "smart"

    @property
    def label(self) -> str:
        return "智能模式"

    def _action_label(self, action: str) -> str:
        labels = {"gather": "聚能", "escape": "逃跑", "skill1_gather": "技能1+聚能"}
        return labels.get(action, action)

    def on_battle_start(self, event: BattleEvent) -> None:
        is_pollute = event.pollute_capture_score > event.capture_score
        self._current_action = (
            self._pollute_action if is_pollute else self._normal_action
        )
        self._skill1_used = False

        mode_label = "污染" if is_pollute else "普通"
        action_label = self._action_label(self._current_action)
        print(
            f"[{_ts()}] 智能模式判型: 本场={mode_label} → {action_label}"
            f"（capture={event.capture_score:.3f}, pollute_capture={event.pollute_capture_score:.3f}）"
        )

    def on_action(self, event: BattleEvent, is_hit: bool, action_score: float) -> Optional[float]:
        if not is_hit:
            return None

        if self._current_action is None or self._current_action == "none":
            return None

        if self._current_action == "gather":
            press_once(event.hwnd, CONFIG.press_key)
            print(f"[{_ts()}] 智能模式动作: 已触发按键 {CONFIG.press_key}（本场=聚能）")
            return None
        elif self._current_action == "escape":
            return self._do_escape(event)
        elif self._current_action == "skill1_gather":
            if not self._skill1_used:
                press_once(event.hwnd, "1")
                self._skill1_used = True
                print(f"[{_ts()}] 智能模式动作: 已释放技能1（本场=技能1+聚能）")
                return 1.0
            else:
                press_once(event.hwnd, CONFIG.press_key)
                print(f"[{_ts()}] 智能模式动作: 已触发按键 {CONFIG.press_key}（本场=技能1+聚能）")
                return None
        return None

    def _do_escape(self, event: BattleEvent) -> float:
        press_once(event.hwnd, "esc")
        print(f"[{_ts()}] 智能模式动作: 已触发 ESC（本场=逃跑）")

        yes_threshold = CONFIG.match_threshold * 0.8
        for _ in range(10):
            time.sleep(0.3)
            full_shot = capture_window_bgr(event.hwnd)
            best_score, best_loc = best_yes_score_and_loc(full_shot, event.templates, event.scale)

            if best_score >= yes_threshold:
                cap_h, cap_w = full_shot.shape[:2]
                click_x, click_y = best_loc
                if cap_w > 0 and cap_h > 0 and (cap_w != event.window_width or cap_h != event.window_height):
                    click_x = int(round(best_loc[0] * event.window_width / cap_w))
                    click_y = int(round(best_loc[1] * event.window_height / cap_h))
                    click_x = max(0, min(event.window_width - 1, click_x))
                    click_y = max(0, min(event.window_height - 1, click_y))

                if click_at(event.hwnd, click_x, click_y):
                    print(f"[{_ts()}] 逃跑确认点击成功")
                    break
        else:
            print(f"[{_ts()}] [警告] 触发 ESC 后未找到确认按钮 yes.png")

        return 2.0

    def on_battle_end(self, event: BattleEvent) -> None:
        self._current_action = None
        self._skill1_used = False
