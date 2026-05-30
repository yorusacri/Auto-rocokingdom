from modes import MODE_REGISTRY
from modes.base import BaseMode


def test_all_modes_are_base_mode_subclasses():
    for key, cls in MODE_REGISTRY.items():
        instance = cls()
        assert isinstance(instance, BaseMode), f"Mode '{key}' is not a BaseMode subclass"

def test_all_modes_have_valid_name():
    for key, cls in MODE_REGISTRY.items():
        instance = cls()
        assert isinstance(instance.name, str), f"Mode '{key}' name is not a string"
        assert len(instance.name) > 0, f"Mode '{key}' name is empty"

def test_all_modes_have_valid_label():
    for key, cls in MODE_REGISTRY.items():
        instance = cls()
        assert isinstance(instance.label, str), f"Mode '{key}' label is not a string"
        assert len(instance.label) > 0, f"Mode '{key}' label is empty"

def test_registry_contains_expected_modes():
    assert "1" in MODE_REGISTRY
    assert "2" in MODE_REGISTRY
