"""Scratch ticket bot (Diamond / misc)."""

from __future__ import annotations

import os
import random
import sys
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Callable, Optional

import cv2
import mss
import numpy as np
import win32api
import win32con
import win32gui

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from lib.bot_runner import run_bot
from lib.fivem_window import focus_window
from lib.keystrokes import press_5, press_esc

Logger = Optional[Callable[[str], None]]

os.environ["FIVEM_BOT_ITERATION_SOUND"] = "0"

WINDOW_TITLE_PATTERN = r".*FiveM.*"
INTERVAL_SECONDS = int(os.getenv("FIVEM_SCRATCH_INTERVAL", "1"))
FAIL_INTERVAL_SECONDS = int(os.getenv("FIVEM_SCRATCH_FAIL_INTERVAL", "2"))
KEY_DELAY_SECONDS = float(os.getenv("FIVEM_SCRATCH_KEY_DELAY", "0.15"))

RECT_DEFAULT = (0.36, 0.34, 0.64, 0.70)  # left, top, right, bottom (relative to window)
RECT_ENV = os.getenv("FIVEM_SCRATCH_RECT", "")
RECT_PADDING = int(os.getenv("FIVEM_SCRATCH_PADDING", "6"))
STEP_PIXELS = int(os.getenv("FIVEM_SCRATCH_STEP", "10"))
MOVE_DELAY_SECONDS = float(os.getenv("FIVEM_SCRATCH_MOVE_DELAY", "0.012"))
PASSES = int(os.getenv("FIVEM_SCRATCH_PASSES", "1"))
PASS_DELAY_SECONDS = float(os.getenv("FIVEM_SCRATCH_PASS_DELAY", "0.2"))
TEMPLATE_THRESHOLD = float(os.getenv("FIVEM_SCRATCH_TEMPLATE_THRESHOLD", "0.70"))
TEMPLATE_PATH = os.getenv("FIVEM_SCRATCH_TEMPLATE", str(ROOT_DIR / "assets/scratch_texture_full.PNG")).strip()
REQUIRE_TEMPLATE = os.getenv("FIVEM_SCRATCH_REQUIRE_TEMPLATE", "1").strip().lower() not in {"0", "false", "no"}
DEBUG_SAVE = os.getenv("FIVEM_SCRATCH_DEBUG", "0").strip().lower() not in {"0", "false", "no"}
DEBUG_DIR = ROOT_DIR / "debug"
WAIT_TIMEOUT_SECONDS = float(os.getenv("FIVEM_SCRATCH_WAIT_TIMEOUT", "2"))
WAIT_POLL_SECONDS = float(os.getenv("FIVEM_SCRATCH_WAIT_POLL", "0.2"))
DONE_TEMPLATE_PATH = os.getenv(
    "FIVEM_SCRATCH_DONE_TEMPLATE",
    str(ROOT_DIR / "assets/ticket-done.PNG"),
).strip()
DONE_TEMPLATE_THRESHOLD = float(os.getenv("FIVEM_SCRATCH_DONE_THRESHOLD", "0.72"))
DONE_SLEEP_SECONDS = float(os.getenv("FIVEM_SCRATCH_DONE_SLEEP", "3"))
WAIT_FAILURES_BEFORE_SOUND = int(os.getenv("FIVEM_SCRATCH_ALERT_AFTER", "3"))
WAIT_ALERT_BEEP_MS = int(os.getenv("FIVEM_SCRATCH_ALERT_BEEP_MS", "250"))
WAIT_ALERT_FREQ = int(os.getenv("FIVEM_SCRATCH_ALERT_FREQ", "880"))
_TEMPLATE_IMAGE: Optional[np.ndarray] = None
_TEMPLATE_SIZE: tuple[int, int] = (0, 0)
_DONE_TEMPLATE_IMAGE: Optional[np.ndarray] = None
_DONE_TEMPLATE_SIZE: tuple[int, int] = (0, 0)
_WAIT_FAILURES = 0


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
        winsound.Beep(WAIT_ALERT_FREQ, WAIT_ALERT_BEEP_MS)
    except Exception as exc:
        _log(logger, f"Alert sound failed: {exc!r}")


def _parse_rect(value: str) -> Optional[tuple[float, float, float, float]]:
    try:
        parts = [float(part.strip()) for part in value.split(",") if part.strip()]
    except ValueError:
        return None
    if len(parts) != 4:
        return None
    left, top, right, bottom = parts
    if right <= left or bottom <= top:
        return None
    return left, top, right, bottom


def _load_template(logger: Logger) -> bool:
    global _TEMPLATE_IMAGE, _TEMPLATE_SIZE
    if _TEMPLATE_IMAGE is not None:
        return True
    if not TEMPLATE_PATH:
        _log(logger, "Scratch template path not set.")
        return False
    template_path = Path(TEMPLATE_PATH)
    if not template_path.exists():
        _log(logger, f"Scratch template not found: {template_path}")
        return False

    template = cv2.imread(str(template_path), cv2.IMREAD_UNCHANGED)
    if template is None:
        _log(logger, f"Scratch template could not be loaded: {template_path}")
        return False
    if template.ndim == 3 and template.shape[2] == 4:
        template = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)
    _TEMPLATE_IMAGE = template
    _TEMPLATE_SIZE = (template.shape[1], template.shape[0])
    return True


def _load_done_template(logger: Logger) -> bool:
    global _DONE_TEMPLATE_IMAGE, _DONE_TEMPLATE_SIZE
    if _DONE_TEMPLATE_IMAGE is not None:
        return True
    if not DONE_TEMPLATE_PATH:
        _log(logger, "Ticket done template path not set.")
        return False
    template_path = Path(DONE_TEMPLATE_PATH)
    if not template_path.exists():
        _log(logger, f"Ticket done template not found: {template_path}")
        return False

    template = cv2.imread(str(template_path), cv2.IMREAD_UNCHANGED)
    if template is None:
        _log(logger, f"Ticket done template could not be loaded: {template_path}")
        return False
    if template.ndim == 3 and template.shape[2] == 4:
        template = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)
    _DONE_TEMPLATE_IMAGE = template
    _DONE_TEMPLATE_SIZE = (template.shape[1], template.shape[0])
    return True


def _capture_window(hwnd: int) -> tuple[np.ndarray, tuple[int, int]]:
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width, height = right - left, bottom - top
    with mss.mss() as screen_capture:
        monitor = {"left": left, "top": top, "width": width, "height": height}
        image = np.array(screen_capture.grab(monitor))
    return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR), (left, top)


@dataclass(frozen=True)
class TemplateMatch:
    rect: tuple[int, int, int, int]
    origin: tuple[int, int]
    snapshot: np.ndarray
    score: float


def _find_template_match(hwnd: int, logger: Logger) -> Optional[TemplateMatch]:
    if not _load_template(logger):
        return None
    if _TEMPLATE_IMAGE is None:
        return None
    snapshot, origin = _capture_window(hwnd)
    result = cv2.matchTemplate(snapshot, _TEMPLATE_IMAGE, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val < TEMPLATE_THRESHOLD:
        _log(logger, f"Scratch template match below threshold ({max_val:.2f}).")
        return None

    w, h = _TEMPLATE_SIZE
    left = origin[0] + max_loc[0]
    top = origin[1] + max_loc[1]
    rect = (left, top, left + w, top + h)
    return TemplateMatch(rect=rect, origin=origin, snapshot=snapshot, score=max_val)


def _find_done_match(hwnd: int, logger: Logger) -> bool:
    if not _load_done_template(logger):
        return False
    if _DONE_TEMPLATE_IMAGE is None:
        return False
    snapshot, _ = _capture_window(hwnd)
    result = cv2.matchTemplate(snapshot, _DONE_TEMPLATE_IMAGE, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)
    if max_val < DONE_TEMPLATE_THRESHOLD:
        return False
    _log(logger, f"Ticket done detected ({max_val:.2f}).")
    return True


def _save_debug_snapshot(match: TemplateMatch, logger: Logger) -> None:
    if not DEBUG_SAVE:
        return
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    image = match.snapshot.copy()
    rel_left = match.rect[0] - match.origin[0]
    rel_top = match.rect[1] - match.origin[1]
    rel_right = match.rect[2] - match.origin[0]
    rel_bottom = match.rect[3] - match.origin[1]
    cv2.rectangle(image, (rel_left, rel_top), (rel_right, rel_bottom), (0, 255, 0), 2)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = DEBUG_DIR / f"scratch_match_{timestamp}.png"
    cv2.imwrite(str(filename), image)
    _log(logger, f"Saved debug screenshot: {filename}")


def _resolve_scratch_rect(hwnd: int, logger: Logger) -> tuple[int, int, int, int]:
    match = _find_template_match(hwnd, logger)
    if match is not None:
        _save_debug_snapshot(match, logger)
        return match.rect

    if REQUIRE_TEMPLATE:
        raise RuntimeError("Scratch template not found.")

    rect = _parse_rect(RECT_ENV) if RECT_ENV else None
    if rect is None:
        rect = RECT_DEFAULT

    left, top, right, bottom = rect
    win_left, win_top, win_right, win_bottom = win32gui.GetWindowRect(hwnd)
    width, height = win_right - win_left, win_bottom - win_top

    if max(rect) <= 1.0:
        return (
            win_left + int(left * width),
            win_top + int(top * height),
            win_left + int(right * width),
            win_top + int(bottom * height),
        )

    return (
        win_left + int(left),
        win_top + int(top),
        win_left + int(right),
        win_top + int(bottom),
    )


def _wait_for_ticket(hwnd: int, logger: Logger) -> bool:
    if not _load_template(logger):
        if REQUIRE_TEMPLATE:
            return False
        time.sleep(WAIT_TIMEOUT_SECONDS)
        return True

    start = time.time()
    while time.time() - start <= WAIT_TIMEOUT_SECONDS:
        if _find_template_match(hwnd, logger) is not None:
            _log(logger, "Scratch ticket detected.")
            return True
        time.sleep(WAIT_POLL_SECONDS)

    _log(logger, "Scratch ticket not detected before timeout.")
    return False


def _build_snake_points(
    left: int,
    top: int,
    right: int,
    bottom: int,
    *,
    step: int,
    x_offset: int = 0,
) -> list[tuple[int, int]]:
    points: list[tuple[int, int]] = []
    x = left + x_offset
    direction = 1
    while x <= right:
        if direction > 0:
            points.append((x, top))
            points.append((x, bottom))
        else:
            points.append((x, bottom))
            points.append((x, top))
        x += step
        direction *= -1
    return points


def _drag_path(points: list[tuple[int, int]]) -> None:
    if not points:
        return
    win32api.SetCursorPos(points[0])
    time.sleep(0.01)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.01)
    for x, y in points[1:]:
        win32api.SetCursorPos((x, y))
        time.sleep(MOVE_DELAY_SECONDS)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.01)


def _scratch_action(window: object, logger: Logger) -> bool:
    global _WAIT_FAILURES
    if not focus_window(window, logger):
        return False

    if not press_5(logger):
        return False
    time.sleep(KEY_DELAY_SECONDS)

    if not _wait_for_ticket(window.handle, logger):
        _WAIT_FAILURES += 1
        if _WAIT_FAILURES >= max(1, WAIT_FAILURES_BEFORE_SOUND):
            _play_alert(logger)
            _WAIT_FAILURES = 0
        return False
    _WAIT_FAILURES = 0

    try:
        left, top, right, bottom = _resolve_scratch_rect(window.handle, logger)
    except RuntimeError as exc:
        _log(logger, str(exc))
        return False
    left += RECT_PADDING
    top += RECT_PADDING
    right -= RECT_PADDING
    bottom -= RECT_PADDING

    if right <= left or bottom <= top:
        _log(logger, "Scratch rectangle is invalid after padding.")
        return False

    step = max(6, STEP_PIXELS)
    for pass_index in range(max(1, PASSES)):
        x_offset = int((pass_index % 2) * step * 0.5)
        jitter = random.randint(-2, 2)
        points = _build_snake_points(
            left + jitter,
            top + jitter,
            right - jitter,
            bottom - jitter,
            step=step,
            x_offset=x_offset,
        )
        _drag_path(points)
        if pass_index < PASSES - 1:
            time.sleep(PASS_DELAY_SECONDS)

    if _find_done_match(window.handle, logger):
        press_esc(logger)
        time.sleep(DONE_SLEEP_SECONDS)

    _log(logger, "Scratch pass complete.")
    return True


def main() -> None:
    run_bot(
        action=_scratch_action,
        interval_seconds=INTERVAL_SECONDS,
        fail_interval_seconds=FAIL_INTERVAL_SECONDS,
        title_pattern=WINDOW_TITLE_PATTERN,
        random_range=(0.0, 0.0),
    )


if __name__ == "__main__":
    main()
