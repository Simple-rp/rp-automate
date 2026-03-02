"""Template matching and click helpers for inventory items."""

from __future__ import annotations

import ctypes
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, Tuple

import cv2
import mss
import numpy as np
import win32api
import win32con
import win32gui

Logger = Optional[Callable[[str], None]]
CaptureSide = str


def _log(logger: Logger, message: str) -> None:
    if logger is not None:
        logger(message)


@dataclass
class TemplateClicker:
    template_path: Path
    match_threshold: float = 0.75
    capture_side: CaptureSide = "left"  # "left", "right" or "full"
    ctrl_click: bool = True
    _template_image: Optional[np.ndarray] = field(init=False, default=None, repr=False)
    _template_w: int = field(init=False, default=0, repr=False)
    _template_h: int = field(init=False, default=0, repr=False)

    def __post_init__(self) -> None:
        if self.capture_side not in {"left", "right", "full"}:
            raise ValueError("capture_side must be 'left', 'right' or 'full'")
        self._load_template()

    def _load_template(self) -> None:
        if not self.template_path.exists():
            return
        image = cv2.imread(str(self.template_path), cv2.IMREAD_UNCHANGED)
        if image is None:
            return
        if image.ndim == 3 and image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        self._template_image = image
        self._template_w = image.shape[1]
        self._template_h = image.shape[0]

    @property
    def is_loaded(self) -> bool:
        return self._template_image is not None

    def find_match(self, hwnd: int, logger: Logger = None) -> Optional[Tuple[int, int]]:
        """Return absolute (x, y) center if template is found."""
        if self._template_image is None:
            _log(logger, f"Template image not loaded: {self.template_path}")
            return None
        try:
            snapshot, origin = self._capture_window_image(hwnd)
            match = self._match_template(snapshot)
            if match is None:
                return None
            return origin[0] + match[0], origin[1] + match[1]
        except Exception as exc:  # pragma: no cover - defensive logging
            _log(logger, f"Detection failed: {exc!r}")
            return None

    def click(self, pos: Tuple[int, int], button: str = "left") -> None:
        self._move_mouse_and_click(pos, button=button)

    def find_and_click(
        self,
        hwnd: int,
        logger: Logger = None,
        *,
        log_not_found: bool = True,
        button: str = "left",
    ) -> bool:
        """Locate template in configured capture zone and click it."""
        target = self.find_match(hwnd, logger)
        if target is None:
            if log_not_found:
                _log(logger, "Item not found on screen.")
            return False
        self._move_mouse_and_click(target, button=button)
        action = "Right-clicked" if button == "right" else "Clicked"
        _log(logger, f"{action} item at {target}.")
        return True

    def _capture_window_image(self, hwnd: int) -> Tuple[np.ndarray, Tuple[int, int]]:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        full_width, height = right - left, bottom - top
        if self.capture_side == "full":
            cap_left = left
            cap_width = full_width
        else:
            half_width = full_width // 2
            cap_left = left if self.capture_side == "left" else left + half_width
            cap_width = half_width
        with mss.mss() as screen_capture:
            monitor = {"left": cap_left, "top": top, "width": cap_width, "height": height}
            image = np.array(screen_capture.grab(monitor))
        return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR), (cap_left, top)

    def _match_template(self, source: np.ndarray) -> Optional[Tuple[int, int]]:
        if self._template_image is None:
            return None
        result = cv2.matchTemplate(source, self._template_image, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val < self.match_threshold:
            return None
        center_x = max_loc[0] + self._template_w // 2
        center_y = max_loc[1] + self._template_h // 2
        return center_x, center_y

    def _move_mouse_and_click(self, pos: Tuple[int, int], button: str = "left") -> None:
        if button not in {"left", "right"}:
            raise ValueError("button must be 'left' or 'right'")
        x, y = map(int, pos)
        win32api.SetCursorPos((x, y))
        time.sleep(0.02)
        if self.ctrl_click:
            self._key_down(win32con.VK_CONTROL)
            time.sleep(0.01)
        down_flag = win32con.MOUSEEVENTF_RIGHTDOWN if button == "right" else win32con.MOUSEEVENTF_LEFTDOWN
        up_flag = win32con.MOUSEEVENTF_RIGHTUP if button == "right" else win32con.MOUSEEVENTF_LEFTUP
        win32api.mouse_event(down_flag, 0, 0, 0, 0)
        time.sleep(0.01)
        win32api.mouse_event(up_flag, 0, 0, 0, 0)
        time.sleep(0.01)
        if self.ctrl_click:
            self._key_up(win32con.VK_CONTROL)

    @staticmethod
    def _key_down(vk_code: int) -> None:
        scan = ctypes.windll.user32.MapVirtualKeyW(vk_code, 0)
        win32api.keybd_event(vk_code, scan, 0, 0)

    @staticmethod
    def _key_up(vk_code: int) -> None:
        scan = ctypes.windll.user32.MapVirtualKeyW(vk_code, 0)
        win32api.keybd_event(vk_code, scan, win32con.KEYEVENTF_KEYUP, 0)
