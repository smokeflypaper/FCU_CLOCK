"""Command-line interface for FCU Desktop."""

import argparse
import sys
import time
from datetime import datetime
from typing import Callable, TextIO

from .clock import ClockFields
from .controls import DesktopController
from .device import load_hid, select_fcu
from .inputs import decode_transitions
from .protocol import build_display_reports, build_led_report
from .weather import fetch_temperature, format_temperature
from .platform_actions import NoActions, create_actions


class VolumeOverlay:
    def __init__(self, duration: float = 3.0):
        self._duration = duration
        self._percent = None
        self._deadline = 0.0

    def show(self, percent: int, *, at: float) -> None:
        self._percent = percent
        self._deadline = at + self._duration

    def current(self, *, at: float) -> int | None:
        if self._percent is None or at >= self._deadline:
            return None
        return self._percent

    def clear(self) -> None:
        self._percent = None


def _weather_refresh_due(tick: float, deadline: float, overlay_percent: int | None) -> bool:
    return overlay_percent is None and tick >= deadline


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fcu-desktop")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("discover", help="Find the WINCTRL 32 FCU")
    commands.add_parser("doctor", help="Check hardware and desktop dependencies")
    clock = commands.add_parser("clock", help="Show local system time and date")
    clock.add_argument("--once", action="store_true", help="Write once, then exit")
    clock.add_argument("--no-controls", action="store_true", help="Clock and FCU brightness only")
    return parser


def _write_clock(
    handle,
    value: datetime,
    temperature: float | None,
    *,
    spd_override: str | None = None,
) -> None:
    fields = ClockFields.from_datetime(value)
    update, commit = build_display_reports(
        spd_override if spd_override is not None else fields.hour,
        fields.minute,
        f"{fields.day} {fields.month}",
        format_temperature(temperature),
    )
    handle.write(update)
    handle.write(commit)


def main(
    argv: list[str] | None = None,
    *,
    hid_module=None,
    output: TextIO = sys.stdout,
    now: Callable[[], datetime] = datetime.now,
    temperature_provider: Callable[[], float | None] | None = None,
    system_actions=None,
    monotonic: Callable[[], float] = time.monotonic,
) -> int:
    args = _parser().parse_args(argv)
    if hid_module is None:
        try:
            hid_module = load_hid()
        except ImportError as error:
            print(f"HID dependency missing: {error}. Run python -m pip install -e .", file=output)
            return 1

    try:
        descriptor = select_fcu(hid_module.enumerate())
    except OSError as error:
        print(f"HID discovery failed: {error}", file=output)
        return 1
    if args.command == "doctor":
        from .diagnostics import diagnose
        result = diagnose(hid_module, descriptor, output)
        return 2 if descriptor is None else result
    if descriptor is None:
        print("WINCTRL 32 FCU nebylo nalezeno.", file=output)
        print("Ukoncete MobiFlight a SimAppPro, pripojte FCU a zkuste to znovu.", file=output)
        return 2

    if args.command == "discover":
        name = descriptor.get("product_string") or "WINCTRL 32 FCU"
        print(f"Nalezeno: {name}", file=output)
        return 0

    handle = hid_module.device()
    owned_actions = None
    try:
        if temperature_provider is None:
            temperature_provider = fetch_temperature
        try:
            temperature = temperature_provider()
        except (OSError, ValueError) as error:
            temperature = None
            print(f"Pocasi nelze nacist: {error}", file=output)

        handle.open_path(descriptor["path"])
        handle.write(build_led_report(0, 180))
        handle.write(build_led_report(1, 180))
        overlay = VolumeOverlay()
        overlay_displayed = False

        def show_volume(percent: int | None) -> None:
            nonlocal overlay_displayed
            if percent is None:
                overlay.clear()
                if overlay_displayed:
                    _write_clock(handle, now(), temperature)
                overlay_displayed = False
                return
            overlay.show(percent, at=monotonic())
            overlay_displayed = True
            _write_clock(handle, now(), temperature, spd_override=str(percent))

        _write_clock(handle, now(), temperature)
        if args.once:
            print("Cas a datum byly zapsany do FCU.", file=output)
            return 0

        actions = system_actions
        if args.no_controls:
            actions = NoActions()
        elif actions is None:
            actions = owned_actions = create_actions()
        if hasattr(actions, "prepare"):
            try:
                actions.prepare()
            except (OSError, RuntimeError, ImportError) as error:
                print(f"Desktop input unavailable: {error}. Clock and audio remain available.", file=output)
        controller = DesktopController(actions, handle, on_volume=show_volume)
        print("FCU Desktop bezi. Ukonceni: Ctrl+C", file=output)
        previous_state = 0
        last_minute = None
        next_weather_update = monotonic() + 900
        while True:
            current = now()
            tick = monotonic()
            overlay_percent = overlay.current(at=tick)
            if overlay_displayed and overlay_percent is None:
                _write_clock(handle, current, temperature)
                overlay_displayed = False
            if _weather_refresh_due(tick, next_weather_update, overlay_percent):
                try:
                    temperature = temperature_provider()
                except (OSError, ValueError) as error:
                    print(f"Pocasi nelze aktualizovat: {error}", file=output)
                tick = monotonic()
                next_weather_update = tick + 900
            minute_key = (current.year, current.month, current.day, current.hour, current.minute)
            if minute_key != last_minute:
                _write_clock(
                    handle,
                    current,
                    temperature,
                    spd_override=(
                        str(overlay_percent) if overlay_percent is not None else None
                    ),
                )
                last_minute = minute_key
            # Keep up with the FCU's rapid encoder reports. A long blocking read
            # plus an additional sleep lets old button reports queue up, making
            # actions appear under the control being used later.
            report = bytes(handle.read(64, 5))
            if report:
                events, previous_state = decode_transitions(report, previous_state)
                for event in events:
                    try:
                        controller.handle(event)
                    except (OSError, RuntimeError, ValueError, KeyError, ImportError) as error:
                        print(f"Action {event.control} failed: {error}", file=output)
                    state = "stisk" if event.pressed else "uvolneni"
                    print(f"{event.control}: {state}", file=output)
    except KeyboardInterrupt:
        print("FCU Desktop ukoncen.", file=output)
        return 0
    except (OSError, RuntimeError) as error:
        print(f"FCU error: {error}. Close other FCU programs; check USB and Linux udev permissions (README).", file=output)
        return 1
    finally:
        try:
            handle.close()
        finally:
            if owned_actions is not None and hasattr(owned_actions, "close"):
                owned_actions.close()


if __name__ == "__main__":
    raise SystemExit(main())
