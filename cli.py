"""Interactive CLI launcher for Python scripts in the scripts/ directory."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def resolve_root_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


ROOT_DIR = resolve_root_dir()
SCRIPTS_DIR = ROOT_DIR / "scripts"
EXIT_CHOICES = {"0", "q", "quit", "exit"}
REFRESH_CHOICES = {"r", "refresh", ""}


def discover_scripts() -> list[Path]:
    if not SCRIPTS_DIR.exists():
        return []

    scripts = [
        path
        for path in SCRIPTS_DIR.rglob("*.py")
        if path.is_file() and path.name != "__init__.py"
    ]
    scripts.sort(key=lambda path: path.relative_to(SCRIPTS_DIR).as_posix().lower())
    return scripts


def format_script_label(path: Path) -> str:
    return path.relative_to(SCRIPTS_DIR).as_posix()


def print_menu(scripts: list[Path]) -> None:
    print("\n=== FiveM Bot Launcher ===")
    if not scripts:
        print("No Python scripts found in scripts/.")
    else:
        for index, script_path in enumerate(scripts, start=1):
            print(f"{index}. {format_script_label(script_path)}")

    print("\n[r] refresh")
    print("[0] quit")


def run_script(script_path: Path) -> None:
    label = format_script_label(script_path)
    print(f"\nRunning: {label}")
    start_time = time.time()
    command = build_python_command()
    if command is None:
        print("Python interpreter not found. Set FIVEM_BOT_PYTHON or install Python.")
        input("Press Enter to return to menu...")
        return

    result = subprocess.run([*command, str(script_path)], cwd=str(ROOT_DIR))
    duration = time.time() - start_time
    print(f"Script finished (code {result.returncode}) in {duration:.1f}s.")
    input("Press Enter to return to menu...")


def build_python_command() -> list[str] | None:
    custom_python = os.getenv("FIVEM_BOT_PYTHON", "").strip()
    if custom_python:
        return [custom_python]

    if not getattr(sys, "frozen", False):
        return [sys.executable]

    for command in ("py", "python"):
        if shutil.which(command):
            return [command]
    return None


def prompt_choice(scripts_count: int) -> int | None:
    choice = input("\nChoice: ").strip().lower()

    if choice in EXIT_CHOICES:
        return -1
    if choice in REFRESH_CHOICES:
        return None
    if not choice.isdigit():
        print("Invalid choice. Enter a number, r, or 0.")
        return None

    index = int(choice)
    if not 1 <= index <= scripts_count:
        print("Invalid number.")
        return None
    return index - 1


def main() -> None:
    while True:
        scripts = discover_scripts()
        print_menu(scripts)
        selected_index = prompt_choice(len(scripts))

        if selected_index == -1:
            print("Bye.")
            return
        if selected_index is None:
            continue

        run_script(scripts[selected_index])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
