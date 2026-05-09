from typing import Optional

from core.input import click_at
from modes.base import BaseMode, BattleEvent


class AutoBallMode(BaseMode):
    @property
    def name(self) -> str:
        return "auto_ball"

    @property
    def label(self) -> str:
        return "自动丢球"

    def on_non_battle_no_action(self, event: BattleEvent) -> None:
        click_at(event.hwnd)

    def on_action(self, event: BattleEvent, is_hit: bool, action_score: float) -> Optional[float]:
        return None
