import sys
import unittest
from datetime import datetime
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from fcu_desktop.clock import ClockFields


class ClockFieldsTests(unittest.TestCase):
    def test_preserves_leading_zeroes_for_clock_and_date(self) -> None:
        fields = ClockFields.from_datetime(datetime(2026, 11, 7, 7, 3))

        self.assertEqual(fields.hour, "07")
        self.assertEqual(fields.minute, "03")
        self.assertEqual(fields.day, "07")
        self.assertEqual(fields.month, "11")

    def test_midnight_at_month_boundary_has_valid_fields(self) -> None:
        fields = ClockFields.from_datetime(datetime(2027, 1, 1, 0, 0))

        self.assertEqual(fields.hour, "00")
        self.assertEqual(fields.minute, "00")
        self.assertEqual(fields.day, "01")
        self.assertEqual(fields.month, "01")


if __name__ == "__main__":
    unittest.main()
