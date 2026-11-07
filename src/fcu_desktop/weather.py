"""Current outdoor temperature for a user-configured location via Open-Meteo."""

import json
import os
from collections.abc import Callable
from collections.abc import Mapping
from urllib.request import urlopen


def configured_weather_url(environ: Mapping[str, str] = os.environ) -> str:
    latitude = environ.get("FCU_CLOCK_LATITUDE")
    longitude = environ.get("FCU_CLOCK_LONGITUDE")
    if not latitude or not longitude:
        raise ValueError(
            "Set FCU_CLOCK_LATITUDE and FCU_CLOCK_LONGITUDE to enable weather"
        )
    return (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}"
        "&current=temperature_2m&timezone=auto"
    )


def fetch_temperature(*, url: str | None = None, opener: Callable = urlopen) -> float:
    with opener(url or configured_weather_url(), timeout=5) as response:
        payload = json.load(response)
    try:
        return float(payload["current"]["temperature_2m"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Open-Meteo response has no valid temperature_2m") from error


def format_temperature(value: float | None) -> str:
    if value is None:
        return ""
    rounded = max(-99, min(99, round(value)))
    return f"{rounded}C".rjust(4)
