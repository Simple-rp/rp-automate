"""Saumon boat harvesting bot (Diamond / Peche)."""

from __future__ import annotations

import ctypes
import os
import sys
import time
from pathlib import Path
from typing import Callable, Optional

import win32api
import win32con

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from lib.bot_runner import run_bot
from lib.fivem_window import focus_window
from lib.keystrokes import press_e, press_f, press_tab, press_x
from lib.template_clicker import TemplateClicker
from lib.template_paths import collect_image_templates

Logger = Optional[Callable[[str], None]]

INTERVAL_SECONDS = int(os.getenv("FIVEM_BOT_INTERVAL", "155"))
FAIL_INTERVAL_SECONDS = int(os.getenv("FIVEM_BOT_FAIL_INTERVAL", "30"))
WINDOW_TITLE_PATTERN = r".*FiveM.*"
TEMPLATE_DIR = ROOT_DIR / "assets/items/peches"
MATCH_THRESHOLD = float(os.getenv("FIVEM_SAUMON_MATCH_THRESHOLD", "0.75"))
DEBUG = False

STOP_RECOLTE_DELAY_SECONDS = float(os.getenv("FIVEM_SAUMON_STOP_DELAY", "0.4"))
ENTER_BOAT_DELAY_SECONDS = float(os.getenv("FIVEM_SAUMON_ENTER_BOAT_DELAY", "3.0"))
EXIT_BOAT_DELAY_SECONDS = float(os.getenv("FIVEM_SAUMON_EXIT_BOAT_DELAY", "3.0"))
PRE_FIND_DELAY_SECONDS = float(os.getenv("FIVEM_SAUMON_PRE_FIND_DELAY", "1.2"))
FIND_TIMEOUT_SECONDS = float(os.getenv("FIVEM_SAUMON_FIND_TIMEOUT", "2.5"))
FIND_POLL_SECONDS = float(os.getenv("FIVEM_SAUMON_FIND_POLL", "0.2"))
POST_SHIFT_CLICK_DELAY_SECONDS = float(os.getenv("FIVEM_SAUMON_POST_SHIFT_CLICK_DELAY", "0.5"))
CTRL_CLICK_REPEAT = 2
CTRL_CLICK_REPEAT_DELAY_SECONDS = float(os.getenv("FIVEM_SAUMON_CTRL_CLICK_REPEAT_DELAY", "0.15"))
CTRL_CLICK_VERIFY_DELAY_SECONDS = float(os.getenv("FIVEM_SAUMON_CTRL_CLICK_VERIFY_DELAY", "0.35"))
STUCK_ALERT_SOUND = os.getenv(
    "FIVEM_SAUMON_STUCK_ALERT_SOUND",
    str(ROOT_DIR / "assets/sound/beep-warn.wav"),
).strip()
STUCK_ALERT_FREQ = int(os.getenv("FIVEM_SAUMON_STUCK_ALERT_FREQ", "880"))
STUCK_ALERT_BEEP_MS = int(os.getenv("FIVEM_SAUMON_STUCK_ALERT_BEEP_MS", "500"))
STUCK_ALERT_REPEAT = int(os.getenv("FIVEM_SAUMON_STUCK_ALERT_REPEAT", "4"))
STUCK_ALERT_REPEAT_DELAY_SECONDS = float(os.getenv("FIVEM_SAUMON_STUCK_ALERT_REPEAT_DELAY", "0.12"))
INVENTORY_CLOSE_DELAY_SECONDS = float(os.getenv("FIVEM_SAUMON_INVENTORY_CLOSE_DELAY", "0.5"))
POST_E_DELAY_SECONDS = float(os.getenv("FIVEM_SAUMON_POST_E_DELAY", "0.4"))


def _log(logger: Logger, message: str) -> None:
    if logger is not None:
        logger(message)


def _play_alert(logger: Logger) -> None:
    try:
        import winsound
    except Exception:
        _log(logger, "Alert sound skipped (winsound unavailable).")
        return

    try:
        repeat = max(1, STUCK_ALERT_REPEAT)
        for index in range(repeat):
            if STUCK_ALERT_SOUND and Path(STUCK_ALERT_SOUND).exists():
                winsound.PlaySound(STUCK_ALERT_SOUND, winsound.SND_FILENAME)
            else:
                winsound.Beep(STUCK_ALERT_FREQ, STUCK_ALERT_BEEP_MS)

            if index < repeat - 1:
                time.sleep(max(0.0, STUCK_ALERT_REPEAT_DELAY_SECONDS))
    except Exception as exc:
        _log(logger, f"Alert sound failed: {exc!r}")


def _build_saumon_clickers() -> list[TemplateClicker]:
    template_paths = collect_image_templates(TEMPLATE_DIR, extensions=(".png",))
    return [
        TemplateClicker(
            template_path=template_path,
            match_threshold=MATCH_THRESHOLD,
            capture_side="left",
            ctrl_click=False,
        )
        for template_path in template_paths
    ]


def _key_down(vk_code: int) -> None:
    scan = ctypes.windll.user32.MapVirtualKeyW(vk_code, 0)
    win32api.keybd_event(vk_code, scan, 0, 0)


def _key_up(vk_code: int) -> None:
    scan = ctypes.windll.user32.MapVirtualKeyW(vk_code, 0)
    win32api.keybd_event(vk_code, scan, win32con.KEYEVENTF_KEYUP, 0)


def _ctrl_click(pos: tuple[int, int], logger: Logger) -> None:
    x, y = map(int, pos)

    for index in range(CTRL_CLICK_REPEAT):
        win32api.SetCursorPos((x, y))
        time.sleep(0.02)

        try:
            _key_down(win32con.VK_CONTROL)
            time.sleep(0.01)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(0.01)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            time.sleep(0.01)
        finally:
            _key_up(win32con.VK_CONTROL)

        if index < CTRL_CLICK_REPEAT - 1:
            time.sleep(max(0.0, CTRL_CLICK_REPEAT_DELAY_SECONDS))

    _log(logger, f"Ctrl-clicked item {CTRL_CLICK_REPEAT}x at {pos}.")


def _find_and_ctrl_click_saumon(
    clickers: list[TemplateClicker],
    window: object,
    logger: Logger,
) -> bool:
    loaded_clickers = [clicker for clicker in clickers if clicker.is_loaded]
    if not loaded_clickers:
        _log(logger, f"No item templates loaded from {TEMPLATE_DIR}.")
        return False

    deadline = time.time() + max(0.0, FIND_TIMEOUT_SECONDS)
    while True:
        for clicker in loaded_clickers:
            pos = clicker.find_match(window.handle, logger)
            if pos is None:
                continue

            _ctrl_click(pos, logger)
            time.sleep(max(0.0, CTRL_CLICK_VERIFY_DELAY_SECONDS))
            if clicker.find_match(window.handle, logger) is not None:
                _log(
                    logger,
                    f"Item still on left side after ctrl-click using template '{clicker.template_path.name}'.",
                )
                _play_alert(logger)
                raise SystemExit(1)
            _log(logger, f"Item matched using template '{clicker.template_path.name}'.")
            return True

        if time.time() >= deadline:
            _log(logger, f"Item not found on left side after {FIND_TIMEOUT_SECONDS:.1f}s.")
            return False

        time.sleep(max(0.01, FIND_POLL_SECONDS))


def _make_recolte_action(clickers: list[TemplateClicker]) -> Callable[[object, Logger], bool]:
    def _recolte_saumon_action(window: object, logger: Logger) -> bool:
        if not focus_window(window, logger):
            return False

        if not press_x(logger):
            return False
        time.sleep(max(0.0, STOP_RECOLTE_DELAY_SECONDS))

        if not press_f(logger):
            return False
        time.sleep(max(0.0, ENTER_BOAT_DELAY_SECONDS))

        if not press_tab(logger):
            return False
        time.sleep(max(0.0, PRE_FIND_DELAY_SECONDS))

        saumon_found = _find_and_ctrl_click_saumon(clickers, window, logger)
        time.sleep(max(0.0, POST_SHIFT_CLICK_DELAY_SECONDS))

        if not press_tab(logger):
            return False
        time.sleep(max(0.0, INVENTORY_CLOSE_DELAY_SECONDS))

        if not press_f(logger):
            return False
        time.sleep(max(0.0, EXIT_BOAT_DELAY_SECONDS))

        if not press_e(logger):
            return False
        time.sleep(max(0.0, POST_E_DELAY_SECONDS))

        return saumon_found

    return _recolte_saumon_action


def main() -> None:
    saumon_clickers = _build_saumon_clickers()
    run_bot(
        action=_make_recolte_action(saumon_clickers),
        interval_seconds=INTERVAL_SECONDS,
        fail_interval_seconds=FAIL_INTERVAL_SECONDS,
        title_pattern=WINDOW_TITLE_PATTERN,
        debug=DEBUG,
    )


if __name__ == "__main__":
    main()
