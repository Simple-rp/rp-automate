"""Saumon selling bot (Diamond / Peche)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from lib.inventory_bot import run_inventory_bot
from lib.template_paths import collect_image_templates

INTERVAL_SECONDS = int(os.getenv("FIVEM_BOT_INTERVAL", "155"))
FAIL_INTERVAL_SECONDS = 10
WINDOW_TITLE_PATTERN = r".*FiveM.*"
TEMPLATE_DIR = ROOT_DIR / "assets/items/peches"
TEMPLATE_PREFIX = "saumon"
MATCH_THRESHOLD = 0.75
DEBUG = False


def main() -> None:
    template_paths = [
        template_path
        for template_path in collect_image_templates(TEMPLATE_DIR, extensions=(".png",))
        if template_path.stem.lower().startswith(TEMPLATE_PREFIX)
    ]
    if not template_paths:
        raise FileNotFoundError(f"No {TEMPLATE_PREFIX} templates found in directory: {TEMPLATE_DIR}")

    run_inventory_bot(
        interval_seconds=INTERVAL_SECONDS,
        fail_interval_seconds=FAIL_INTERVAL_SECONDS,
        template_path=template_paths,
        capture_side="right",
        match_threshold=MATCH_THRESHOLD,
        title_pattern=WINDOW_TITLE_PATTERN,
        debug=DEBUG,
        open_trunk=True,
        alt_tab_after_action=True,
        send_sale_confirmation=False,
        check_eat_drink=False,
    )


if __name__ == "__main__":
    main()
