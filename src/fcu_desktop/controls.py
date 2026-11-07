"""Map FCU controls to desktop actions and local brightness changes."""

from .inputs import InputEvent
from .protocol import build_led_report


ACTION_MAP = {
    "MACH": "show_desktop",
    "SPD DEC": "volume_down",
    "SPD INC": "volume_up",
    "SPD PUSH": "volume_mute",
    "HDG DEC": "left",
    "HDG INC": "right",
    "HDG PUSH": "media_play_pause",
    "VS DEC": "scroll_down",
    "VS INC": "scroll_up",
    "VS PUSH": "home",
}


class DesktopController:
    def __init__(self, actions, handle, *, initial_brightness: int = 180, step: int = 15, on_volume=None):
        self._actions = actions
        self._handle = handle
        self._brightness = {0: initial_brightness, 1: initial_brightness}
        self._selected_channel = 1
        self._step = step
        self._on_volume = on_volume or (lambda _percent: None)

    def handle(self, event: InputEvent) -> None:
        if not event.pressed:
            return
        if event.control == "ALT 100":
            self._selected_channel = 1
            return
        if event.control == "ALT 1000":
            self._selected_channel = 0
            return
        if event.control in ("ALT DEC", "ALT INC"):
            direction = -1 if event.control == "ALT DEC" else 1
            level = self._brightness[self._selected_channel] + direction * self._step
            level = max(0, min(255, level))
            self._brightness[self._selected_channel] = level
            self._handle.write(build_led_report(self._selected_channel, level))
            return
        action = ACTION_MAP.get(event.control)
        if action is not None:
            level = self._actions.invoke(action)
            if event.control in ("SPD DEC", "SPD INC"):
                self._on_volume(round(level * 100) if level is not None else None)
