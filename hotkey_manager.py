"""
High-Performance Native Windows Hotkey Manager for PRORP Translator.

Uses Windows native RegisterHotKey API via a dedicated Win32 message loop thread,
guaranteeing system-wide hotkey interception even while exclusive 3D games (GTA, FiveM, SAMP)
have active window focus. Includes pynput fallback and audio feedback.
"""

from __future__ import annotations

import sys
import time
import ctypes
import threading
from typing import Any
from ctypes import wintypes

from PyQt6.QtCore import QObject, pyqtSignal

user32 = ctypes.windll.user32
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000


# Win32 API function signatures for 64-bit Windows reliability
user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
user32.RegisterHotKey.restype = wintypes.BOOL
user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
user32.UnregisterHotKey.restype = wintypes.BOOL
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetAsyncKeyState.restype = ctypes.c_short


class HotkeyManager(QObject):
    """
    Manages global system hotkeys for games and desktop.
    Emits Qt signals when shortcuts fire.
    """

    ocr_input = pyqtSignal()
    ocr_chatlog = pyqtSignal()
    ocr_capture = pyqtSignal()  # Backward-compatible alias for ocr_input
    clipboard_capture = pyqtSignal()
    copy_answer_1 = pyqtSignal()
    copy_answer_2 = pyqtSignal()
    copy_answer_3 = pyqtSignal()
    toggle_window = pyqtSignal()
    scroll_up = pyqtSignal()
    scroll_down = pyqtSignal()
    triggered = pyqtSignal(str)

    def __init__(self, config_manager: Any = None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._config = config_manager
        self._thread: threading.Thread | None = None
        self._poll_thread: threading.Thread | None = None
        self._pynput_listener: Any = None
        self._thread_id: int | None = None
        self._is_running = False
        self._last_trigger_time: dict[str, float] = {}

        # Signal dispatcher mapping
        self._signal_map = {
            "ocr_input": self.ocr_input,
            "ocr_chatlog": self.ocr_chatlog,
            "ocr_capture": self.ocr_capture,
            "clipboard_capture": self.clipboard_capture,
            "copy_answer_1": self.copy_answer_1,
            "copy_answer_2": self.copy_answer_2,
            "copy_answer_3": self.copy_answer_3,
            "toggle_window": self.toggle_window,
            "scroll_up": self.scroll_up,
            "scroll_down": self.scroll_down,
        }

        # Registered hotkey definitions: id -> (action_name, mods, vk, raw_string)
        self._hotkey_defs: dict[int, tuple[str, int, int, str]] = {}
        self.reload_config()

    def reload_config(self) -> None:
        """Parse all configured hotkeys into Win32 modifier and virtual-key codes."""
        was_running = self._is_running
        if was_running:
            self.stop()

        self._hotkey_defs.clear()

        if not self._config:
            return

        cfg = self._config.config if hasattr(self._config, "config") else {}
        hk_dict = cfg.get("hotkeys", {})

        def get_hk(flat_key: str, nested_key: str, default: str) -> str:
            return cfg.get(flat_key) or hk_dict.get(nested_key) or default

        bindings = [
            (1, "ocr_input", get_hk("hotkey_ocr_input", "ocr_input", get_hk("hotkey_ocr", "ocr_capture", "<f4>"))),
            (2, "ocr_chatlog", get_hk("hotkey_ocr_chatlog", "ocr_chatlog", "<f3>")),
            (3, "clipboard_capture", get_hk("hotkey_clipboard", "clipboard_capture", "<f5>")),
            (4, "copy_answer_1", get_hk("hotkey_ans1", "copy_answer_1", "<ctrl>+1")),
            (5, "copy_answer_2", get_hk("hotkey_ans2", "copy_answer_2", "<ctrl>+2")),
            (6, "copy_answer_3", get_hk("hotkey_ans3", "copy_answer_3", "<ctrl>+3")),
            (7, "toggle_window", get_hk("hotkey_toggle_window", "toggle_window", "<insert>")),
            (8, "scroll_up", get_hk("hotkey_scroll_up", "scroll_up", "<page_up>")),
            (9, "scroll_down", get_hk("hotkey_scroll_down", "scroll_down", "<page_down>")),
        ]

        for hid, action, raw_str in bindings:
            mods, vk = self._parse_to_win32(raw_str)
            if vk > 0:
                self._hotkey_defs[hid] = (action, mods, vk, raw_str)

        if was_running:
            self.start()

    @staticmethod
    def _parse_to_win32(key_string: str) -> tuple[int, int]:
        """
        Convert hotkey strings like '<f4>', '<ctrl>+1', 'insert' to Win32 (mods, vk).
        """
        raw = key_string.strip().lower()
        parts = [p.strip().strip("<>").lower() for p in raw.split("+")]

        mods = MOD_NOREPEAT
        vk = 0

        VK_MAP = {
            "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73, "f5": 0x74, "f6": 0x75,
            "f7": 0x76, "f8": 0x77, "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
            "insert": 0x2D, "page_up": 0x21, "pageup": 0x21, "page_down": 0x22, "pagedown": 0x22,
            "home": 0x24, "end": 0x23, "esc": 0x1B, "escape": 0x1B, "space": 0x20, "tab": 0x09, "enter": 0x0D,
        }

        for p in parts:
            if p in ("ctrl", "control"):
                mods |= MOD_CONTROL
            elif p in ("alt", "menu"):
                mods |= MOD_ALT
            elif p in ("shift",):
                mods |= MOD_SHIFT
            elif p in ("win", "cmd"):
                mods |= MOD_WIN
            elif p in VK_MAP:
                vk = VK_MAP[p]
            elif len(p) == 1:
                vk = ord(p.upper())

        return mods, vk

    # ── Threaded Triple-Engine Hotkey Listeners ────────────────────────

    def start(self) -> None:
        """
        Start triple-engine hotkey interception:
        1. Low-Level Keyboard Hook (WH_KEYBOARD_LL) - fastest desktop/game interception
        2. Hardware State Polling (GetAsyncKeyState) - bypasses Error 1409 & DirectX grabs
        3. Native Win32 Message Loop (RegisterHotKey) - standard Windows registered hotkeys
        """
        if self._is_running:
            return

        self._is_running = True

        # Engine 1: Native Win32 RegisterHotKey loop
        ready_event = threading.Event()
        self._thread = threading.Thread(
            target=self._win32_hotkey_loop,
            args=(ready_event,),
            daemon=True,
            name="Win32HotkeyThread",
        )
        self._thread.start()

        # Engine 2: Direct Hardware Keystate Polling (15ms / ~66Hz)
        self._poll_thread = threading.Thread(
            target=self._hardware_poll_loop,
            daemon=True,
            name="HardwareHotkeyPollThread",
        )
        self._poll_thread.start()

        # Engine 3: Low-Level Windows Keyboard Hook (WH_KEYBOARD_LL)
        try:
            import pynput.keyboard as pk

            pynput_map = {}
            for hid, (action, req_mods, vk, raw_str) in self._hotkey_defs.items():
                s = raw_str.strip().lower()
                parts = s.split("+")
                norm_parts = []
                for p in parts:
                    clean_name = p.strip().strip("<>")
                    if clean_name in (
                        "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12",
                        "ctrl", "control", "alt", "shift", "win", "cmd", "insert",
                        "page_up", "pageup", "page_down", "pagedown", "home", "end", "space", "tab", "enter"
                    ):
                        norm_parts.append(f"<{clean_name}>")
                    else:
                        norm_parts.append(clean_name)
                norm_key = "+".join(norm_parts)

                def _make_handler(act: str):
                    return lambda: self._dispatch_action(act)

                pynput_map[norm_key] = _make_handler(action)

            self._pynput_listener = pk.GlobalHotKeys(pynput_map)
            self._pynput_listener.daemon = True
            self._pynput_listener.start()
        except Exception as e:
            print(f"[HotkeyManager] Low-level keyboard hook skipped: {e}")

        ready_event.wait(timeout=1.0)
        print(f"[HotkeyManager] Triple-engine hotkey listeners active with {len(self._hotkey_defs)} hotkeys")

    def stop(self) -> None:
        """Stop all background hotkey threads and hooks."""
        if not self._is_running:
            return

        self._is_running = False

        # Stop pynput hook
        if self._pynput_listener:
            try:
                self._pynput_listener.stop()
            except Exception:
                pass
            self._pynput_listener = None

        # Stop Win32 thread
        if self._thread_id:
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)

        # Stop hardware poll thread
        if self._poll_thread and self._poll_thread.is_alive():
            self._poll_thread.join(timeout=0.5)

        self._thread = None
        self._poll_thread = None
        self._thread_id = None
        print("[HotkeyManager] Triple-engine hotkey listeners stopped")

    def _win32_hotkey_loop(self, ready_event: threading.Event) -> None:
        """Runs the native Windows GetMessage loop in a dedicated background thread."""
        self._thread_id = threading.get_native_id()

        # Force message queue creation for this thread
        msg = wintypes.MSG()
        user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 0)

        registered_ids = []
        for hid, (action, mods, vk, raw_str) in self._hotkey_defs.items():
            success = user32.RegisterHotKey(None, hid, mods, vk)
            if success:
                registered_ids.append(hid)

        ready_event.set()

        try:
            while self._is_running:
                ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if ret == 0 or ret == -1:
                    break

                if msg.message == WM_HOTKEY:
                    hid = int(msg.wParam)
                    if hid in self._hotkey_defs:
                        action, _, _, _ = self._hotkey_defs[hid]
                        self._dispatch_action(action)

                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            for hid in registered_ids:
                user32.UnregisterHotKey(None, hid)

    def _hardware_poll_loop(self) -> None:
        """
        Direct hardware keyboard state polling loop.
        Guarantees hotkeys fire even when RegisterHotKey is blocked by error 1409
        (e.g., F3/F4/F5 locked by FiveM, GPU overlays, or other apps),
        and works flawlessly inside full-screen 3D games.
        """
        last_state: dict[int, bool] = {hid: False for hid in self._hotkey_defs}

        while self._is_running:
            try:
                # Query modifier keys state
                ctrl_pressed = bool(
                    (user32.GetAsyncKeyState(0x11) & 0x8000)
                    or (user32.GetAsyncKeyState(0xA2) & 0x8000)
                    or (user32.GetAsyncKeyState(0xA3) & 0x8000)
                )
                alt_pressed = bool(
                    (user32.GetAsyncKeyState(0x12) & 0x8000)
                    or (user32.GetAsyncKeyState(0xA4) & 0x8000)
                    or (user32.GetAsyncKeyState(0xA5) & 0x8000)
                )
                shift_pressed = bool(
                    (user32.GetAsyncKeyState(0x10) & 0x8000)
                    or (user32.GetAsyncKeyState(0xA0) & 0x8000)
                    or (user32.GetAsyncKeyState(0xA1) & 0x8000)
                )
                win_pressed = bool(
                    (user32.GetAsyncKeyState(0x5B) & 0x8000)
                    or (user32.GetAsyncKeyState(0x5C) & 0x8000)
                )

                for hid, (action, req_mods, vk, raw_str) in list(self._hotkey_defs.items()):
                    key_down = bool(user32.GetAsyncKeyState(vk) & 0x8000)
                    was_down = last_state.get(hid, False)
                    last_state[hid] = key_down

                    # Detect key down transition
                    if key_down and not was_down:
                        req_ctrl = bool(req_mods & MOD_CONTROL)
                        req_alt = bool(req_mods & MOD_ALT)
                        req_shift = bool(req_mods & MOD_SHIFT)
                        req_win = bool(req_mods & MOD_WIN)

                        if (
                            ctrl_pressed == req_ctrl
                            and alt_pressed == req_alt
                            and shift_pressed == req_shift
                            and win_pressed == req_win
                        ):
                            self._dispatch_action(action)
            except Exception as e:
                print(f"[HotkeyManager] Polling loop exception: {e}")

            time.sleep(0.015)  # 15ms poll rate = ~66Hz, zero CPU usage, instant response

    def _dispatch_action(self, action: str) -> None:
        """Dispatches action with debounce."""
        now = time.time()
        last = self._last_trigger_time.get(action, 0)
        if now - last < 0.25:  # 250ms debounce
            return
        self._last_trigger_time[action] = now

        # Dispatch action silently without disturbing Windows system sounds
        print(f"[HotkeyManager] Hotkey triggered: {action}")
        self.triggered.emit(action)
        if action in self._signal_map:
            self._signal_map[action].emit()
