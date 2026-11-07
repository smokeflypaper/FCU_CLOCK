import io
import sys
import unittest
from unittest.mock import patch
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fcu_desktop.cli import VolumeOverlay, _weather_refresh_due, _write_clock, main


class FakeHandle:
    def __init__(self):
        self.opened_path = None
        self.writes = []
        self.closed = False

    def open_path(self, path):
        self.opened_path = path

    def write(self, report):
        self.writes.append(bytes(report))
        return len(report)

    def close(self):
        self.closed = True


class InterruptingHandle(FakeHandle):
    def __init__(self):
        super().__init__()
        self.read_timeouts = []

    def read(self, size, timeout_ms):
        self.read_timeouts.append(timeout_ms)
        if len(self.read_timeouts) == 1:
            return []
        raise KeyboardInterrupt


class FakeHid:
    def __init__(self, devices):
        self.devices = devices
        self.handle = FakeHandle()

    def enumerate(self):
        return self.devices

    def device(self):
        return self.handle


class CliTests(unittest.TestCase):
    def test_volume_overlay_refreshes_deadline_and_expires_after_three_seconds(self):
        overlay = VolumeOverlay(duration=3.0)
        overlay.show(73, at=10.0)
        self.assertEqual(overlay.current(at=12.9), 73)
        overlay.show(80, at=12.0)
        self.assertEqual(overlay.current(at=14.9), 80)
        self.assertIsNone(overlay.current(at=15.0))

    def test_volume_overlay_can_be_cleared_by_global_fallback(self):
        overlay = VolumeOverlay(duration=3.0)
        overlay.show(73, at=10.0)
        overlay.clear()
        self.assertIsNone(overlay.current(at=10.1))

    def test_weather_refresh_is_deferred_while_volume_overlay_is_visible(self):
        self.assertFalse(_weather_refresh_due(900.0, 900.0, 73))
        self.assertTrue(_weather_refresh_due(903.0, 900.0, None))

    def test_clock_writer_can_show_percent_then_restore_current_hour(self):
        handle = FakeHandle()
        value = datetime(2026, 11, 7, 4, 30)
        _write_clock(handle, value, 1.3, spd_override="0")
        percent_report = handle.writes[-2]
        _write_clock(handle, value, 1.3)
        clock_report = handle.writes[-2]
        self.assertNotEqual(percent_report[25:27], clock_report[25:27])

    def test_continuous_clock_polls_hid_quickly_without_extra_delay(self):
        hid = FakeHid([{
            "vendor_id": 0x4098,
            "product_id": 0xBB10,
            "path": b"fcu-path",
        }])
        hid.handle = InterruptingHandle()

        with patch("fcu_desktop.cli.time.sleep") as sleep:
            exit_code = main(
                ["clock"],
                hid_module=hid,
                output=io.StringIO(),
                now=lambda: datetime(2026, 11, 7, 14, 3),
                temperature_provider=lambda: None,
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(hid.handle.read_timeouts, [5, 5])
        sleep.assert_not_called()

    def test_clock_status_is_printable_in_legacy_windows_console(self):
        hid = FakeHid([{
            "vendor_id": 0x4098,
            "product_id": 0xBB10,
            "path": b"fcu-path",
        }])
        raw = io.BytesIO()
        output = io.TextIOWrapper(raw, encoding="cp1252")

        exit_code = main(
            ["clock", "--once"],
            hid_module=hid,
            output=output,
            now=lambda: datetime(2026, 11, 7, 14, 3),
            temperature_provider=lambda: None,
        )

        self.assertEqual(exit_code, 0)

    def test_discover_reports_missing_device_cleanly(self):
        output = io.StringIO()
        exit_code = main(["discover"], hid_module=FakeHid([]), output=output)
        self.assertEqual(exit_code, 2)
        self.assertIn("WINCTRL 32 FCU nebylo nalezeno", output.getvalue())

    def test_clock_once_writes_backlights_time_date_and_closes(self):
        hid = FakeHid([{
            "vendor_id": 0x4098,
            "product_id": 0xBB10,
            "path": b"fcu-path",
            "product_string": "WINCTRL 32 FCU",
        }])
        output = io.StringIO()

        exit_code = main(
            ["clock", "--once"],
            hid_module=hid,
            output=output,
            now=lambda: datetime(2026, 11, 7, 14, 3),
            temperature_provider=lambda: None,
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(hid.handle.opened_path, b"fcu-path")
        self.assertEqual(len(hid.handle.writes), 4)
        self.assertEqual(hid.handle.writes[0][7:9], bytes([0, 180]))
        self.assertEqual(hid.handle.writes[1][7:9], bytes([1, 180]))
        self.assertEqual(hid.handle.writes[2][25:42], bytes([
            0x60, 0x6C, 0x00, 0xA0, 0x4F, 0x0F, 0x00,
            0xA0, 0x0F, 0x0E, 0x00, 0x06, 0x06, 0x00, 0x00, 0x00, 0x00,
        ]))
        self.assertTrue(hid.handle.closed)

    def test_clock_displays_rounded_outdoor_temperature(self):
        hid = FakeHid([{
            "vendor_id": 0x4098,
            "product_id": 0xBB10,
            "path": b"fcu-path",
        }])

        exit_code = main(
            ["clock", "--once"],
            hid_module=hid,
            output=io.StringIO(),
            now=lambda: datetime(2026, 11, 7, 14, 3),
            temperature_provider=lambda: 1.3,
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(hid.handle.writes[2][38:42], bytes([0x00, 0x00, 0xA6, 0x09]))


if __name__ == "__main__":
    unittest.main()
