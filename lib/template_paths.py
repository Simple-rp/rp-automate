"""Helpers for discovering template image paths."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence


def collect_image_templates(
    template_dir: Path | str,
    *,
    extensions: Sequence[str] = (".png",),
) -> list[Path]:
    """Return sorted template files from a directory, validating expected inputs."""
    directory = Path(template_dir)
    if not directory.exists():
        raise FileNotFoundError(f"Template directory not found: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Template path is not a directory: {directory}")

    allowed_suffixes = {suffix.lower() for suffix in extensions}
    template_paths = sorted(
        (path for path in directory.iterdir() if path.is_file() and path.suffix.lower() in allowed_suffixes),
        key=lambda path: path.name.lower(),
    )
    if not template_paths:
        suffix_label = ", ".join(sorted(allowed_suffixes))
        raise FileNotFoundError(
            f"No template images found in directory: {directory} (extensions: {suffix_label})"
        )
    return template_paths
