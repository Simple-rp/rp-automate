"""FiveM window discovery and focus helpers."""

from __future__ import annotations

import time
from typing import Callable, Optional

import win32con
import win32gui
from pywinauto import Desktop
from pywinauto.base_wrapper import BaseWrapper

Logger = Optional[Callable[[str], None]]


def _log(logger: Logger, message: str) -> None:
    if logger is not None:
        logger(message)


def find_fivem_window(title_pattern: str, logger: Logger = None) -> Optional[BaseWrapper]:
    """Return the first visible FiveM window if found."""
    try:
        windows = Desktop(backend="uia").windows(
            title_re=title_pattern,
            visible_only=True,
            enabled_only=True,
        )
        if windows:
            _log(logger, f"Found window: '{windows[0].window_text()}'")
            return windows[0]
        return None
    except Exception as exc:  # pragma: no cover - defensive logging
        _log(logger, f"Failed to enumerate windows: {exc!r}")
        return None


def focus_window(window: BaseWrapper, logger: Logger = None, focus_delay_seconds: float = 0.8) -> bool:
    """Bring the target window to foreground and focus it."""
    try:
        hwnd = window.handle
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        win32gui.SetActiveWindow(hwnd)
        window.set_focus()
        time.sleep(focus_delay_seconds)
        return True
    except Exception as exc:  # pragma: no cover - defensive logging
        _log(logger, f"Could not focus window: {exc!r}")
        return False
