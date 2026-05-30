from unittest.mock import MagicMock, patch

import pytest
import numpy as np

from core.engine import Engine


@pytest.fixture
def mock_engine_deps():
    """Mock all the heavy deps needed to construct an Engine."""
    with patch("core.engine.load_templates", return_value=[]):
        with patch("core.engine.normalize_poll_interval", return_value=2.0):
            yield


def test_snapshot_keys(mock_engine_deps):
    """_snapshot must return all 8 keys the frontend JS expects."""
    from modes.smart import SmartMode
    engine = Engine(SmartMode())
    snap = engine._snapshot()
    expected = {
        "battle_count", "pollute_count", "in_battle",
        "action_template", "action_score",
        "end_name", "end_score", "reconnect_score",
    }
    assert set(snap.keys()) == expected


def test_snapshot_types(mock_engine_deps):
    from modes.smart import SmartMode
    engine = Engine(SmartMode())
    snap = engine._snapshot()
    assert isinstance(snap["battle_count"], int)
    assert isinstance(snap["pollute_count"], int)
    assert isinstance(snap["in_battle"], bool)
    assert isinstance(snap["action_score"], float)
    assert isinstance(snap["end_score"], float)
    assert isinstance(snap["reconnect_score"], float)


def test_snapshot_initial_state(mock_engine_deps):
    from modes.smart import SmartMode
    engine = Engine(SmartMode())
    snap = engine._snapshot()
    assert snap["battle_count"] == 0
    assert snap["pollute_count"] == 0
    assert snap["in_battle"] is False
    assert snap["action_score"] == 0.0


def test_pause_resume_toggle(mock_engine_deps):
    from modes.smart import SmartMode
    engine = Engine(SmartMode())
    assert engine.is_paused is False
    assert engine.is_running is True
    # Toggle → pause
    result = engine.toggle_pause()
    assert result is True
    assert engine.is_paused is True
    # Toggle → resume
    result = engine.toggle_pause()
    assert result is False
    assert engine.is_paused is False


def test_stop(mock_engine_deps):
    from modes.smart import SmartMode
    engine = Engine(SmartMode())
    engine.stop()
    assert engine.is_running is False
    assert engine.is_paused is False  # pause is released on stop


def test_switch_window(mock_engine_deps):
    from modes.smart import SmartMode
    engine = Engine(SmartMode(), hwnd=12345)
    assert engine._hwnd == 12345
    engine.switch_window(67890)
    assert engine._hwnd == 67890
