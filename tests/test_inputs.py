import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fcu_desktop.inputs import decode_transitions
from fcu_desktop.device import select_fcu


class InputDecoderTests(unittest.TestCase):
    def test_decodes_encoder_press_and_release_transitions(self):
        pressed = bytes([1, 0x00, 0x04, 0x00, 0x00])  # bit 10: SPD INC
        events, state = decode_transitions(pressed, 0)
        self.assertEqual([(event.control, event.pressed) for event in events], [("SPD INC", True)])

        released = bytes([1, 0x00, 0x00, 0x00, 0x00])
        events, state = decode_transitions(released, state)
        self.assertEqual([(event.control, event.pressed) for event in events], [("SPD INC", False)])
        self.assertEqual(state, 0)

    def test_unknown_input_bit_is_reported_not_discarded(self):
        events, _ = decode_transitions(bytes([1, 0, 0, 0, 0x80]), 0)
        self.assertEqual(events[0].control, "UNKNOWN 31")
        self.assertTrue(events[0].pressed)

    def test_rejects_short_input_report(self):
        with self.assertRaisesRegex(ValueError, "at least 5 bytes"):
            decode_transitions(bytes([1, 2]), 0)

    def test_ignores_brightness_reply_instead_of_decoding_it_as_buttons(self):
        previous_state = 1 << 26
        brightness_reply = bytes.fromhex("0210cb000003490069")

        events, state = decode_transitions(brightness_reply, previous_state)

        self.assertEqual(events, [])
        self.assertEqual(state, previous_state)


class DeviceSelectionTests(unittest.TestCase):
    def test_selects_winctrl_fcu_by_vid_and_pid(self):
        devices = [
            {"vendor_id": 0x1234, "product_id": 0xBB10, "path": b"wrong"},
            {"vendor_id": 0x4098, "product_id": 0xBB10, "path": b"fcu"},
        ]
        self.assertEqual(select_fcu(devices)["path"], b"fcu")

    def test_missing_fcu_returns_none(self):
        self.assertIsNone(select_fcu([]))


if __name__ == "__main__":
    unittest.main()
