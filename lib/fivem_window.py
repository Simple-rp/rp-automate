"""FiveM window discovery and focus helpers."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Callable, Optional

import win32con
import win32gui

Logger = Optional[Callable[[str], None]]


@dataclass
class WindowInfo:
    handle: int
    title: str

    def window_text(self) -> str:
        return self.title


def _log(logger: Logger, message: str) -> None:
    if logger is not None:
        logger(message)


def find_fivem_window(title_pattern: str, logger: Logger = None) -> Optional[WindowInfo]:
    """Return the first visible FiveM window if found."""
    try:
        title_re = re.compile(title_pattern)
        candidates: list[WindowInfo] = []

        def _collect(hwnd: int, _data: object) -> bool:
            if not win32gui.IsWindowVisible(hwnd):
                return True
            if not win32gui.IsWindowEnabled(hwnd):
                return True
            title = win32gui.GetWindowText(hwnd)
            if not title:
                return True
            if title_re.search(title) is None:
                return True
            candidates.append(WindowInfo(handle=hwnd, title=title))
            return True

        win32gui.EnumWindows(_collect, None)

        if candidates:
            _log(logger, f"Found window: '{candidates[0].title}'")
            return candidates[0]
        return None
    except Exception as exc:  # pragma: no cover - defensive logging
        _log(logger, f"Failed to enumerate windows: {exc!r}")
        return None


def focus_window(window: WindowInfo, logger: Logger = None, focus_delay_seconds: float = 0.8) -> bool:
    """Bring the target window to foreground and focus it."""
    try:
        hwnd = window.handle
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        win32gui.SetActiveWindow(hwnd)
        if hasattr(window, "set_focus"):
            try:
                window.set_focus()
            except Exception as exc:
                _log(logger, f"Could not set focus via wrapper: {exc!r}")
        time.sleep(focus_delay_seconds)
        return True
    except Exception as exc:  # pragma: no cover - defensive logging
        _log(logger, f"Could not focus window: {exc!r}")
        return False
