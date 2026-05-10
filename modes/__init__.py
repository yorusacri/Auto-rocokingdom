from modes.ball import AutoBallMode
from modes.smart import SmartMode

MODE_REGISTRY = {
    "1": SmartMode,
    "2": AutoBallMode,
}

__all__ = ["MODE_REGISTRY"]
