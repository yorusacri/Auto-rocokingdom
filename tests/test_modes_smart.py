from unittest.mock import MagicMock, patch

import pytest

from modes.base import BattleEvent
from modes.smart import SmartMode, ACTION_OPTIONS


class TestSmartModeOnBattleStart:
    def setup_method(self):
        self.mode = SmartMode(pollute_action="gather", normal_action="escape")

    def _make_event(self, capture_score=0.0, pollute_capture_score=0.0):
        return BattleEvent(
            hwnd=0, templates=[], scale=1.0,
            battle_count=1, pollute_count=0,
            capture_score=capture_score,
            pollute_capture_score=pollute_capture_score,
            window_width=100, window_height=100,
        )

    def test_pollute_when_pollute_gt_capture(self):
        """pollute_capture_score > capture_score → classify as pollute."""
        self.mode.on_battle_start(self._make_event(capture_score=0.3, pollute_capture_score=0.8))
        assert self.mode._current_action == "gather"  # pollute_action

    def test_normal_when_capture_gte_pollute(self):
        """capture_score >= pollute_capture_score → classify as normal."""
        self.mode.on_battle_start(self._make_event(capture_score=0.8, pollute_capture_score=0.3))
        assert self.mode._current_action == "escape"  # normal_action

    def test_normal_when_equal(self):
        """capture_score == pollute_capture_score → normal (not >)."""
        self.mode.on_battle_start(self._make_event(capture_score=0.5, pollute_capture_score=0.5))
        assert self.mode._current_action == "escape"

    def test_resets_skill1_flag(self):
        self.mode._skill1_used = True
        self.mode.on_battle_start(self._make_event(capture_score=0.8, pollute_capture_score=0.3))
        assert self.mode._skill1_used is False


class TestSmartModeOnBattleEnd:
    def test_resets_current_action(self):
        mode = SmartMode()
        mode._current_action = "gather"
        mode._skill1_used = True
        event = BattleEvent(
            hwnd=0, templates=[], scale=1.0,
            battle_count=1, pollute_count=1,
            capture_score=0.0, pollute_capture_score=0.0,
            window_width=100, window_height=100,
        )
        mode.on_battle_end(event)
        assert mode._current_action is None
        assert mode._skill1_used is False


class TestSmartModeOnAction:
    def _make_event(self, hwnd=0):
        return BattleEvent(
            hwnd=hwnd, templates=[], scale=1.0,
            battle_count=1, pollute_count=0,
            capture_score=0.0, pollute_capture_score=0.0,
            window_width=100, window_height=100,
        )

    def test_not_hit_returns_none(self):
        mode = SmartMode()
        mode._current_action = "gather"
        result = mode.on_action(self._make_event(), False, 0.0)
        assert result is None

    def test_none_action_returns_none(self):
        mode = SmartMode()
        mode._current_action = "none"
        result = mode.on_action(self._make_event(), True, 0.8)
        assert result is None

    def test_null_current_action_returns_none(self):
        mode = SmartMode()
        mode._current_action = None
        result = mode.on_action(self._make_event(), True, 0.8)
        assert result is None

    def test_gather_presses_key(self, monkeypatch):
        mock_press = MagicMock()
        monkeypatch.setattr("modes.smart.press_once", mock_press)
        monkeypatch.setattr("modes.smart.CONFIG.press_key", "x")
        mode = SmartMode()
        mode._current_action = "gather"
        result = mode.on_action(self._make_event(hwnd=42), True, 0.8)
        mock_press.assert_called_once_with(42, "x")
        assert result is None

    def test_skill1_gather_first_call(self, monkeypatch):
        """First call with skill1_gather should press '1', set flag, return 1.0."""
        mock_press = MagicMock()
        monkeypatch.setattr("modes.smart.press_once", mock_press)
        mode = SmartMode()
        mode._current_action = "skill1_gather"
        mode._skill1_used = False
        result = mode.on_action(self._make_event(hwnd=0), True, 0.8)
        assert result == 1.0
        assert mode._skill1_used is True
        mock_press.assert_called_once_with(0, "1")

    def test_skill1_gather_second_call(self, monkeypatch):
        """Second call should press CONFIG.press_key, return None."""
        mock_press = MagicMock()
        monkeypatch.setattr("modes.smart.press_once", mock_press)
        monkeypatch.setattr("modes.smart.CONFIG.press_key", "x")
        mode = SmartMode()
        mode._current_action = "skill1_gather"
        mode._skill1_used = True
        result = mode.on_action(self._make_event(hwnd=0), True, 0.8)
        assert result is None
        mock_press.assert_called_once_with(0, "x")


class TestActionOptions:
    def test_all_options_valid(self):
        assert "1" in ACTION_OPTIONS
        assert "2" in ACTION_OPTIONS
        assert "3" in ACTION_OPTIONS
        assert "4" in ACTION_OPTIONS

    def test_options_have_key_and_label(self):
        for key, (action_key, label) in ACTION_OPTIONS.items():
            assert isinstance(action_key, str)
            assert isinstance(label, str)
            assert len(label) > 0
