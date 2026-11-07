import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fcu_desktop.controls import DesktopController
from fcu_desktop.inputs import InputEvent


class FakeActions:
    def __init__(self, result=None):
        self.calls = []
        self.result = result

    def invoke(self, action):
        self.calls.append(action)
        return self.result


class FakeHandle:
    def __init__(self):
        self.writes = []

    def write(self, report):
        self.writes.append(bytes(report))


class DesktopControllerTests(unittest.TestCase):
    def test_maps_pressed_controls_to_requested_desktop_actions(self):
        actions = FakeActions()
        controller = DesktopController(actions, FakeHandle())
        expected = {
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

        for control, action in expected.items():
            controller.handle(InputEvent(control, True))
            self.assertEqual(actions.calls[-1], action)

    def test_release_and_unassigned_controls_do_nothing(self):
        actions = FakeActions()
        handle = FakeHandle()
        controller = DesktopController(actions, handle)
        controller.handle(InputEvent("SPD INC", False))
        controller.handle(InputEvent("AP1", True))
        self.assertEqual(actions.calls, [])
        self.assertEqual(handle.writes, [])

    def test_alt_selector_chooses_display_or_panel_brightness(self):
        handle = FakeHandle()
        controller = DesktopController(FakeActions(), handle, initial_brightness=180, step=15)

        controller.handle(InputEvent("ALT 100", True))
        controller.handle(InputEvent("ALT DEC", True))
        self.assertEqual(handle.writes[-1][7:9], bytes([1, 165]))

        controller.handle(InputEvent("ALT 1000", True))
        controller.handle(InputEvent("ALT INC", True))
        self.assertEqual(handle.writes[-1][7:9], bytes([0, 195]))

    def test_brightness_is_clamped_to_byte_range(self):
        handle = FakeHandle()
        controller = DesktopController(FakeActions(), handle, initial_brightness=250, step=15)
        controller.handle(InputEvent("ALT 1000", True))
        controller.handle(InputEvent("ALT INC", True))
        self.assertEqual(handle.writes[-1][8], 255)

    def test_spd_rotation_reports_application_volume_percent_only_on_success(self):
        shown = []
        controller = DesktopController(
            FakeActions(result=0.73), FakeHandle(), on_volume=shown.append
        )
        controller.handle(InputEvent("SPD INC", True))
        self.assertEqual(shown, [73])

        fallback = DesktopController(
            FakeActions(result=None), FakeHandle(), on_volume=shown.append
        )
        fallback.handle(InputEvent("SPD DEC", True))
        fallback.handle(InputEvent("SPD PUSH", True))
        self.assertEqual(shown, [73, None])


if __name__ == "__main__":
    unittest.main()
