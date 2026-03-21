"""High-level inventory bot template used by all scripts."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Sequence

from lib.bot_runner import build_logger, run_bot
from lib.eat_drink import EatDrinkChecker
from lib.fivem_actions import ActionSettings, run_inventory_cycle
from lib.fivem_window import focus_window
from lib.keystrokes import press_tab
from lib.template_clicker import Logger, TemplateClicker


def _normalize_template_paths(template_path: Path | str | Sequence[Path | str]) -> list[Path]:
    if isinstance(template_path, (Path, str)):
        return [Path(template_path)]

    paths = [Path(path) for path in template_path]
    if not paths:
        raise ValueError("template_path must contain at least one path.")
    return paths


def _discover_project_root(template_paths: Sequence[Path]) -> Path:
    for template_path in template_paths:
        resolved = template_path.resolve()
        for candidate in [resolved.parent, *resolved.parents]:
            if (candidate / "assets").exists() and (candidate / "lib").exists():
                return candidate
    return Path.cwd()


class _MultiTemplateClicker:
    def __init__(
        self,
        template_paths: Sequence[Path],
        *,
        match_threshold: float,
        capture_side: str,
    ) -> None:
        self._clickers = [
            TemplateClicker(
                template_path=template_path,
                match_threshold=match_threshold,
                capture_side=capture_side,
            )
            for template_path in template_paths
        ]
        self._template_paths = [str(path) for path in template_paths]

    def find_and_click(
        self,
        hwnd: int,
        logger: Logger = None,
        *,
        log_not_found: bool = True,
        button: str = "left",
        per_template_timeout_seconds: float = 0.0,
        per_template_poll_seconds: float = 0.05,
    ) -> bool:
        at_least_one_template_loaded = False
        for clicker in self._clickers:
            if not clicker.is_loaded:
                continue
            at_least_one_template_loaded = True
            template_deadline = time.time() + max(0.0, per_template_timeout_seconds)
            while True:
                if clicker.find_and_click(hwnd, logger, log_not_found=False, button=button):
                    return True
                if time.time() >= template_deadline:
                    break
                time.sleep(max(0.01, per_template_poll_seconds))

        if not log_not_found:
            return False
        if logger is None:
            return False
        if at_least_one_template_loaded:
            logger("Item not found on screen.")
        else:
            logger(f"Template image not loaded: {', '.join(self._template_paths)}")
        return False


def _debug_find_action(
    window: object,
    logger: Logger,
    clicker: _MultiTemplateClicker,
    settings: ActionSettings,
) -> bool:
    if not focus_window(window, logger):
        return False

    press_tab(logger)
    time.sleep(settings.pre_find_delay_seconds)

    deadline = time.time() + max(0.0, settings.find_timeout_seconds)
    item_found = False
    while True:
        item_found = clicker.find_and_click(
            window.handle,
            logger,
            log_not_found=False,
            per_template_timeout_seconds=settings.per_template_timeout_seconds,
            per_template_poll_seconds=settings.per_template_poll_seconds,
        )
        if item_found:
            break
        if time.time() >= deadline:
            if logger is not None:
                logger(f"Debug: item not found after {settings.find_timeout_seconds:.1f}s.")
            break
        time.sleep(max(0.01, settings.find_poll_seconds))

    time.sleep(settings.post_find_delay_seconds)
    press_tab(logger)
    time.sleep(settings.post_tab_delay_seconds)
    return item_found


def run_inventory_bot(
    *,
    interval_seconds: int,
    fail_interval_seconds: int,
    template_path: Path | str | Sequence[Path | str],
    capture_side: str,
    match_threshold: float = 0.75,
    debug: bool = False,
    title_pattern: str = r".*FiveM.*",
    open_trunk: bool = True,
    alt_tab_after_action: bool = False,
    send_sale_confirmation: bool = False,
    check_eat_drink: bool = True,
    pre_find_delay_seconds: float = 0.75,
    find_timeout_seconds: float = 2.0,
    find_poll_seconds: float = 0.2,
    per_template_timeout_seconds: float = 0.0,
    per_template_poll_seconds: float = 0.05,
) -> None:
    """Run a configured inventory bot with shared fail/random behavior."""
    template_paths = _normalize_template_paths(template_path)
    clicker = _MultiTemplateClicker(
        template_paths,
        match_threshold=match_threshold,
        capture_side=capture_side,
    )
    settings = ActionSettings(
        open_trunk=open_trunk,
        alt_tab_after_action=alt_tab_after_action,
        send_sale_confirmation=send_sale_confirmation,
        pre_find_delay_seconds=pre_find_delay_seconds,
        find_timeout_seconds=find_timeout_seconds,
        find_poll_seconds=find_poll_seconds,
        per_template_timeout_seconds=per_template_timeout_seconds,
        per_template_poll_seconds=per_template_poll_seconds,
    )
    project_root = _discover_project_root(template_paths)
    eat_assets_root = project_root / "assets/eating"
    eat_drink_checker = EatDrinkChecker(
        food_gauge_path=eat_assets_root / "jauge/food.png",
        water_gauge_path=eat_assets_root / "jauge/water.png",
        use_template_path=eat_assets_root / "jauge/use.png",
        items_root_dir=eat_assets_root,
        match_threshold=match_threshold,
        enabled=check_eat_drink,
    )
    eat_drink_checker.initialize(build_logger())

    run_bot(
        action=lambda window, logger: run_inventory_cycle(
            window,
            clicker,
            settings,
            logger,
            post_cycle_hook=lambda current_window, current_logger: eat_drink_checker.check_and_consume(
                current_window,
                current_logger,
            ),
        ),
        debug_action=lambda window, logger: _debug_find_action(window, logger, clicker, settings),
        interval_seconds=interval_seconds,
        fail_interval_seconds=fail_interval_seconds,
        title_pattern=title_pattern,
        debug=debug,
    )
