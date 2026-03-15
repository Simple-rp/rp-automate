"""List open windows with basic metadata to help match title patterns."""

from __future__ import annotations

import win32gui
import win32process


def safe_call(func, fallback):
    try:
        return func()
    except Exception:
        return fallback


def main() -> None:
    hwnds: list[int] = []

    def _collect(hwnd, _):
        hwnds.append(hwnd)
        return True

    win32gui.EnumWindows(_collect, None)

    if not hwnds:
        print("No windows found.")
        return

    for index, hwnd in enumerate(hwnds, start=1):
        title = safe_call(lambda: win32gui.GetWindowText(hwnd), "<unknown>")
        handle = hwnd
        visible = safe_call(lambda: win32gui.IsWindowVisible(hwnd), False)
        enabled = safe_call(lambda: win32gui.IsWindowEnabled(hwnd), False)
        class_name = safe_call(lambda: win32gui.GetClassName(hwnd), "n/a")
        process_id = safe_call(lambda: win32process.GetWindowThreadProcessId(hwnd)[1], "n/a")
        print(
            f"{index:3d}. title='{title}' | handle={handle} | "
            f"visible={visible} | enabled={enabled} | class={class_name} | pid={process_id}"
        )


if __name__ == "__main__":
    main()
