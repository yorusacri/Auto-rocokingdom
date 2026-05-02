from typing import Optional

from config import CONFIG
from core.input import press_once
from core.util import _ts
from modes.base import BaseMode, BattleEvent
from modes.escape import EscapeMode

ACTION_OPTIONS = {
    "1": ("gather", "只聚能（按 X）"),
    "2": ("escape", "逃跑（按 ESC + 确认）"),
    "3": ("skill1_gather", "释放技能1后聚能（按 1，再按 X）"),
}


class SmartMode(BaseMode):
    def __init__(self, pollute_action: str = "gather", normal_action: str = "escape") -> None:
        self._escape_delegate = EscapeMode()
        self._pollute_action = pollute_action
        self._normal_action = normal_action
        self._current_action: Optional[str] = None
        self._skill1_used = False

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

        if self._current_action is None:
            return None

        if self._current_action == "gather":
            press_once(event.hwnd, CONFIG.press_key)
            print(f"[{_ts()}] 智能模式动作: 已触发按键 {CONFIG.press_key}（本场=聚能）")
            return None
        elif self._current_action == "escape":
            print(f"[{_ts()}] 智能模式动作: 已触发 ESC（本场=逃跑）")
            return self._escape_delegate.on_action(event, is_hit, action_score)
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

    def on_battle_end(self, event: BattleEvent) -> None:
        self._current_action = None
        self._skill1_used = False
