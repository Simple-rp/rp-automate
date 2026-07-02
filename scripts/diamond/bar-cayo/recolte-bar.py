"""Bar harvesting bot (Diamond / Bar Cayo)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from lib.inventory_bot import run_inventory_bot
from lib.template_paths import collect_image_templates

INTERVAL_SECONDS = int(os.getenv("FIVEM_BOT_INTERVAL", str(15*16+5)))
FAIL_INTERVAL_SECONDS = 18
WINDOW_TITLE_PATTERN = r".*FiveM.*"
TEMPLATE_DIR = ROOT_DIR / "assets/items/banane"
MATCH_THRESHOLD = 0.75
DEBUG = False
PRE_FIND_DELAY_SECONDS = 1.2
FIND_TIMEOUT_SECONDS = 2.5
PER_TEMPLATE_TIMEOUT_SECONDS = 0.2  
PER_TEMPLATE_POLL_SECONDS = 0.06


def main() -> None:
    template_paths = collect_image_templates(TEMPLATE_DIR, extensions=(".png",))

    run_inventory_bot(
        interval_seconds=INTERVAL_SECONDS,
        fail_interval_seconds=FAIL_INTERVAL_SECONDS,
        template_path=template_paths,
        capture_side="left",
        match_threshold=MATCH_THRESHOLD,
        title_pattern=WINDOW_TITLE_PATTERN,
        debug=DEBUG,
        open_trunk=True,
        alt_tab_after_action=True,
        send_sale_confirmation=True,
        check_eat_drink=False,
        pre_find_delay_seconds=PRE_FIND_DELAY_SECONDS,
        find_timeout_seconds=FIND_TIMEOUT_SECONDS,
        per_template_timeout_seconds=PER_TEMPLATE_TIMEOUT_SECONDS,
        per_template_poll_seconds=PER_TEMPLATE_POLL_SECONDS,
    )


if __name__ == "__main__":
    main()
