import json
import sys
import unittest
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fcu_desktop.weather import configured_weather_url, fetch_temperature, format_temperature


class Response(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class WeatherTests(unittest.TestCase):
    def test_builds_weather_url_from_environment_without_embedded_location(self):
        url = configured_weather_url(
            {
                "FCU_CLOCK_LATITUDE": "50.0000",
                "FCU_CLOCK_LONGITUDE": "15.0000",
            }
        )

        self.assertIn("latitude=50.0000", url)
        self.assertIn("longitude=15.0000", url)

    def test_location_must_be_configured(self):
        with self.assertRaisesRegex(ValueError, "FCU_CLOCK_LATITUDE"):
            configured_weather_url({})

    def test_formats_temperature_for_four_character_vs_display(self):
        self.assertEqual(format_temperature(1.3), "  1C")
        self.assertEqual(format_temperature(-10.2), "-10C")
        self.assertEqual(format_temperature(23.0), " 23C")

    def test_blank_temperature_is_blank_display(self):
        self.assertEqual(format_temperature(None), "")

    def test_fetches_current_temperature_from_open_meteo_shape(self):
        payload = json.dumps({"current": {"temperature_2m": 1.3}}).encode()

        value = fetch_temperature(
            url="https://example.test/weather",
            opener=lambda *_args, **_kwargs: Response(payload),
        )

        self.assertEqual(value, 1.3)

    def test_rejects_malformed_weather_response(self):
        payload = json.dumps({"current": {}}).encode()
        with self.assertRaisesRegex(ValueError, "temperature_2m"):
            fetch_temperature(
                url="https://example.test/weather",
                opener=lambda *_args, **_kwargs: Response(payload),
            )


if __name__ == "__main__":
    unittest.main()
