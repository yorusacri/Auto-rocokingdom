import os
from unittest.mock import MagicMock, patch

import pytest

from core.gui import _TeeStdout, _classify_log_level, _drain_log, _stdout_buffer, _stdout_lock


class TestTeeStdoutFileno:
    """Test the fileno() method that has caused real crashes in production."""

    def test_fileno_normal_delegates(self):
        """When original has a working fileno(), return its value."""
        original = MagicMock()
        original.fileno.return_value = 1
        tee = _TeeStdout(original)
        assert tee.fileno() == 1

    def test_fileno_original_none_falls_back(self):
        """When original is None, return a real fd pointing to os.devnull."""
        tee = _TeeStdout(None)
        fd = tee.fileno()
        assert isinstance(fd, int)
        assert fd > 2

    def test_fileno_original_oserror_falls_back(self):
        """When original.fileno() raises OSError, fall back to os.devnull.

        This reproduces the PyInstaller console=False crash where
        Edge passes sys.stdout to subprocess.Popen, which calls
        fileno() and expects a valid integer fd.
        """
        original = MagicMock()
        original.fileno.side_effect = OSError("No underlying file descriptor")
        tee = _TeeStdout(original)
        fd = tee.fileno()
        assert isinstance(fd, int)
        assert fd > 2

    def test_fileno_no_hasattr_falls_back(self):
        """When original has no fileno attribute, use fallback."""
        original = object()  # no fileno method
        tee = _TeeStdout(original)
        fd = tee.fileno()
        assert isinstance(fd, int)
        assert fd > 2


class TestTeeStdoutWrite:
    """Test the write() buffering logic."""

    def setup_method(self):
        with _stdout_lock:
            _stdout_buffer.clear()

    def test_write_full_line_appended_to_buffer(self):
        original = MagicMock()
        tee = _TeeStdout(original)
        tee.write("hello world\n")
        with _stdout_lock:
            assert "hello world" in _stdout_buffer

    def test_write_partial_line_not_yet_buffered(self):
        original = MagicMock()
        tee = _TeeStdout(original)
        tee.write("hello ")
        with _stdout_lock:
            assert _stdout_buffer == []
        tee.write("world\n")
        with _stdout_lock:
            assert "hello world" in _stdout_buffer

    def test_write_empty_line_skipped(self):
        original = MagicMock()
        tee = _TeeStdout(original)
        with _stdout_lock:
            _stdout_buffer.clear()
        tee.write("   \n")
        with _stdout_lock:
            assert _stdout_buffer == []

    def test_write_multiline_split(self):
        original = MagicMock()
        tee = _TeeStdout(original)
        tee.write("line1\nline2\n")
        with _stdout_lock:
            assert "line1" in _stdout_buffer
            assert "line2" in _stdout_buffer

    def test_write_tees_to_original(self):
        original = MagicMock()
        tee = _TeeStdout(original)
        tee.write("test\n")
        original.write.assert_called_with("test\n")
        original.flush.assert_called()

    def test_write_original_none_does_not_crash(self):
        tee = _TeeStdout(None)
        tee.write("test\n")  # should not raise


class TestFlush:
    def test_flush_delegates_to_original(self):
        original = MagicMock()
        tee = _TeeStdout(original)
        tee.flush()
        original.flush.assert_called_once()

    def test_flush_original_none_does_not_crash(self):
        tee = _TeeStdout(None)
        tee.flush()  # should not raise


class TestClassifyLogLevel:
    @pytest.mark.parametrize("line, expected", [
        ("[12:00] >>> 战斗开始（第 1 场）", "battle-start"),
        ("[12:01] <<< 战斗结束（第 1 场）", "battle-end"),
        ("[12:00] 污染判型 精灵名称", "pollute"),
        ("[12:00] 污染精灵：某精灵", "pollute"),
        ("[12:00] [警告] 无法读取配置", "warning"),
        ("[12:00] [错误] 引擎异常", "warning"),
        ("[12:00] 检测到同行", "info"),
        ("[12:00] 待机中...", "info"),
        ("[12:00] random unknown message", "info"),
    ])
    def test_classify(self, line, expected):
        assert _classify_log_level(line) == expected


class TestDrainLog:
    def test_drain_returns_and_clears(self):
        with _stdout_lock:
            _stdout_buffer[:] = ["line1", "line2", "line3"]
        result = _drain_log()
        assert result == ["line1", "line2", "line3"]
        with _stdout_lock:
            assert _stdout_buffer == []

    def test_drain_empty_returns_list(self):
        with _stdout_lock:
            _stdout_buffer.clear()
        result = _drain_log()
        assert result == []
