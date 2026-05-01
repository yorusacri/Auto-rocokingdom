"""Build standalone executables using PyInstaller.

Usage:
    python build.py          # build both lite and full
    python build.py lite     # build lite only
    python build.py full     # build full only
"""

import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
DIST_DIR = PROJECT_DIR / "dist"
TEMPLATES_DIR = PROJECT_DIR / "templates"

PYINSTALLER_COMMON = [
    sys.executable, "-m", "PyInstaller",
    "--noconfirm",
    "--onedir",
    "--console",
    f"--add-data={TEMPLATES_DIR};templates",
    f"--paths={PROJECT_DIR}",
]

LITE_NAME = "auto-roco-lite"
FULL_NAME = "auto-roco-full"

LITE_EXCLUDE = [
    "--exclude-module=easyocr",
    "--exclude-module=torch",
    "--exclude-module=torchvision",
    "--exclude-module=PIL",
    "--exclude-module=scipy",
    "--exclude-module=shapely",
]

FULL_COLLECT = [
    "--collect-all=easyocr",
    "--collect-all=torch",
    "--collect-all=torchvision",
    "--collect-all=PIL",
]


def build(name: str, extra_args: list[str] | None = None) -> None:
    cmd = [*PYINSTALLER_COMMON, f"--name={name}", *(extra_args or []), "main.py"]
    print(f"\n{'='*60}")
    print(f"Building {name} ...")
    print(f"{'='*60}\n")
    subprocess.check_call(cmd, cwd=PROJECT_DIR)

    # Copy README and CHANGELOG into dist
    out_dir = DIST_DIR / name
    for doc in ("README.md", "CHANGELOG.md"):
        src = PROJECT_DIR / doc
        if src.exists():
            shutil.copy2(src, out_dir / doc)

    print(f"\n[OK] {name} built -> {out_dir}")


def main() -> None:
    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    if target in ("all", "lite"):
        build(LITE_NAME, LITE_EXCLUDE)

    if target in ("all", "full"):
        build(FULL_NAME, FULL_COLLECT)

    if target not in ("all", "lite", "full"):
        print(f"Unknown target: {target}")
        print("Usage: python build.py [all|lite|full]")
        sys.exit(1)

    print(f"\nDone. Output in {DIST_DIR}")


if __name__ == "__main__":
    main()
