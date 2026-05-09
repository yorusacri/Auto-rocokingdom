from modes.ball import AutoBallMode
from modes.battle import BattleMode
from modes.count import CountMode
from modes.escape import EscapeMode
from modes.smart import SmartMode

MODE_REGISTRY = {
    "1": BattleMode,
    "2": EscapeMode,
    "3": CountMode,
    "4": SmartMode,
    "5": AutoBallMode,
}

__all__ = ["MODE_REGISTRY"]
