import numpy as np
import pytest

from core.vision import normalize_template_name, normalize_poll_interval, preprocess, Template


class TestNormalizePollInterval:
    @pytest.mark.parametrize("input_val, expected", [
        (0, 5.0),
        (-1, 5.0),
        (-100, 5.0),
        (0.05, 0.05),
        (2.0, 2.0),
        (5.0, 5.0),
        (5.0001, 5.0),
        (100, 5.0),
    ])
    def test_boundary_values(self, input_val, expected):
        assert normalize_poll_interval(input_val) == expected


class TestNormalizeTemplateName:
    @pytest.mark.parametrize("input_name, expected", [
        ("capture.png", "capture.png"),
        ("CAPTURE.PNG", "capture.png"),
        ("Capture.Png", "capture.png"),
        ("map.png", "map.png"),
    ])
    def test_lowercase(self, input_name, expected):
        assert normalize_template_name(input_name) == expected

    def test_basename_only(self):
        assert normalize_template_name(r"C:\templates\CAPTURE.PNG") == "capture.png"
        assert normalize_template_name("/home/user/templates/Map.PNG") == "map.png"

    def test_strips_whitespace(self):
        assert normalize_template_name("  capture.png  ") == "capture.png"


class TestPreprocess:
    def test_returns_grayscale_shape(self, dummy_bgr_frame):
        from config import CONFIG
        import importlib
        import core.vision
        importlib.reload(core.vision)
        result = preprocess(dummy_bgr_frame)
        assert len(result.shape) == 2  # single-channel output

    def test_edge_mode_output_is_binary(self):
        from config import CONFIG
        import importlib
        import core.vision
        # force edge_match
        import config
        config.CONFIG.use_edge_match = True
        importlib.reload(core.vision)
        frame = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        result = core.vision.preprocess(frame)
        # Canny output is binary (0 or 255)
        assert result.max() <= 255
        assert result.min() >= 0
        assert len(result.shape) == 2


class TestTemplate:
    def test_create_template(self):
        img = np.zeros((20, 30), dtype=np.uint8)
        t = Template(name="test.png", image=img)
        assert t.name == "test.png"
        assert np.array_equal(t.image, img)
