import pytest

from modes.base import BaseMode, BattleEvent
from core.vision import Template


class TestBattleEvent:
    def test_default_values(self):
        event = BattleEvent(
            hwnd=123,
            templates=[],
            scale=1.0,
            battle_count=1,
            pollute_count=0,
            capture_score=0.5,
            pollute_capture_score=0.3,
            window_width=1920,
            window_height=1080,
        )
        assert event.hwnd == 123
        assert event.all_scores is None
        assert event.end_scores is None

    def test_with_scores_provided(self):
        event = BattleEvent(
            hwnd=0, templates=[], scale=1.0,
            battle_count=2, pollute_count=1,
            capture_score=0.8, pollute_capture_score=0.9,
            window_width=100, window_height=100,
            all_scores=[("t1.png", 0.5)],
            end_scores=[("elf_P.png", 0.3)],
        )
        assert event.all_scores == [("t1.png", 0.5)]
        assert event.end_scores == [("elf_P.png", 0.3)]


class TestBaseModeDefaults:
    def _make_mode(self):
        class TestMode(BaseMode):
            @property
            def name(self):
                return "test"
            @property
            def label(self):
                return "测试"
            def on_action(self, event, is_hit, action_score):
                return None

        return TestMode()

    def _make_event(self):
        return BattleEvent(
            hwnd=0, templates=[], scale=1.0,
            battle_count=0, pollute_count=0,
            capture_score=0.0, pollute_capture_score=0.0,
            window_width=100, window_height=100,
        )

    def test_on_battle_start_does_not_raise(self):
        m = self._make_mode()
        m.on_battle_start(self._make_event())

    def test_on_battle_end_does_not_raise(self):
        m = self._make_mode()
        m.on_battle_end(self._make_event())

    def test_on_non_battle_no_action_does_not_raise(self):
        m = self._make_mode()
        m.on_non_battle_no_action(self._make_event())

    def test_name_and_label_are_strings(self):
        m = self._make_mode()
        assert isinstance(m.name, str)
        assert len(m.name) > 0
        assert isinstance(m.label, str)
        assert len(m.label) > 0
