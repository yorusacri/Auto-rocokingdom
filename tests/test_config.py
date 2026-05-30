import json
import os

import pytest

from config import load_prefs, save_prefs, AppConfig


class TestLoadPrefs:
    def test_file_not_found_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr("config._PREFS_PATH", str(tmp_path / "missing.json"))
        assert load_prefs() == {}

    def test_corrupt_json_returns_empty(self, tmp_path, monkeypatch):
        p = tmp_path / "bad.json"
        p.write_text("this is not json", encoding="utf-8")
        monkeypatch.setattr("config._PREFS_PATH", str(p))
        assert load_prefs() == {}

    def test_valid_json_returns_data(self, tmp_path, monkeypatch):
        p = tmp_path / "ok.json"
        p.write_text('{"key": "value", "num": 42}', encoding="utf-8")
        monkeypatch.setattr("config._PREFS_PATH", str(p))
        assert load_prefs() == {"key": "value", "num": 42}

    def test_oserror_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "config._PREFS_PATH",
            str(tmp_path / "dir" / "file.json"),
        )
        # directory doesn't exist → OSError on open
        monkeypatch.setattr("builtins.open", lambda *a, **kw: (_ for _ in ()).throw(OSError("denied")))
        assert load_prefs() == {}


class TestSavePrefs:
    def test_save_writes_and_merges(self, tmp_path, monkeypatch):
        p = tmp_path / "prefs.json"
        monkeypatch.setattr("config._PREFS_PATH", str(p))
        save_prefs({"a": 1})
        data = json.loads(p.read_text(encoding="utf-8"))
        assert data["a"] == 1

    def test_save_merges_with_existing(self, tmp_path, monkeypatch):
        p = tmp_path / "prefs2.json"
        p.write_text('{"existing": true}', encoding="utf-8")
        monkeypatch.setattr("config._PREFS_PATH", str(p))
        save_prefs({"new": 123})
        data = json.loads(p.read_text(encoding="utf-8"))
        assert data["existing"] is True
        assert data["new"] == 123


class TestAppConfig:
    def test_default_values(self):
        """AppConfig should have sensible defaults."""
        assert AppConfig.window_title_keyword == "洛克王国：世界"
        assert AppConfig.poll_interval_sec == 2.0
        assert AppConfig.match_threshold == 0.40
        assert AppConfig.press_key == "x"
        assert AppConfig.use_edge_match is True

    def test_references(self):
        """AppConfig should define all the template keys the engine uses."""
        assert len(AppConfig.battle_end_template_names) >= 1
        assert AppConfig.capture_template_name.endswith(".png")
        assert AppConfig.pollute_capture_template_name.endswith(".png")
