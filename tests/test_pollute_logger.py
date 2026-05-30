import csv
import importlib
import os

import pytest


class TestPolluteLogger:
    def test_ensure_csv_creates_file_with_header(self, tmp_path, monkeypatch):
        log_path = tmp_path / "logs" / "test_pollute.csv"
        monkeypatch.setattr("config.CONFIG.pollute_log_path", str(log_path))

        import core.pollute_logger
        importlib.reload(core.pollute_logger)

        from core.pollute_logger import _ensure_csv_file
        _ensure_csv_file()

        assert log_path.exists()
        content = log_path.read_text(encoding="utf-8-sig")
        assert "序号" in content
        assert "时间" in content
        assert "污染精灵" in content

    def test_ensure_csv_appends_mode_header_row(self, tmp_path, monkeypatch):
        log_path = tmp_path / "logs" / "test_start.csv"
        monkeypatch.setattr("config.CONFIG.pollute_log_path", str(log_path))

        import core.pollute_logger
        importlib.reload(core.pollute_logger)

        from core.pollute_logger import log_mode_start
        log_mode_start("智能模式")

        content = log_path.read_text(encoding="utf-8-sig")
        assert "mode=智能模式" in content
        assert "序号" in content  # header row also written

    def test_ensure_csv_does_not_overwrite(self, tmp_path, monkeypatch):
        log_path = tmp_path / "logs" / "test_keep.csv"
        monkeypatch.setattr("config.CONFIG.pollute_log_path", str(log_path))

        import core.pollute_logger
        importlib.reload(core.pollute_logger)

        from core.pollute_logger import _ensure_csv_file
        _ensure_csv_file()
        before = log_path.read_text(encoding="utf-8-sig")
        _ensure_csv_file()
        after = log_path.read_text(encoding="utf-8-sig")
        assert before == after  # no duplicate header

    def test_log_pollute_battle_writes_row(self, tmp_path, monkeypatch):
        log_path = tmp_path / "logs" / "test_battle.csv"
        monkeypatch.setattr("config.CONFIG.pollute_log_path", str(log_path))

        import core.pollute_logger
        importlib.reload(core.pollute_logger)

        from core.pollute_logger import log_pollute_battle
        log_pollute_battle(42, "测试精灵")

        content = log_path.read_text(encoding="utf-8-sig")
        assert "42" in content
        assert "测试精灵" in content
        assert "mode=" not in content  # log_pollute_battle doesn't add mode marker
