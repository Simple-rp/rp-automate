"""Peche bot (Diamond / misc)."""

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
from lib.keystrokes import press_4, press_5, press_c, press_tab
from lib.template_clicker import TemplateClicker

Logger = Optional[Callable[[str], None]]

os.environ["FIVEM_BOT_ITERATION_SOUND"] = "0"



#### CLICKING PARAMETERS
EMPTY_SPAM_HOLD_SECONDS = float(os.getenv("FIVEM_PECHE_EMPTY_HOLD_SECONDS", "1.1"))
EMPTY_SPAM_RELEASE_SECONDS = float(os.getenv("FIVEM_PECHE_EMPTY_RELEASE_SECONDS", "1.4"))

INVENTORY_EVERY = int(os.getenv("FIVEM_PECHE_INVENTORY_EVERY", "15"))


WINDOW_TITLE_PATTERN = r".*FiveM.*"
INTERVAL_SECONDS = int(os.getenv("FIVEM_PECHE_INTERVAL", "0"))
FAIL_INTERVAL_SECONDS = int(os.getenv("FIVEM_PECHE_FAIL_INTERVAL", "1"))
KEY_DELAY_SECONDS = float(os.getenv("FIVEM_PECHE_KEY_DELAY", "0.5"))
DELAY_BETWEEN_5_AND_4 = float(os.getenv("FIVEM_PECHE_DELAY_5_4", "1.0"))
C_HOLD_SECONDS = float(os.getenv("FIVEM_PECHE_C_HOLD", "0.1"))
POST_4_DELAY_SECONDS = float(os.getenv("FIVEM_PECHE_POST_4_DELAY", "1.0"))
POST_STOPPER_DELAY_SECONDS = float(os.getenv("FIVEM_PECHE_POST_STOPPER_DELAY", "1.0"))

INVENTORY_OPEN_DELAY_SECONDS = float(os.getenv("FIVEM_PECHE_INVENTORY_OPEN_DELAY", "1.0"))
INVENTORY_CLOSE_DELAY_SECONDS = float(os.getenv("FIVEM_PECHE_INVENTORY_CLOSE_DELAY", "0.2"))
INVENTORY_CHECK_OPEN_TEMPLATE_PATH = os.getenv(
    "FIVEM_PECHE_INVENTORY_CHECK_OPEN_TEMPLATE",
    str(ROOT_DIR / "assets/fishing/check-inventory-open.PNG"),
).strip()
INVENTORY_CHECK_OPEN_THRESHOLD = float(os.getenv("FIVEM_PECHE_INVENTORY_CHECK_OPEN_THRESHOLD", "0.75"))
INVENTORY_CHECK_TIMEOUT_SECONDS = float(os.getenv("FIVEM_PECHE_INVENTORY_CHECK_TIMEOUT", "2.0"))
INVENTORY_CHECK_POLL_SECONDS = float(os.getenv("FIVEM_PECHE_INVENTORY_CHECK_POLL", "0.2"))
INVENTORY_OPEN_POST_ACTION_DELAY_SECONDS = float(
    os.getenv("FIVEM_PECHE_INVENTORY_OPEN_POST_ACTION_DELAY", "0.8")
)
POISSON_TEMPLATE_PATH = os.getenv(
    "FIVEM_PECHE_POISSON_TEMPLATE",
    str(ROOT_DIR / "assets/items/poisson.PNG"),
).strip()
POISSON_THRESHOLD = float(os.getenv("FIVEM_PECHE_POISSON_THRESHOLD", "0.75"))
POISSON_LIGHT_TEMPLATE_PATH = os.getenv(
    "FIVEM_PECHE_POISSON_LIGHT_TEMPLATE",
    str(ROOT_DIR / "assets/items/poisson-light.PNG"),
).strip()
POISSON_LIGHT_THRESHOLD = float(os.getenv("FIVEM_PECHE_POISSON_LIGHT_THRESHOLD", "0.75"))
POISSON_CLICK_DELAY_SECONDS = float(os.getenv("FIVEM_PECHE_POISSON_CLICK_DELAY", "0.45"))
POISSON_MAX_CLICKS = int(os.getenv("FIVEM_PECHE_POISSON_MAX_CLICKS", "50"))
POISSON_FIND_TIMEOUT_SECONDS = float(os.getenv("FIVEM_PECHE_POISSON_FIND_TIMEOUT", "2.0"))
POISSON_FIND_POLL_SECONDS = float(os.getenv("FIVEM_PECHE_POISSON_FIND_POLL", "0.2"))
POISSON_CTRL_CLICKS_PER_MATCH = int(os.getenv("FIVEM_PECHE_POISSON_CTRL_CLICKS_PER_MATCH", "5"))
POISSON_MOVE_AFTER_CLICK_PIXELS = int(os.getenv("FIVEM_PECHE_POISSON_MOVE_AFTER_CLICK_PIXELS", "18"))
POISSON_MOVE_AFTER_CLICK_DELAY_SECONDS = float(
    os.getenv("FIVEM_PECHE_POISSON_MOVE_AFTER_CLICK_DELAY", "0.05")
)
APPAT_TEMPLATE_PATH = os.getenv(
    "FIVEM_PECHE_APPAT_TEMPLATE",
    str(ROOT_DIR / "assets/items/appat.PNG"),
).strip()
APPAT_THRESHOLD = float(os.getenv("FIVEM_PECHE_APPAT_THRESHOLD", "0.75"))
APPAT_FIND_TIMEOUT_SECONDS = float(os.getenv("FIVEM_PECHE_APPAT_FIND_TIMEOUT", "2.0"))
APPAT_FIND_POLL_SECONDS = float(os.getenv("FIVEM_PECHE_APPAT_FIND_POLL", "0.2"))
INVENTORY_INTERACTION_DELAY_SECONDS = float(
    os.getenv("FIVEM_PECHE_INVENTORY_INTERACTION_DELAY", "0.35")
)

_SEQUENCE_COUNT = 0

STARTED_TEMPLATE_PATH = os.getenv(
    "FIVEM_PECHE_STARTED_TEMPLATE",
    str(ROOT_DIR / "assets/fishing/started.PNG"),
).strip()
STARTED_THRESHOLD = float(os.getenv("FIVEM_PECHE_STARTED_THRESHOLD", "0.75"))

CATCHED_TEMPLATE_PATH = os.getenv(
    "FIVEM_PECHE_CATCHED_TEMPLATE",
    str(ROOT_DIR / "assets/fishing/catched.png"),
).strip()
CATCHED_THRESHOLD = float(os.getenv("FIVEM_PECHE_CATCHED_THRESHOLD", "0.75"))
CATCHED_TIMEOUT_SECONDS = float(os.getenv("FIVEM_PECHE_CATCHED_TIMEOUT", "20"))
CATCHED_POLL_SECONDS = float(os.getenv("FIVEM_PECHE_CATCHED_POLL", "0.2"))
CATCHED_POST_DELAY_SECONDS = float(os.getenv("FIVEM_PECHE_CATCHED_POST_DELAY", "1.0"))

EMPTY_TEMPLATE_PATH = os.getenv(
    "FIVEM_PECHE_EMPTY_TEMPLATE",
    str(ROOT_DIR / "assets/fishing/empty-circle.PNG"),
).strip()
EMPTY_THRESHOLD = float(os.getenv("FIVEM_PECHE_EMPTY_THRESHOLD", "0.75"))
EMPTY_SPAM_SECONDS = float(os.getenv("FIVEM_PECHE_EMPTY_SPAM_SECONDS", "0"))
EMPTY_WAIT_TIMEOUT_SECONDS = float(os.getenv("FIVEM_PECHE_EMPTY_WAIT_TIMEOUT", "0"))
EMPTY_WAIT_POLL_SECONDS = float(os.getenv("FIVEM_PECHE_EMPTY_WAIT_POLL", "0.2"))
EMPTY_SPAM_METHOD = os.getenv("FIVEM_PECHE_EMPTY_SPAM_METHOD", "sendinput").strip().lower()

STOPPER_TEMPLATE_PATH = os.getenv(
    "FIVEM_PECHE_STOPPER_TEMPLATE",
    str(ROOT_DIR / "assets/fishing/stopper.png"),
).strip()
STOPPER_THRESHOLD = float(os.getenv("FIVEM_PECHE_STOPPER_THRESHOLD", "0.75"))

_STARTED_CLICKER = TemplateClicker(
    Path(STARTED_TEMPLATE_PATH),
    match_threshold=STARTED_THRESHOLD,
    capture_side="full",
    ctrl_click=False,
)
_CATCHED_CLICKER = TemplateClicker(
    Path(CATCHED_TEMPLATE_PATH),
    match_threshold=CATCHED_THRESHOLD,
    capture_side="full",
    ctrl_click=False,
)
_EMPTY_CLICKER = TemplateClicker(
    Path(EMPTY_TEMPLATE_PATH),
    match_threshold=EMPTY_THRESHOLD,
    capture_side="full",
    ctrl_click=False,
)
_STOPPER_CLICKER = TemplateClicker(
    Path(STOPPER_TEMPLATE_PATH),
    match_threshold=STOPPER_THRESHOLD,
    capture_side="full",
    ctrl_click=False,
)
_POISSON_CLICKER = TemplateClicker(
    Path(POISSON_TEMPLATE_PATH),
    match_threshold=POISSON_THRESHOLD,
    capture_side="left",
    ctrl_click=True,
)
_POISSON_LIGHT_CLICKER = TemplateClicker(
    Path(POISSON_LIGHT_TEMPLATE_PATH),
    match_threshold=POISSON_LIGHT_THRESHOLD,
    capture_side="left",
    ctrl_click=True,
)
_APPAT_CLICKER = TemplateClicker(
    Path(APPAT_TEMPLATE_PATH),
    match_threshold=APPAT_THRESHOLD,
    capture_side="right",
    ctrl_click=True,
)
_INVENTORY_OPEN_CLICKER = TemplateClicker(
    Path(INVENTORY_CHECK_OPEN_TEMPLATE_PATH),
    match_threshold=INVENTORY_CHECK_OPEN_THRESHOLD,
    capture_side="full",
    ctrl_click=False,
)


def _log(logger: Logger, message: str) -> None:
    if logger is not None:
        logger(message)


def _check_started(window: object, logger: Logger) -> bool:
    if not _STARTED_CLICKER.is_loaded:
        _log(logger, f"Started template not loaded: {STARTED_TEMPLATE_PATH}")
        return False
    pos = _STARTED_CLICKER.find_match(window.handle, logger)
    if pos is None:
        return False
    _log(logger, "Pecehe started")
    return True


def _wait_and_click_catched(window: object, logger: Logger) -> bool:
    if not _CATCHED_CLICKER.is_loaded:
        _log(logger, f"Catched template not loaded: {CATCHED_TEMPLATE_PATH}")
        return False
    deadline = time.time() + max(0.0, CATCHED_TIMEOUT_SECONDS)
    while time.time() <= deadline:
        pos = _CATCHED_CLICKER.find_match(window.handle, logger)
        if pos is not None:
            _CATCHED_CLICKER.click(pos, button="left")
            _log(logger, f"Clicked catched at {pos}.")
            time.sleep(CATCHED_POST_DELAY_SECONDS)
            return True
        time.sleep(max(0.01, CATCHED_POLL_SECONDS))
    return False


def _spam_left_click_at(window: object, pos: tuple[int, int], *, seconds: float, logger: Logger) -> bool:
    x, y = map(int, pos)
    win32api.SetCursorPos((x, y))
    time.sleep(0.02)
    end_time = None
    if seconds > 0:
        end_time = time.time() + seconds
    hold_seconds = max(0.0, EMPTY_SPAM_HOLD_SECONDS)
    release_seconds = max(0.0, EMPTY_SPAM_RELEASE_SECONDS)
    clicks = 0
    while True:
        if EMPTY_SPAM_METHOD == "sendinput":
            _sendinput_left_click(hold_seconds=hold_seconds)
        else:
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            if hold_seconds:
                time.sleep(hold_seconds)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        clicks += 1
        if _STOPPER_CLICKER.is_loaded:
            stopper_pos = _STOPPER_CLICKER.find_match(window.handle, logger)
            if stopper_pos is not None:
                _log(logger, f"Stopper found at {stopper_pos}.")
                return True
        if release_seconds:
            time.sleep(release_seconds)
        if _STOPPER_CLICKER.is_loaded:
            stopper_pos = _STOPPER_CLICKER.find_match(window.handle, logger)
            if stopper_pos is not None:
                _log(logger, f"Stopper found at {stopper_pos}.")
                return True
        if end_time is not None and time.time() >= end_time:
            return False
    return False
    # Best-effort debug; logger not available here.
    if clicks == 0:
        pass


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("mi", _MOUSEINPUT)]


class _INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("union", _INPUTUNION)]


def _sendinput_left_click(*, hold_seconds: float = 0.0) -> None:
    extra = ctypes.c_ulong(0)
    down = _INPUT(
        type=0,  # INPUT_MOUSE
        union=_INPUTUNION(
            mi=_MOUSEINPUT(
                dx=0,
                dy=0,
                mouseData=0,
                dwFlags=win32con.MOUSEEVENTF_LEFTDOWN,
                time=0,
                dwExtraInfo=ctypes.pointer(extra),
            )
        ),
    )
    up = _INPUT(
        type=0,
        union=_INPUTUNION(
            mi=_MOUSEINPUT(
                dx=0,
                dy=0,
                mouseData=0,
                dwFlags=win32con.MOUSEEVENTF_LEFTUP,
                time=0,
                dwExtraInfo=ctypes.pointer(extra),
            )
        ),
    )
    inputs = (_INPUT * 1)(down)
    ctypes.windll.user32.SendInput(1, inputs, ctypes.sizeof(_INPUT))
    if hold_seconds:
        time.sleep(hold_seconds)
    inputs = (_INPUT * 1)(up)
    ctypes.windll.user32.SendInput(1, inputs, ctypes.sizeof(_INPUT))


def _wait_for_empty_and_spam(window: object, logger: Logger) -> bool:
    if not _EMPTY_CLICKER.is_loaded:
        _log(logger, f"Empty-circle template not loaded: {EMPTY_TEMPLATE_PATH}")
        return False
    if not _STOPPER_CLICKER.is_loaded:
        _log(logger, f"Stopper template not loaded: {STOPPER_TEMPLATE_PATH}")
    _log(logger, "Waiting for empty-circle.")
    deadline = None
    if EMPTY_WAIT_TIMEOUT_SECONDS > 0:
        deadline = time.time() + EMPTY_WAIT_TIMEOUT_SECONDS
    while True:
        pos = _EMPTY_CLICKER.find_match(window.handle, logger)
        if pos is not None:
            _log(logger, f"Empty-circle found at {pos}. Spamming clicks.")
            stopper_found = _spam_left_click_at(window, pos, seconds=EMPTY_SPAM_SECONDS, logger=logger)
            if stopper_found:
                _log(logger, "Stopper found. Ending sequence.")
                return True
            _log(logger, "Stopped spamming before stopper was found.")
            return False
        if deadline is not None and time.time() >= deadline:
            _log(logger, "Empty-circle not found before timeout.")
            return False
        time.sleep(max(0.01, EMPTY_WAIT_POLL_SECONDS))


def _find_with_timeout(
    clicker: TemplateClicker,
    window: object,
    *,
    timeout_seconds: float,
    poll_seconds: float,
    logger: Logger,
) -> Optional[tuple[int, int]]:
    deadline = time.time() + max(0.0, timeout_seconds)
    while time.time() <= deadline:
        pos = clicker.find_match(window.handle, logger)
        if pos is not None:
            return pos
        time.sleep(max(0.01, poll_seconds))
    return None


def _click_poisson_match(clicker: TemplateClicker, pos: tuple[int, int], logger: Logger) -> None:
    repeat = max(1, POISSON_CTRL_CLICKS_PER_MATCH)
    x, y = map(int, pos)
    move_px = POISSON_MOVE_AFTER_CLICK_PIXELS
    for index in range(repeat):
        clicker.click(pos, button="left")
        if move_px == 0:
            continue
        offset = move_px if index % 2 == 0 else -move_px
        win32api.SetCursorPos((x + offset, y))
        time.sleep(max(0.0, POISSON_MOVE_AFTER_CLICK_DELAY_SECONDS))
    if repeat > 1:
        _log(logger, f"Poisson ctrl-clicked {repeat}x at {pos}.")


def _run_inventory_sequence(window: object, logger: Logger) -> None:
    if not press_tab(logger):
        _log(logger, "Failed to open inventory.")
        return
    time.sleep(INVENTORY_OPEN_DELAY_SECONDS)
    time.sleep(max(0.0, INVENTORY_INTERACTION_DELAY_SECONDS))

    if not _POISSON_CLICKER.is_loaded and not _POISSON_LIGHT_CLICKER.is_loaded:
        _log(
            logger,
            (
                "Poisson templates not loaded: "
                f"{POISSON_TEMPLATE_PATH} / {POISSON_LIGHT_TEMPLATE_PATH}"
            ),
        )
    else:
        clicks = 0
        while clicks < max(1, POISSON_MAX_CLICKS):
            pos = None
            clicker = None

            if _POISSON_CLICKER.is_loaded:
                pos = _find_with_timeout(
                    _POISSON_CLICKER,
                    window,
                    timeout_seconds=POISSON_FIND_TIMEOUT_SECONDS,
                    poll_seconds=POISSON_FIND_POLL_SECONDS,
                    logger=logger,
                )
                if pos is not None:
                    clicker = _POISSON_CLICKER

            if pos is None and _POISSON_LIGHT_CLICKER.is_loaded:
                pos = _find_with_timeout(
                    _POISSON_LIGHT_CLICKER,
                    window,
                    timeout_seconds=POISSON_FIND_TIMEOUT_SECONDS,
                    poll_seconds=POISSON_FIND_POLL_SECONDS,
                    logger=logger,
                )
                if pos is not None:
                    clicker = _POISSON_LIGHT_CLICKER
                    _log(logger, f"Poisson fallback matched (light) at {pos}.")

            if pos is None:
                if clicks == 0:
                    _log(logger, f"Poisson not found on left side after {POISSON_FIND_TIMEOUT_SECONDS:.1f}s.")
                else:
                    _log(logger, "No more poisson on left side.")
                break
            if clicker is None:
                break
            _click_poisson_match(clicker, pos, logger)
            clicks += 1
            time.sleep(max(POISSON_CLICK_DELAY_SECONDS, INVENTORY_INTERACTION_DELAY_SECONDS))
        if clicks >= POISSON_MAX_CLICKS:
            _log(logger, f"Poisson click limit reached ({POISSON_MAX_CLICKS}).")

    if not _APPAT_CLICKER.is_loaded:
        _log(logger, f"Appat template not loaded: {APPAT_TEMPLATE_PATH}")
    else:
        pos = _find_with_timeout(
            _APPAT_CLICKER,
            window,
            timeout_seconds=APPAT_FIND_TIMEOUT_SECONDS,
            poll_seconds=APPAT_FIND_POLL_SECONDS,
            logger=logger,
        )
        if pos is None:
            _log(logger, f"Appat not found on right side after {APPAT_FIND_TIMEOUT_SECONDS:.1f}s.")
        else:
            _APPAT_CLICKER.click(pos, button="left")
            _log(logger, f"Ctrl-clicked appat at {pos}.")
            time.sleep(max(0.0, INVENTORY_INTERACTION_DELAY_SECONDS))

    if press_tab(logger):
        time.sleep(max(INVENTORY_CLOSE_DELAY_SECONDS, INVENTORY_INTERACTION_DELAY_SECONDS))


def _close_inventory_if_open(window: object, logger: Logger) -> bool:
    if not _INVENTORY_OPEN_CLICKER.is_loaded:
        _log(logger, f"Inventory-open template not loaded: {INVENTORY_CHECK_OPEN_TEMPLATE_PATH}")
        return False

    deadline = time.time() + max(0.0, INVENTORY_CHECK_TIMEOUT_SECONDS)
    while time.time() <= deadline:
        pos = _INVENTORY_OPEN_CLICKER.find_match(window.handle, logger)
        if pos is None:
            time.sleep(max(0.01, INVENTORY_CHECK_POLL_SECONDS))
            continue

        _log(logger, f"Inventory detected open at {pos}; closing with Tab.")
        if not press_tab(logger):
            _log(logger, "Failed to close open inventory.")
            return True

        close_delay = max(
            INVENTORY_CLOSE_DELAY_SECONDS,
            INVENTORY_OPEN_POST_ACTION_DELAY_SECONDS,
        )
        time.sleep(close_delay)
        _log(logger, f"Inventory closed. Applied post-action delay: {close_delay:.2f}s.")
        return True

    return False


def _peche_action(window: object, logger: Logger) -> bool:
    global _SEQUENCE_COUNT
    if not focus_window(window, logger):
        return False
    _close_inventory_if_open(window, logger)

    if not press_c(logger, hold_seconds=C_HOLD_SECONDS):
        return False
    time.sleep(KEY_DELAY_SECONDS)

    if not press_5(logger):
        return False
    time.sleep(DELAY_BETWEEN_5_AND_4)

    if not press_4(logger):
        return False
    time.sleep(POST_4_DELAY_SECONDS)

    sequence_finished = False
    if _check_started(window, logger):
        if _wait_and_click_catched(window, logger):
            if _wait_for_empty_and_spam(window, logger):
                time.sleep(max(0.0, POST_STOPPER_DELAY_SECONDS))
                sequence_finished = True

    _log(logger, "Peche sequence complete.")
    if sequence_finished:
        _SEQUENCE_COUNT += 1
        if INVENTORY_EVERY > 0 and _SEQUENCE_COUNT % INVENTORY_EVERY == 0:
            _log(logger, f"Running inventory sequence (every {INVENTORY_EVERY}).")
            _run_inventory_sequence(window, logger)
    return True


def main() -> None:
    run_bot(
        action=_peche_action,
        interval_seconds=INTERVAL_SECONDS,
        fail_interval_seconds=FAIL_INTERVAL_SECONDS,
        title_pattern=WINDOW_TITLE_PATTERN,
        random_range=(0.0, 0.0),
    )


if __name__ == "__main__":
    main()
