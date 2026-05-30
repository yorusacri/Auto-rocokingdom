import sys
from unittest.mock import MagicMock

import numpy as np
import pytest

# Mock heavy OS/driver modules before any project import touches them
sys.modules.setdefault("eel", MagicMock())
sys.modules.setdefault("win32gui", MagicMock())
sys.modules.setdefault("win32ui", MagicMock())
sys.modules.setdefault("win32con", MagicMock())
sys.modules.setdefault("interception", MagicMock())


@pytest.fixture
def dummy_bgr_frame():
    return np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)


@pytest.fixture
def dummy_gray_frame():
    return np.random.randint(0, 256, (100, 100), dtype=np.uint8)


@pytest.fixture
def dummy_templates():
    from core.vision import Template

    return [
        Template(name="capture.png", image=np.random.randint(0, 256, (20, 30), dtype=np.uint8)),
        Template(name="action.png", image=np.random.randint(0, 256, (15, 25), dtype=np.uint8)),
    ]
