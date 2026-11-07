import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fcu_desktop.system_actions import WindowsActions


class FakeBackend:
    def __init__(self):
        self.calls = []

    def key_press(self, virtual_key):
        self.calls.append(("key", virtual_key))

    def wheel(self, delta):
        self.calls.append(("wheel", delta))

    def hotkey(self, *virtual_keys):
        self.calls.append(("hotkey", virtual_keys))


class FakeAppVolume:
    def __init__(self, result=True, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def change(self, step):
        self.calls.append(("change", step))
        if self.error:
            raise self.error
        return self.result

    def toggle_mute(self):
        self.calls.append(("toggle_mute",))
        if self.error:
            raise self.error
        return self.result


class WindowsActionsTests(unittest.TestCase):
    def test_invokes_global_media_and_navigation_keys(self):
        backend = FakeBackend()
        actions = WindowsActions(backend, app_volume=FakeAppVolume(result=None))
        expected = {
            "volume_down": 0xAE,
            "volume_up": 0xAF,
            "volume_mute": 0xAD,
            "media_play_pause": 0xB3,
            "left": 0x25,
            "right": 0x27,
            "home": 0x24,
        }
        for action, virtual_key in expected.items():
            actions.invoke(action)
            self.assertEqual(backend.calls[-1], ("key", virtual_key))

    def test_invokes_mouse_wheel_in_requested_direction(self):
        backend = FakeBackend()
        actions = WindowsActions(backend)
        actions.invoke("scroll_up")
        actions.invoke("scroll_down")
        self.assertEqual(backend.calls, [("wheel", 120), ("wheel", -120)])

    def test_show_desktop_uses_windows_d_hotkey(self):
        backend = FakeBackend()
        actions = WindowsActions(backend, app_volume=FakeAppVolume(result=None))
        actions.invoke("show_desktop")
        self.assertEqual(backend.calls, [("hotkey", (0x5B, 0x44))])

    def test_volume_actions_control_foreground_application(self):
        backend = FakeBackend()
        app_volume = FakeAppVolume(result=0.65)
        actions = WindowsActions(backend, app_volume=app_volume)

        actions.invoke("volume_down")
        result = actions.invoke("volume_up")
        mute_result = actions.invoke("volume_mute")

        self.assertEqual(app_volume.calls, [
            ("change", -0.05),
            ("change", 0.05),
            ("toggle_mute",),
        ])
        self.assertEqual(backend.calls, [])
        self.assertEqual(result, 0.65)
        self.assertIsNone(mute_result)

    def test_volume_actions_fall_back_when_adapter_has_no_session_or_fails(self):
        for app_volume in (
            FakeAppVolume(result=None),
            FakeAppVolume(error=RuntimeError("Core Audio failed")),
        ):
            with self.subTest(app_volume=app_volume):
                backend = FakeBackend()
                actions = WindowsActions(backend, app_volume=app_volume)
                actions.invoke("volume_up")
                self.assertEqual(backend.calls, [("key", 0xAF)])


if __name__ == "__main__":
    unittest.main()
