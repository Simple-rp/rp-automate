"""Food/water gauge checks and consumable usage."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from pywinauto.base_wrapper import BaseWrapper

from lib.keystrokes import press_tab
from lib.template_clicker import TemplateClicker

Logger = Optional[Callable[[str], None]]


def _log(logger: Logger, message: str) -> None:
    if logger is not None:
        logger(message)


@dataclass
class EatDrinkChecker:
    food_gauge_path: Path
    water_gauge_path: Path
    use_template_path: Path
    items_root_dir: Path
    match_threshold: float = 0.75
    gauge_capture_side: str = "full"
    item_capture_side: str = "full"
    open_inventory_delay_seconds: float = 0.45
    open_context_delay_seconds: float = 0.25
    use_click_delay_seconds: float = 15
    consume_step_delay_seconds: float = 0.25
    close_inventory_delay_seconds: float = 0.20
    enabled: bool = True
    _use_clicker: Optional[TemplateClicker] = field(init=False, default=None, repr=False)
    _food_gauge_clicker: Optional[TemplateClicker] = field(init=False, default=None, repr=False)
    _water_gauge_clicker: Optional[TemplateClicker] = field(init=False, default=None, repr=False)
    _food_item_clickers: list[TemplateClicker] = field(init=False, default_factory=list, repr=False)
    _drink_item_clickers: list[TemplateClicker] = field(init=False, default_factory=list, repr=False)
    _food_enabled: bool = field(init=False, default=False, repr=False)
    _water_enabled: bool = field(init=False, default=False, repr=False)

    def initialize(self, logger: Logger = None) -> None:
        """Load templates and validate image folders before bot starts."""
        if not self.enabled:
            _log(logger, "Eat/drink checks are disabled.")
            return

        self._use_clicker = self._build_use_clicker(self.use_template_path, logger)
        self._food_gauge_clicker = self._build_gauge_clicker(self.food_gauge_path, "food", logger)
        self._water_gauge_clicker = self._build_gauge_clicker(self.water_gauge_path, "water", logger)
        item_files = self._discover_item_files(self.items_root_dir)
        food_files = [path for path in item_files if self._is_food_item(path)]
        drink_files = [path for path in item_files if self._is_drink_item(path)]

        self._food_item_clickers = self._build_item_clickers(food_files, "food", logger)
        self._drink_item_clickers = self._build_item_clickers(drink_files, "drink", logger)

        if self._use_clicker is None:
            self._food_enabled = False
            self._water_enabled = False
            _log(logger, "Eat/drink checks disabled (missing use.png template).")
            return

        self._food_enabled = self._food_gauge_clicker is not None and bool(self._food_item_clickers)
        self._water_enabled = self._water_gauge_clicker is not None and bool(self._drink_item_clickers)

        if self._food_enabled:
            _log(logger, f"Food check enabled with {len(self._food_item_clickers)} item template(s).")
        else:
            _log(logger, "Food check disabled (missing gauge or food item templates).")

        if self._water_enabled:
            _log(logger, f"Water check enabled with {len(self._drink_item_clickers)} item template(s).")
        else:
            _log(logger, "Water check disabled (missing gauge or drink item templates).")

    def check_and_consume(self, window: BaseWrapper, logger: Logger = None) -> bool:
        """If any gauge is low, open inventory and consume one matching item."""
        if not self.enabled:
            return False
        if not self._food_enabled and not self._water_enabled:
            return False

        hwnd = window.handle
        need_food = self._food_enabled and self._food_gauge_clicker is not None and (
            self._food_gauge_clicker.find_match(hwnd) is not None
        )
        need_water = self._water_enabled and self._water_gauge_clicker is not None and (
            self._water_gauge_clicker.find_match(hwnd) is not None
        )

        if not need_food and not need_water:
            return False

        if need_food:
            _log(logger, "Food gauge is low; trying to eat.")
        if need_water:
            _log(logger, "Water gauge is low; trying to drink.")

        press_tab(logger)
        time.sleep(self.open_inventory_delay_seconds)

        consumed_any = False
        if need_food:
            consumed_any = self._consume_from_templates(hwnd, self._food_item_clickers, "food", logger) or consumed_any
        if need_water:
            consumed_any = self._consume_from_templates(hwnd, self._drink_item_clickers, "drink", logger) or consumed_any

        time.sleep(self.close_inventory_delay_seconds)
        press_tab(logger)
        return consumed_any

    def _build_use_clicker(self, use_path: Path, logger: Logger) -> Optional[TemplateClicker]:
        if not use_path.exists():
            _log(logger, f"Use template not found: {use_path}")
            return None
        clicker = TemplateClicker(
            template_path=use_path,
            match_threshold=self.match_threshold,
            capture_side=self.item_capture_side,
            ctrl_click=False,
        )
        if not clicker.is_loaded:
            _log(logger, f"Use template could not be loaded: {use_path}")
            return None
        return clicker

    def _build_gauge_clicker(self, gauge_path: Path, label: str, logger: Logger) -> Optional[TemplateClicker]:
        if not gauge_path.exists():
            _log(logger, f"{label.capitalize()} gauge template not found: {gauge_path}")
            return None
        clicker = TemplateClicker(
            template_path=gauge_path,
            match_threshold=self.match_threshold,
            capture_side=self.gauge_capture_side,
            ctrl_click=False,
        )
        if not clicker.is_loaded:
            _log(logger, f"{label.capitalize()} gauge template could not be loaded: {gauge_path}")
            return None
        return clicker

    def _build_item_clickers(self, files: list[Path], label: str, logger: Logger) -> list[TemplateClicker]:
        if not files:
            _log(logger, f"No {label} item images found under: {self.items_root_dir}")
            return []

        clickers: list[TemplateClicker] = []
        for image_path in files:
            clicker = TemplateClicker(
                template_path=image_path,
                match_threshold=self.match_threshold,
                capture_side=self.item_capture_side,
                ctrl_click=False,
            )
            if clicker.is_loaded:
                clickers.append(clicker)
        if not clickers:
            _log(logger, f"{label.capitalize()} item images exist but none could be loaded under: {self.items_root_dir}")
        return clickers

    @staticmethod
    def _discover_item_files(root_dir: Path) -> list[Path]:
        if not root_dir.exists() or not root_dir.is_dir():
            return []
        return sorted(
            path
            for path in root_dir.rglob("*.png")
            if path.is_file() and "jauge" not in {part.lower() for part in path.parts}
        )

    @staticmethod
    def _is_food_item(path: Path) -> bool:
        stem = path.stem.lower()
        parts = {part.lower() for part in path.parts}
        return stem.startswith("food-") or "food" in parts

    @staticmethod
    def _is_drink_item(path: Path) -> bool:
        stem = path.stem.lower()
        parts = {part.lower() for part in path.parts}
        return stem.startswith("drink-") or "drink" in parts

    def _consume_from_templates(
        self,
        hwnd: int,
        clickers: list[TemplateClicker],
        kind: str,
        logger: Logger,
    ) -> bool:
        if self._use_clicker is None:
            return False
        for clicker in clickers:
            target = clicker.find_match(hwnd)
            if target is None:
                continue

            clicker.click(target, button="right")
            _log(logger, f"Right-clicked {kind} item '{clicker.template_path.name}'.")
            time.sleep(self.open_context_delay_seconds)

            if not self._use_clicker.find_and_click(hwnd, log_not_found=False):
                _log(logger, "Use action not found after right-click.")
                continue

            time.sleep(self.use_click_delay_seconds)
            _log(logger, f"Consumed {kind} using '{clicker.template_path.name}'.")
            return True
        _log(logger, f"No matching {kind} item found on screen.")
        return False
