# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Auto-Roco (洛克王国自动化助手) — a game automation tool for "洛克王国：世界" that uses OpenCV template matching to detect battle states and simulates keyboard/mouse input. Windows-only (depends on pywin32 for input simulation and window capture).

## Running

```bash
uv sync
uv run main.py
```

Requires Administrator privileges for input simulation. No build step, no tests, no linter configured.

## Architecture

**Strategy pattern**: `modes/` contains mode classes that inherit from `BaseMode` (abstract base in `modes/base.py`). Each mode implements `on_battle_start`, `on_action`, `on_battle_end`, and `on_tick_display`. Modes are registered in `modes/__init__.py` via `MODE_REGISTRY` dict.

**Engine loop** (`core/engine.py`): Captures the game window each tick, runs template matching on the ROI (right-bottom quarter by default), tracks hit/miss streaks for battle state detection, and dispatches events to the active mode.

**Data flow**:
1. `core/capture.py` — takes a screenshot of the game window (works even when covered, not minimized)
2. `core/vision.py` — preprocesses the frame, loads PNG templates, runs `cv2.matchTemplate` with optional Canny edge detection
3. `core/engine.py` — interprets match scores as hit/miss, manages battle state machine, calls mode callbacks
4. Mode callbacks use `core/input.py` to simulate key presses / mouse clicks

**Configuration**: Single frozen dataclass `AppConfig` in `config.py` with all tunables (thresholds, ROI ratios, poll interval, template names).

## Commit Rules

Before every git commit:
1. Review CHANGELOG.md and add entries for all functional changes (new features, bug fixes) first; structural/refactor changes are secondary.
2. Review README.md and update any sections affected by the changes (e.g., update logs, mode descriptions, usage instructions, feature lists).
3. Review `.gitignore` and add any new files or directories that should not be tracked (e.g., newly generated files, IDE configs, sensitive data).

## Template Roles

Templates in `templates/` are strictly partitioned by purpose. Each template belongs to exactly one category:

| Category | Templates | Matching mode | Purpose |
|---|---|---|---|
| Action detection | `skill1.png`, `exchange.png`, etc. | Canny edge | Detect action buttons during battle; trigger key presses |
| Battle type | `capture.png`, `pollute_capture.png` | Canny edge | Compare scores at battle start to classify normal vs pollution |
| Battle end | `elf_P.png`, `missions.png`, `map.png` | Canny edge | Detect battle-over screen in their respective ROIs |
| Escape confirm | `yes.png` | Grayscale | Locate the "confirm" button position after ESC in escape mode |
| Teammate reconnect | `qiudaidai.png` | Grayscale (threshold 0.6) | Detect teammate rejoin request in non-battle state |

Matching mode is determined in `core/vision.py:load_templates()` — templates with `yes` or `qiudaidai` in the filename use grayscale (`cv2.cvtColor(BGR2GRAY)`), all others use Canny edge detection.

Only **action detection** templates contribute to the action score that triggers battle state transitions. All other templates are excluded from action scoring.

## Key Conventions

- All user-facing strings and log messages are in Chinese
- Templates (`templates/*.png`) are matched at reference resolution 2560x1600; `core/vision.py` auto-scales to actual window size
- Poll interval is capped at 5.0 seconds; trigger cooldown is 1.0 second
- Adding a new mode: create a class in `modes/` extending `BaseMode`, register it in `MODE_REGISTRY` in `modes/__init__.py`, and add the menu entry in `main.py`
