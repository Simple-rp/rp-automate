"""Common bot runtime loop with failover and randomized intervals."""

from __future__ import annotations

from array import array
import sys
try:
    import audioop
except ImportError:  # pragma: no cover - missing in Python 3.13+
    audioop = None
import hashlib
import os
import random
import tempfile
import time
import wave
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from lib.fivem_window import find_fivem_window

Logger = Callable[[str], None]
WindowAction = Callable[[object, Logger], bool]

try:
    import winsound
except ImportError:  # pragma: no cover - Windows only
    winsound = None


def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def build_logger() -> Logger:
    def log(message: str) -> None:
        print(f"[{timestamp()}] {message}")

    return log


def _sound_enabled() -> bool:
    value = os.getenv("FIVEM_BOT_ITERATION_SOUND", "1").strip().lower()
    return value not in {"0", "false", "no", "off"}


def _resolve_sound() -> tuple[str, str | None]:
    value = os.getenv("FIVEM_BOT_SOUND", "").strip()
    if not value:
        default_path = Path(__file__).resolve().parents[1] / "assets/sound/beep.wav"
        if default_path.exists():
            return ("file", str(default_path))
        return ("beep", None)

    lower = value.lower()
    alias_map = {
        "notification": "SystemNotification",
        "asterisk": "SystemAsterisk",
        "exclamation": "SystemExclamation",
        "hand": "SystemHand",
        "question": "SystemQuestion",
        "exit": "SystemExit",
        "default": "SystemDefault",
    }
    if lower in {"beep", "tone"}:
        return ("beep", None)
    if lower in alias_map:
        return ("alias", alias_map[lower])
    if os.path.exists(value):
        return ("file", value)
    return ("alias", value)


def _sound_volume() -> float:
    value = os.getenv("FIVEM_BOT_SOUND_VOLUME", "").strip()
    if not value:
        return 0.35
    try:
        volume = float(value)
    except ValueError:
        return 0.35
    return max(0.0, min(1.0, volume))


def _scale_pcm(frames: bytes, sample_width: int, volume: float) -> bytes:
    if volume >= 0.99:
        return frames
    if sample_width == 1:
        # Unsigned 8-bit PCM centered at 128.
        out = bytearray(len(frames))
        for i, b in enumerate(frames):
            sample = b - 128
            scaled = int(round(sample * volume))
            if scaled > 127:
                scaled = 127
            elif scaled < -128:
                scaled = -128
            out[i] = (scaled + 128) & 0xFF
        return bytes(out)
    if sample_width == 2:
        arr = array("h")
        arr.frombytes(frames)
        if sys.byteorder != "little":
            arr.byteswap()
        for i, sample in enumerate(arr):
            scaled = int(round(sample * volume))
            if scaled > 32767:
                scaled = 32767
            elif scaled < -32768:
                scaled = -32768
            arr[i] = scaled
        if sys.byteorder != "little":
            arr.byteswap()
        return arr.tobytes()
    if sample_width == 3:
        out = bytearray(len(frames))
        for i in range(0, len(frames), 3):
            chunk = frames[i : i + 3]
            if len(chunk) < 3:
                break
            sample = int.from_bytes(chunk, "little", signed=True)
            scaled = int(round(sample * volume))
            if scaled > 8388607:
                scaled = 8388607
            elif scaled < -8388608:
                scaled = -8388608
            out[i : i + 3] = int(scaled).to_bytes(3, "little", signed=True)
        return bytes(out)
    if sample_width == 4:
        arr = array("i")
        arr.frombytes(frames)
        if sys.byteorder != "little":
            arr.byteswap()
        for i, sample in enumerate(arr):
            scaled = int(round(sample * volume))
            if scaled > 2147483647:
                scaled = 2147483647
            elif scaled < -2147483648:
                scaled = -2147483648
            arr[i] = scaled
        if sys.byteorder != "little":
            arr.byteswap()
        return arr.tobytes()
    return frames


def _prepare_sound_file(sound_path: str, volume: float) -> str | None:
    if volume >= 0.99:
        return sound_path
    if not sound_path.lower().endswith(".wav"):
        return sound_path

    try:
        mtime = os.path.getmtime(sound_path)
        cache_key = f"{sound_path}:{mtime}:{volume:.3f}".encode("utf-8")
        cache_name = hashlib.md5(cache_key).hexdigest()
        cache_dir = Path(tempfile.gettempdir()) / "fivem_bot_sounds"
        cache_dir.mkdir(parents=True, exist_ok=True)
        output_path = cache_dir / f"{Path(sound_path).stem}_{cache_name}.wav"
        if output_path.exists():
            return str(output_path)

        with wave.open(sound_path, "rb") as reader:
            params = reader.getparams()
            sample_width = reader.getsampwidth()
            with wave.open(str(output_path), "wb") as writer:
                writer.setparams(params)
                while True:
                    frames = reader.readframes(4096)
                    if not frames:
                        break
                    if audioop is not None:
                        scaled = audioop.mul(frames, sample_width, volume)
                    else:
                        scaled = _scale_pcm(frames, sample_width, volume)
                    writer.writeframes(scaled)
        return str(output_path)
    except Exception:
        return sound_path


def _play_iteration_sound() -> None:
    if winsound is None or not _sound_enabled():
        return
    kind, sound = _resolve_sound()
    try:
        if kind == "file" and sound:
            volume = _sound_volume()
            if volume <= 0.0:
                return
            sound_path = _prepare_sound_file(sound, volume)
            if not sound_path:
                return
            winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            return
        if kind == "alias" and sound:
            winsound.PlaySound(sound, winsound.SND_ALIAS | winsound.SND_ASYNC)
            return
        winsound.Beep(440, 25)
    except Exception:
        pass


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
            _play_iteration_sound()
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
