"""Keyboard and key-combo helpers for Windows/FiveM automation."""

from __future__ import annotations

import ctypes
import time
from typing import Callable, Optional

import win32api
import win32con

Logger = Optional[Callable[[str], None]]


def _log(logger: Logger, message: str) -> None:
    if logger is not None:
        logger(message)


def _press_vk(
    vk_code: int,
    label: str,
    logger: Logger = None,
    *,
    hold_seconds: float = 0.02,
    extended: bool = False,
) -> bool:
    """Press and release one virtual key code."""
    try:
        scan = ctypes.windll.user32.MapVirtualKeyW(vk_code, 0)
        down_flags = win32con.KEYEVENTF_EXTENDEDKEY if extended else 0
        up_flags = down_flags | win32con.KEYEVENTF_KEYUP
        win32api.keybd_event(vk_code, scan, down_flags, 0)
        time.sleep(hold_seconds)
        win32api.keybd_event(vk_code, scan, up_flags, 0)
        _log(logger, f"Sent '{label}'.")
        return True
    except Exception as exc:  # pragma: no cover - defensive logging
        _log(logger, f"Failed to send '{label}': {exc!r}")
        return False


def press_x(logger: Logger = None) -> bool:
    return _press_vk(0x58, "X", logger)


def press_g(logger: Logger = None) -> bool:
    return _press_vk(0x47, "G", logger)


def press_tab(logger: Logger = None) -> bool:
    return _press_vk(0x09, "Tab", logger)


def press_e(logger: Logger = None) -> bool:
    return _press_vk(0x45, "E", logger)


def press_down(logger: Logger = None) -> bool:
    return _press_vk(win32con.VK_DOWN, "Arrow Down", logger, hold_seconds=0.03, extended=True)


def press_enter(logger: Logger = None) -> bool:
    return _press_vk(win32con.VK_RETURN, "Enter", logger, hold_seconds=0.03)


def press_alt_tab(logger: Logger = None) -> bool:
    """Press Alt+Tab once."""
    try:
        alt_scan = ctypes.windll.user32.MapVirtualKeyW(win32con.VK_MENU, 0)
        tab_scan = ctypes.windll.user32.MapVirtualKeyW(win32con.VK_TAB, 0)

        win32api.keybd_event(win32con.VK_MENU, alt_scan, 0, 0)
        time.sleep(0.02)
        win32api.keybd_event(win32con.VK_TAB, tab_scan, 0, 0)
        time.sleep(0.02)
        win32api.keybd_event(win32con.VK_TAB, tab_scan, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.02)
        win32api.keybd_event(win32con.VK_MENU, alt_scan, win32con.KEYEVENTF_KEYUP, 0)
        _log(logger, "Sent Alt+Tab.")
        return True
    except Exception as exc:  # pragma: no cover - defensive logging
        _log(logger, f"Failed to send Alt+Tab: {exc!r}")
        return False
