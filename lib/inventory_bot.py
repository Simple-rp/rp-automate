"""High-level inventory bot template used by all scripts."""

from __future__ import annotations

from pathlib import Path

from lib.bot_runner import build_logger, run_bot
from lib.eat_drink import EatDrinkChecker
from lib.fivem_actions import ActionSettings, run_inventory_cycle
from lib.template_clicker import TemplateClicker


def _discover_project_root(template_path: Path) -> Path:
    resolved = template_path.resolve()
    for candidate in [resolved.parent, *resolved.parents]:
        if (candidate / "assets").exists() and (candidate / "lib").exists():
            return candidate
    return Path.cwd()


def run_inventory_bot(
    *,
    interval_seconds: int,
    fail_interval_seconds: int,
    template_path: Path,
    capture_side: str,
    match_threshold: float = 0.75,
    debug: bool = False,
    title_pattern: str = r".*FiveM.*",
    open_trunk: bool = True,
    alt_tab_after_action: bool = False,
    send_sale_confirmation: bool = False,
    check_eat_drink: bool = True,
) -> None:
    """Run a configured inventory bot with shared fail/random behavior."""
    clicker = TemplateClicker(
        template_path=template_path,
        match_threshold=match_threshold,
        capture_side=capture_side,
    )
    settings = ActionSettings(
        open_trunk=open_trunk,
        alt_tab_after_action=alt_tab_after_action,
        send_sale_confirmation=send_sale_confirmation,
    )
    project_root = _discover_project_root(template_path)
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
        debug_action=lambda window, logger: clicker.find_and_click(window.handle, logger),
        interval_seconds=interval_seconds,
        fail_interval_seconds=fail_interval_seconds,
        title_pattern=title_pattern,
        debug=debug,
    )
