"""Native operating-system actions used by FCU controls."""

import ctypes

from .app_volume import WindowsAppVolume


VIRTUAL_KEYS = {
    "volume_down": 0xAE,
    "volume_up": 0xAF,
    "volume_mute": 0xAD,
    "media_play_pause": 0xB3,
    "left": 0x25,
    "right": 0x27,
    "home": 0x24,
}


class WindowsBackend:
    KEYEVENTF_KEYUP = 0x0002
    MOUSEEVENTF_WHEEL = 0x0800

    def key_press(self, virtual_key: int) -> None:
        user32 = ctypes.windll.user32
        user32.keybd_event(virtual_key, 0, 0, 0)
        user32.keybd_event(virtual_key, 0, self.KEYEVENTF_KEYUP, 0)

    def wheel(self, delta: int) -> None:
        ctypes.windll.user32.mouse_event(
            self.MOUSEEVENTF_WHEEL, 0, 0, delta & 0xFFFFFFFF, 0
        )

    def hotkey(self, *virtual_keys: int) -> None:
        user32 = ctypes.windll.user32
        for virtual_key in virtual_keys:
            user32.keybd_event(virtual_key, 0, 0, 0)
        for virtual_key in reversed(virtual_keys):
            user32.keybd_event(virtual_key, 0, self.KEYEVENTF_KEYUP, 0)


class WindowsActions:
    def __init__(self, backend=None, *, app_volume=None):
        self._backend = backend or WindowsBackend()
        self._app_volume = app_volume or WindowsAppVolume()

    def invoke(self, action: str) -> float | None:
        handled = False
        level = None
        try:
            if action == "volume_down":
                level = self._app_volume.change(-0.05)
                handled = level is not None
            elif action == "volume_up":
                level = self._app_volume.change(0.05)
                handled = level is not None
            elif action == "volume_mute":
                handled = self._app_volume.toggle_mute()
        except Exception:
            handled = False

        if handled:
            return level
        if action == "show_desktop":
            self._backend.hotkey(0x5B, 0x44)
        elif action == "scroll_up":
            self._backend.wheel(120)
        elif action == "scroll_down":
            self._backend.wheel(-120)
        else:
            self._backend.key_press(VIRTUAL_KEYS[action])
