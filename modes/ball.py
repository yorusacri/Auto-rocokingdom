from typing import Optional

import win32gui

from config import CONFIG
from core.input import click_at
from core.util import _ts
from modes.base import BaseMode, BattleEvent


class AutoBallMode(BaseMode):
    @property
    def name(self) -> str:
        return "auto_ball"

    @property
    def label(self) -> str:
        return "自动丢球"

    def on_non_battle_no_action(self, event: BattleEvent) -> None:
        if win32gui.GetForegroundWindow() != event.hwnd:
            print(f"[{_ts()}] 丢球跳过：窗口非前台")
            return

        elf_score = next((s for n, s in event.end_scores if "elf_p.png" in n.lower()), 0.0)
        exchange_score = next((s for n, s in event.all_scores if "exchange.png" in n.lower()), 0.0)
        if max(elf_score, exchange_score) < CONFIG.match_threshold:
            print(f"[{_ts()}] 丢球跳过：未达阈值（elf_P={elf_score:.3f} exchange={exchange_score:.3f}）")
            return

        if click_at(event.hwnd):
            print(f"[{_ts()}] 丢球点击（elf_P={elf_score:.3f} exchange={exchange_score:.3f}）")
        else:
            print(f"[{_ts()}] [警告] 丢球点击失败")

    def on_action(self, event: BattleEvent, is_hit: bool, action_score: float) -> Optional[float]:
        return None
