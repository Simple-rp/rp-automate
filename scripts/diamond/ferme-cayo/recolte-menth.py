"""Menthe harvesting bot (Diamond / Ferme Cayo)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from lib.inventory_bot import run_inventory_bot

INTERVAL_SECONDS = int(os.getenv("FIVEM_BOT_INTERVAL", "155"))
FAIL_INTERVAL_SECONDS = 18
WINDOW_TITLE_PATTERN = r".*FiveM.*"
TEMPLATE_PATH = ROOT_DIR / "assets/items/menthe.png"
MATCH_THRESHOLD = 0.75
DEBUG = False


def main() -> None:
    run_inventory_bot(
        interval_seconds=INTERVAL_SECONDS,
        fail_interval_seconds=FAIL_INTERVAL_SECONDS,
        template_path=TEMPLATE_PATH,
        capture_side="left",
        match_threshold=MATCH_THRESHOLD,
        title_pattern=WINDOW_TITLE_PATTERN,
        debug=DEBUG,
        open_trunk=True,
        alt_tab_after_action=True,
        send_sale_confirmation=True,
        check_eat_drink = False,
    )


if __name__ == "__main__":
    main()
