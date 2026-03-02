"""Common bot runtime loop with failover and randomized intervals."""

from __future__ import annotations

import random
import time
from datetime import datetime
from typing import Callable, Optional

from pywinauto.base_wrapper import BaseWrapper

from lib.fivem_window import find_fivem_window

Logger = Callable[[str], None]
WindowAction = Callable[[BaseWrapper, Logger], bool]


def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def build_logger() -> Logger:
    def log(message: str) -> None:
        print(f"[{timestamp()}] {message}")

    return log


def run_bot(
    action: WindowAction,
    interval_seconds: int,
    *,
    fail_interval_seconds: int = 10,
    max_failures: int = 5,
    random_range: tuple[float, float] = (-2.0, 4.0),
    title_pattern: str = r".*FiveM.*",
    debug: bool = False,
    debug_action: Optional[WindowAction] = None,
) -> None:
    """Run the standard bot loop."""
    log = build_logger()
    active_debug_action = debug_action if debug_action is not None else action

    log(
        f"FiveM bot started. Interval: {interval_seconds} seconds. "
        f"Looking for window title matching: '{title_pattern}'."
    )

    iteration = 0
    fail_count = 0

    while True:
        window = find_fivem_window(title_pattern, log)
        iteration_success = False

        if window and debug:
            log(f"Debug: window found: {window is not None}")
            iteration_success = active_debug_action(window, log)
        elif window:
            log(f"Iteration {iteration} starting....")
            iteration_success = action(window, log)
            iteration += 1
        else:
            log("FiveM window not found.")

        if iteration_success:
            fail_count = 0
        else:
            fail_count += 1
            log(f"Failure streak: {fail_count}.")
            if fail_count >= max_failures:
                log(
                    f"Reached {max_failures} consecutive failures (window missing or item not found). "
                    "Stopping bot."
                )
                break

        base_interval = interval_seconds if iteration_success else fail_interval_seconds
        random_seconds = random.uniform(*random_range)
        sleep_seconds = max(0.0, base_interval + random_seconds)
        log(f"next iteration in {sleep_seconds:.1f}s (fail_count: {fail_count}).")
        time.sleep(sleep_seconds)
