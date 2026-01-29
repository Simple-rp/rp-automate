"""
Simple FiveM helper that every 2 minutes brings the FiveM window to the front
and sends the "G" key. Stop with Ctrl+C. Customize interval with env var
FIVEM_BOT_INTERVAL (seconds).
"""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import cv2
import mss
import numpy as np
from pywinauto import Desktop
from pywinauto.base_wrapper import BaseWrapper
from pywinauto.keyboard import send_keys
import win32con
import win32gui
import ctypes
import win32api


INTERVAL_SECONDS = int(os.getenv("FIVEM_BOT_INTERVAL", "20"))
WINDOW_TITLE_PATTERN = r".*FiveM.*"
TEMPLATE_PATH = Path("items/ble.png")
MATCH_THRESHOLD = 0.75
DEBUG = False

# Load template once to avoid disk reads each loop.
TEMPLATE_IMAGE = None
if TEMPLATE_PATH.exists():
    _img = cv2.imread(str(TEMPLATE_PATH), cv2.IMREAD_UNCHANGED)
    if _img is not None:
        TEMPLATE_IMAGE = cv2.cvtColor(_img, cv2.COLOR_BGRA2BGR) if _img.shape[2] == 4 else _img
        TEMPLATE_W, TEMPLATE_H = TEMPLATE_IMAGE.shape[1], TEMPLATE_IMAGE.shape[0]
    else:
        print(f"[{datetime.now()}] Failed to load template at {TEMPLATE_PATH}")
else:
    print(f"[{datetime.now()}] Template not found at {TEMPLATE_PATH}")


def find_fivem_window() -> Optional[BaseWrapper]:
    """Return the first visible FiveM window if found."""
    try:
        windows = Desktop(backend="uia").windows(
            title_re=WINDOW_TITLE_PATTERN,
            visible_only=True,
            enabled_only=True,
        )
        if windows:
            print(f"[{timestamp()}] Found window: '{windows[0].window_text()}'")
            return windows[0]
        return None
    except Exception as exc:  # pragma: no cover - defensive logging
        print(f"[{timestamp()}] Failed to enumerate windows: {exc}")
        return None


def work(window: BaseWrapper) -> None:
    """Focus window, send X then G, Tab, click item, then E."""
    if focus_fivem_window(window):
        send_x_key()
        time.sleep(0.2)
        send_g_key()
        time.sleep(0.5)
        send_tab_key()
        time.sleep(0.5)
        # Find item
        find_and_click_item(window)
        # Close trunk & lock vehicle
        time.sleep(0.75)
        send_tab_key()
        time.sleep(0.5)
        send_e_key()
        time.sleep(1)
        send_g_key()


def focus_fivem_window(window: BaseWrapper) -> bool:
    """Bring the FiveM window to the foreground. Returns True on success."""
    try:
        hwnd = window.handle
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        win32gui.SetActiveWindow(hwnd)
        window.set_focus()
        time.sleep(0.8)  # give Windows time to switch focus
        return True
    except Exception as exc:
        print(f"[{timestamp()}] Could not focus window: {exc!r}")
        return False


def send_g_key() -> None:
    """Send the G key using the method that works (keybd_event)."""
    try:
        send_keybd_event(0x47)  # VK_G
        print(f"[{timestamp()}] Sent 'G'.")
    except Exception as exc:
        print(f"[{timestamp()}] Failed to send 'G': {exc!r}")


def send_tab_key() -> None:
    """Send the Tab key using keybd_event."""
    try:
        send_keybd_event(0x09)  # VK_TAB
        print(f"[{timestamp()}] Sent 'Tab'.")
    except Exception as exc:
        print(f"[{timestamp()}] Failed to send 'Tab': {exc!r}")


def send_x_key() -> None:
    """Send the X key."""
    try:
        send_keybd_event(0x58)  # VK_X
        print(f"[{timestamp()}] Sent 'X'.")
    except Exception as exc:
        print(f"[{timestamp()}] Failed to send 'X': {exc!r}")


def send_e_key() -> None:
    """Send the E key."""
    try:
        send_keybd_event(0x45)  # VK_E
        print(f"[{timestamp()}] Sent 'E'.")
    except Exception as exc:
        print(f"[{timestamp()}] Failed to send 'E': {exc!r}")


def find_and_click_item(window: BaseWrapper) -> None:
    """Capture the window, locate the template, move mouse to it and click."""
    if TEMPLATE_IMAGE is None:
        print(f"[{timestamp()}] Template image not loaded; skipping detection.")
        return
    try:
        snap, origin = capture_window_image(window.handle)
        match = match_template(snap, TEMPLATE_IMAGE, MATCH_THRESHOLD)
        if match is None:
            print(f"[{timestamp()}] Item not found on screen.")
            return
        target = (origin[0] + match[0], origin[1] + match[1])
        move_mouse_and_click(target)
        print(f"[{timestamp()}] Clicked item at {target}.")
    except Exception as exc:
        print(f"[{timestamp()}] Detection failed: {exc!r}")


def capture_window_image(hwnd: int) -> Tuple[np.ndarray, Tuple[int, int]]:
    """Grab a screenshot of the left half of the window; returns (image BGR, (left, top))."""
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    full_width, height = right - left, bottom - top
    width = full_width // 2  # only left half
    with mss.mss() as sct:
        monitor = {"left": left, "top": top, "width": width, "height": height}
        img = np.array(sct.grab(monitor))
    bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return bgr, (left, top)


def match_template(source: np.ndarray, template: np.ndarray, threshold: float) -> Optional[Tuple[int, int]]:
    """Return center (x, y) in source if template match exceeds threshold."""
    res = cv2.matchTemplate(source, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    if max_val < threshold:
        return None
    center_x = max_loc[0] + TEMPLATE_W // 2
    center_y = max_loc[1] + TEMPLATE_H // 2
    return center_x, center_y


def move_mouse_and_click(pos: Tuple[int, int]) -> None:
    """Move cursor to absolute screen coords and perform a Ctrl+click."""
    x, y = map(int, pos)
    win32api.SetCursorPos((x, y))
    time.sleep(0.02)
    # Hold Ctrl
    ctrl_scan = ctypes.windll.user32.MapVirtualKeyW(win32con.VK_CONTROL, 0)
    win32api.keybd_event(win32con.VK_CONTROL, ctrl_scan, 0, 0)
    time.sleep(0.01)
    # Left click
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.01)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.01)
    # Release Ctrl
    win32api.keybd_event(win32con.VK_CONTROL, ctrl_scan, win32con.KEYEVENTF_KEYUP, 0)


def send_keybd_event(vk_code: int) -> None:
    """Fallback using deprecated keybd_event (still works for some games)."""
    scan = ctypes.windll.user32.MapVirtualKeyW(vk_code, 0)
    win32api.keybd_event(vk_code, scan, 0, 0)
    time.sleep(0.02)
    win32api.keybd_event(vk_code, scan, win32con.KEYEVENTF_KEYUP, 0)

def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main() -> None:
    print(
        f"[{timestamp()}] FiveM bot started. Interval: {INTERVAL_SECONDS} seconds. "
        f"Looking for window title matching: '{WINDOW_TITLE_PATTERN}'."
    )
    while True:
        window = find_fivem_window()
        if DEBUG and window:
            print(f"[{timestamp()}] Debug: window found: {window is not None}")
            
            find_and_click_item(window)
        elif window:
            print(f"[{timestamp()}] Work starting....")
            work(window)
        else:
            print(f"[{timestamp()}] FiveM window not found.")
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
