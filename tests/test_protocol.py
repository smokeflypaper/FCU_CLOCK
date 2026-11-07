import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fcu_desktop.protocol import build_display_reports, build_led_report


class DisplayProtocolTests(unittest.TestCase):
    def test_builds_lcd_backlight_report(self):
        self.assertEqual(
            build_led_report(channel=1, brightness=180),
            bytes([0x02, 0x10, 0xBB, 0, 0, 3, 0x49, 1, 180, 0, 0, 0, 0, 0]),
        )

    def test_rejects_brightness_outside_byte_range(self):
        with self.assertRaisesRegex(ValueError, "0 through 255"):
            build_led_report(channel=1, brightness=256)

    def test_builds_known_clock_and_date_payload(self):
        update, commit = build_display_reports("07", "11", "07 11", "")

        self.assertEqual(len(update), 64)
        self.assertEqual(len(commit), 64)
        self.assertEqual(update[:25], bytes([
            0xF0, 0x00, 0x01, 0x31, 0x10, 0xBB, 0x00, 0x00,
            0x02, 0x01, 0x00, 0x00, 0xFF, 0xFF, 0x02, 0x00,
            0x00, 0x20, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        ]))
        self.assertEqual(
            update[25:42],
            bytes([
                0xFA, 0xE0, 0x00,       # SPD: 07, no decimal/label flags
                0x00, 0x06, 0x06, 0x00, # HDG: 11, no label flags
                0xA0, 0x0F, 0x0E, 0x00, 0x06, 0x06, # ALT: 07 11
                0x00, 0x00, 0x00, 0x00, # blank V/S, no label flags
            ]),
        )
        self.assertEqual(
            commit[:18],
            bytes([
                0xF0, 0x00, 0x01, 0x11, 0x10, 0xBB, 0x00, 0x00,
                0x03, 0x01, 0x00, 0x00, 0xFF, 0xFF, 0x02, 0x00,
                0x00, 0x00,
            ]),
        )

    def test_rejects_values_that_do_not_fit_the_physical_displays(self):
        with self.assertRaisesRegex(ValueError, "SPD supports at most 3"):
            build_display_reports("1234", "00", "01 01", "")


if __name__ == "__main__":
    unittest.main()
