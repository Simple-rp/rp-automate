"""FiveM window discovery and focus helpers."""

from __future__ import annotations

import ctypes
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


def _is_foreground_window(hwnd: int) -> bool:
    return win32gui.GetForegroundWindow() == hwnd


def _send_alt_nudge() -> None:
    """Let Windows accept a following SetForegroundWindow call more often."""
    scan = ctypes.windll.user32.MapVirtualKeyW(win32con.VK_MENU, 0)
    ctypes.windll.user32.keybd_event(win32con.VK_MENU, scan, 0, 0)
    time.sleep(0.02)
    ctypes.windll.user32.keybd_event(win32con.VK_MENU, scan, win32con.KEYEVENTF_KEYUP, 0)


def _get_window_thread_id(hwnd: int) -> int:
    process_id = ctypes.c_ulong()
    return int(ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id)))


def _get_current_thread_id() -> int:
    return int(ctypes.windll.kernel32.GetCurrentThreadId())


def _attach_thread_input(source_thread_id: int, target_thread_id: int, attach: bool) -> bool:
    return bool(ctypes.windll.user32.AttachThreadInput(source_thread_id, target_thread_id, attach))


def _set_foreground_direct(hwnd: int, logger: Logger) -> bool:
    try:
        win32gui.SetForegroundWindow(hwnd)
        return _is_foreground_window(hwnd)
    except Exception as exc:
        _log(logger, f"Direct foreground focus failed: {exc!r}")
        return _is_foreground_window(hwnd)


def _set_foreground_with_alt(hwnd: int, logger: Logger) -> bool:
    try:
        _send_alt_nudge()
        win32gui.SetForegroundWindow(hwnd)
        return _is_foreground_window(hwnd)
    except Exception as exc:
        _log(logger, f"Alt foreground focus failed: {exc!r}")
        return _is_foreground_window(hwnd)


def _set_foreground_attached(hwnd: int, logger: Logger) -> bool:
    attached_threads: list[tuple[int, int]] = []
    try:
        current_thread_id = _get_current_thread_id()
        target_thread_id = _get_window_thread_id(hwnd)
        foreground_hwnd = win32gui.GetForegroundWindow()
        foreground_thread_id = 0
        if foreground_hwnd:
            foreground_thread_id = _get_window_thread_id(foreground_hwnd)

        for source_thread_id in {current_thread_id, foreground_thread_id}:
            if source_thread_id and source_thread_id != target_thread_id:
                if _attach_thread_input(source_thread_id, target_thread_id, True):
                    attached_threads.append((source_thread_id, target_thread_id))

        try:
            win32gui.BringWindowToTop(hwnd)
        except Exception as exc:
            _log(logger, f"BringWindowToTop failed: {exc!r}")
        try:
            win32gui.SetActiveWindow(hwnd)
        except Exception as exc:
            _log(logger, f"SetActiveWindow failed: {exc!r}")
        win32gui.SetForegroundWindow(hwnd)
        return _is_foreground_window(hwnd)
    except Exception as exc:
        _log(logger, f"Attached foreground focus failed: {exc!r}")
        return _is_foreground_window(hwnd)
    finally:
        for source_thread_id, target_thread_id in reversed(attached_threads):
            try:
                _attach_thread_input(source_thread_id, target_thread_id, False)
            except Exception:
                pass


def focus_window(window: WindowInfo, logger: Logger = None, focus_delay_seconds: float = 0.8) -> bool:
    """Bring the target window to foreground and focus it."""
    hwnd = window.handle
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    except Exception as exc:  # pragma: no cover - defensive logging
        _log(logger, f"Could not restore window: {exc!r}")
        return False

    focused = (
        _is_foreground_window(hwnd)
        or _set_foreground_direct(hwnd, logger)
        or _set_foreground_with_alt(hwnd, logger)
        or _set_foreground_attached(hwnd, logger)
    )

    if not focused:
        _log(logger, "Could not focus window after all focus attempts.")
        return False

    if hasattr(window, "set_focus"):
        try:
            window.set_focus()
        except Exception as exc:
            _log(logger, f"Could not set focus via wrapper: {exc!r}")

    time.sleep(focus_delay_seconds)
    return True
