# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Auto-Roco (洛克王国自动化助手) — a game automation tool for "洛克王国：世界" that uses OpenCV template matching to detect battle states and simulates keyboard/mouse input. Windows-only (depends on pywin32 + Interception driver for input simulation and window capture).

## Running

```bash
uv sync
uv run main.py --gui    # desktop client (recommended)
uv run main.py          # CLI fallback
```

Requires Administrator privileges for input simulation. No build step, no tests, no linter configured.

## Architecture

### Desktop Client (Eel)

The GUI is an Eel desktop app (Python backend + HTML/CSS/JS frontend rendered in an embedded browser). No terminal window in the packaged exe.

**Frontend** (`web/index.html`): Single-page dark-themed instrument panel with:
- Pause/resume button (header) + stop button (sidebar, only visible when paused)
- Stats panel (battle count, pollute count, detection scores to 2 decimal places)
- Mode selector (smart / auto-ball) with sub-options for pollute/normal behavior
- Window selector with refresh button and radio list
- Settings modal (gear icon): match threshold slider, poll interval slider
- Scrolling log terminal showing program actions (待机/触发/战斗中), not raw scores
- All config persisted to `user_prefs.json` via Python `save_prefs()` / `load_prefs()`

**Backend** (`core/gui.py`): Eel-exposed functions bridge JS ↔ Python:
- `start_engine(hwnd, mode_key, pollute_action, normal_action)` — creates Engine in daemon thread
- `stop_engine()` / `toggle_pause()` — threading.Event control
- `list_windows()` — scans and pushes to JS via `eel.onWindowsListed()`
- `get_settings()` / `save_settings()` — read/write `user_prefs.json`
- `get_gui_prefs()` / `save_gui_prefs()` — persist mode/action choices
- `_push_loop()` — spawned Eel greenlet, drains stdout buffer + engine snapshot to frontend every 0.3s
- stdout is tee'd via `_TeeStdout` to capture Python `print()` output for the frontend log

**Eel wiring**: JS functions must be statically registered via `eel.expose(fn, 'name')` so Eel's pyparsing scanner finds them. Python calls JS with `eel.functionName(args)` (single call). JS calls Python with `eel.exposed_fn(args)()` (double call, second = callback).

### Engine (`core/engine.py`)

Refactored from monolithic `run()` into:
- `_setup()` — loads templates, initializes state (called once in `__init__`)
- `_tick()` — single iteration: capture → match → battle state machine → action trigger
- `tick()` — public wrapper with pause-check + `_snapshot()` return for GUI
- `run()` — thin loop calling `_tick()` + sleep (CLI mode)

**Pause/Stop**: `threading.Event` based. `pause()` clears the event, `_wait_if_paused()` blocks the loop. `stop()` sets `_stop_requested` + releases pause. `toggle_pause()` returns bool.

**Hot-switch**: `switch_window(hwnd)` updates target window. SmartMode has `set_pollute_action()` / `set_normal_action()` for in-flight behavior changes.

### Strategy Pattern

`modes/` contains mode classes that inherit from `BaseMode` (abstract base in `modes/base.py`). Each mode implements `on_battle_start`, `on_action`, `on_battle_end`, and `on_non_battle_no_action`.

| Mode | Class | Name |
|------|-------|------|
| Smart | `SmartMode` (modes/smart.py) | `"smart"` |
| Auto-ball | `AutoBallMode` (modes/ball.py) | `"auto_ball"` |

Modes are registered in `modes/__init__.py` via `MODE_REGISTRY` dict. Adding a mode: create a class extending `BaseMode`, register in `MODE_REGISTRY`, and add placeholder handling in `core/gui.py:_find_mode_cls()`.

### Data Flow

1. `core/capture.py` — takes a screenshot of the game window (works even when covered, not minimized)
2. `core/vision.py` — preprocesses the frame, loads PNG templates, runs `cv2.matchTemplate` with Canny edge detection (or grayscale for `yes.png` / `qiudaidai.png`)
3. `core/engine.py` — interprets match scores, manages battle state machine, calls mode callbacks
4. Mode callbacks use `core/input.py` to simulate key presses / mouse clicks (Interception driver)
5. `core/battle_classify.py` — delayed re-capture at battle start to avoid transition-frame misclassification
6. `core/ocr.py` — optional EasyOCR spirit name recognition (full build only)
7. `core/pollute_logger.py` — CSV logging of pollution battles

### Configuration

`config.py`: `AppConfig` frozen dataclass, populated from `user_prefs.json` at import time. Key tunables:
- `match_threshold` (0.40), `poll_interval_sec` (2.0), `trigger_cooldown_sec` (1.0)
- `press_key` ("x"), `use_edge_match` (True)
- `window_title_keyword` ("洛克王国：世界"), ref resolution 2560x1600

GUI settings panel saves to `user_prefs.json` via `save_prefs()`; changes take effect on next engine start.

## Commit Rules — READ CAREFULLY

- **CRITICAL: NEVER commit, push, or tag unless the user explicitly says "commit" or "push".** This includes `git commit`, `git push`, `git tag`, or any action that creates/modifies git objects. If you commit without permission, the user cannot undo it. Always ask first — even if you've fixed a bug, even if tests pass, even if it "just works now." Wait for the user to say "commit" before creating any commit.
- Before every git commit:
  1. Review CHANGELOG.md and add entries for all functional changes (new features, bug fixes) first; structural/refactor changes are secondary.
  2. Review README.md and update any sections affected by the changes.
  3. Review `.gitignore` and add any new files or directories that should not be tracked.

## Template Roles

| Category | Templates | Matching mode | Purpose |
|---|---|---|---|
| Action detection | `skill1.png`, `exchange.png`, etc. | Canny edge | Detect action buttons during battle; trigger key presses |
| Battle type | `capture.png`, `pollute_capture.png` | Canny edge | Compare scores at battle start to classify normal vs pollution |
| Battle end | `elf_P.png`, `missions.png`, `map.png` | Canny edge | Detect battle-over screen in their respective ROIs |
| Escape confirm | `yes.png` | Grayscale | Locate the "confirm" button position after ESC in escape mode |
| Teammate reconnect | `qiudaidai.png` | Grayscale (threshold 0.6) | Detect teammate rejoin request in non-battle state |

Matching mode is determined in `core/vision.py:load_templates()` — templates with `yes` or `qiudaidai` in the filename use grayscale, all others use Canny edge detection. Only **action detection** templates contribute to the action score.

## Key Conventions

- All user-facing strings and log messages are in Chinese
- Templates matched at reference resolution 2560x1600; auto-scaled to actual window size
- Poll interval capped at 5.0s; trigger cooldown is 1.0s
- Engine log output shows program behavior (待机中/战斗中|触发), not template names or raw scores
- GUI mode/action preferences auto-persist to `user_prefs.json`

## Packaging

PyInstaller via `.spec` files:
- `auto-roco-client-lite.spec` — excludes EasyOCR/torch (smaller)
- `auto-roco-client-full.spec` — includes EasyOCR spirit name recognition

Both use `console=False` (no terminal window). Entry point: `client_main.py`. Built by GitHub Actions on `v*` tag push.
