from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from core.vision import Template


@dataclass
class BattleEvent:
    hwnd: int
    templates: List[Template]
    scale: float
    battle_count: int
    pollute_count: int
    capture_score: float
    pollute_capture_score: float
    window_width: int
    window_height: int
    all_scores: list = None
    end_scores: list = None


class BaseMode(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """模式标识，如 'battle', 'escape', 'count_only', 'smart'"""

    @property
    @abstractmethod
    def label(self) -> str:
        """模式中文标签，如 '聚能模式'"""

    def on_battle_start(self, event: BattleEvent) -> None:
        """新战斗开始时回调"""

    @abstractmethod
    def on_action(self, event: BattleEvent, is_hit: bool, action_score: float) -> Optional[float]:
        """在战斗中每轮调用，执行模式行为。返回额外冷却秒数或 None。"""

    def on_battle_end(self, event: BattleEvent) -> None:
        """战斗结束时回调"""

    def on_non_battle_no_action(self, event: BattleEvent) -> None:
        """非战斗状态且未检测到行动时回调"""
