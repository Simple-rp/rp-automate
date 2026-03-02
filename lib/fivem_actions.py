"""Reusable FiveM action sequences."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Optional

from pywinauto.base_wrapper import BaseWrapper

from lib.fivem_window import focus_window
from lib.keystrokes import (
    press_alt_tab,
    press_down,
    press_e,
    press_enter,
    press_g,
    press_tab,
    press_x,
)
from lib.template_clicker import TemplateClicker

Logger = Optional[Callable[[str], None]]
PostCycleHook = Optional[Callable[[BaseWrapper, Logger], None]]


@dataclass
class ActionSettings:
    open_trunk: bool = True
    alt_tab_after_action: bool = False
    send_sale_confirmation: bool = False
    x_delay_seconds: float = 0.2
    open_trunk_delay_seconds: float = 0.5
    pre_find_delay_seconds: float = 0.75
    post_find_delay_seconds: float = 0.75
    post_tab_delay_seconds: float = 0.5
    post_e_delay_seconds: float = 0.4
    post_down_delay_seconds: float = 0.5
    close_trunk_delay_seconds: float = 1.0
    alt_tab_delay_seconds: float = 0.2


def run_inventory_cycle(
    window: BaseWrapper,
    clicker: TemplateClicker,
    settings: ActionSettings,
    logger: Logger = None,
    post_cycle_hook: PostCycleHook = None,
) -> bool:
    """Focus FiveM, open inventory, click item, and close with optional extras."""
    if not focus_window(window, logger):
        return False

    press_x(logger)
    time.sleep(settings.x_delay_seconds)

    if not settings.open_trunk:
        press_g(logger)
        time.sleep(settings.open_trunk_delay_seconds)

    press_tab(logger)
    time.sleep(settings.pre_find_delay_seconds)

    item_found = clicker.find_and_click(window.handle, logger)

    time.sleep(settings.post_find_delay_seconds)
    press_tab(logger)
    time.sleep(settings.post_tab_delay_seconds)

    if post_cycle_hook is not None:
        post_cycle_hook(window, logger)

    press_e(logger)

    if settings.send_sale_confirmation:
        time.sleep(settings.post_e_delay_seconds)
        press_down(logger)
        time.sleep(settings.post_down_delay_seconds)
        press_enter(logger)

    if not settings.open_trunk:
        time.sleep(settings.close_trunk_delay_seconds)
        press_g(logger)

    if settings.alt_tab_after_action:
        time.sleep(settings.alt_tab_delay_seconds)
        press_alt_tab(logger)

    return item_found
