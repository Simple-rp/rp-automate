"""Entry point for the saumon boat harvesting bot."""

from __future__ import annotations

import runpy
from pathlib import Path


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).with_name("recolte-pecheur.py")), run_name="__main__")
