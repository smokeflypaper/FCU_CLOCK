"""WINCTRL 32 FCU display report encoding.

Protocol layout and segment wiring are derived from schenlap/winwing_fcu,
licensed GPL-3.0: https://github.com/schenlap/winwing_fcu
"""

SEGMENTS = {
    "0": 0xFA, "1": 0x60, "2": 0xD6, "3": 0xF4, "4": 0x6C,
    "5": 0xBC, "6": 0xBE, "7": 0xE0, "8": 0xFE, "9": 0xFC,
    "C": 0x9A, "-": 0x04, " ": 0x00,
}


def build_led_report(channel: int, brightness: int) -> bytes:
    """Build a WINCTRL FCU LED/backlight output report."""
    if not 0 <= brightness <= 255:
        raise ValueError("brightness must be 0 through 255")
    if not 0 <= channel <= 255:
        raise ValueError("channel must be 0 through 255")
    return bytes([0x02, 0x10, 0xBB, 0, 0, 3, 0x49, channel, brightness, 0, 0, 0, 0, 0])


def _normal(width: int, text: str) -> list[int]:
    result = [0] * width
    for index, char in enumerate(text):
        result[width - 1 - index] = SEGMENTS[char]
    return result


def _swap_nibbles(value: int) -> int:
    return ((value & 0x0F) << 4) | ((value & 0xF0) >> 4)


def _swapped(width: int, text: str) -> list[int]:
    result = [_swap_nibbles(value) for value in _normal(width, text)] + [0]
    for index in range(width):
        result[width - index] = (
            (result[width - index] & 0x0F)
            | (result[width - 1 - index] & 0xF0)
        )
        result[width - 1 - index] &= 0x0F
    return result


def _validate(label: str, text: str, width: int) -> None:
    if len(text) > width:
        raise ValueError(f"{label} supports at most {width} characters")
    unsupported = set(text) - SEGMENTS.keys()
    if unsupported:
        raise ValueError(f"{label} contains unsupported characters: {unsupported}")


def build_display_reports(
    speed: str, heading: str, altitude: str, vertical_speed: str
) -> tuple[bytes, bytes]:
    """Return the 64-byte update and commit reports for all FCU displays."""
    fields = (
        ("SPD", speed, 3),
        ("HDG", heading, 3),
        ("ALT", altitude, 5),
        ("V/S", vertical_speed, 4),
    )
    for label, text, width in fields:
        _validate(label, text, width)

    s = _normal(3, speed)
    h = _swapped(3, heading)
    a = _swapped(5, altitude)
    v = _swapped(4, vertical_speed)

    update = [
        0xF0, 0x00, 0x01, 0x31, 0x10, 0xBB, 0x00, 0x00,
        0x02, 0x01, 0x00, 0x00, 0xFF, 0xFF, 0x02, 0x00,
        0x00, 0x20, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        s[2], s[1], s[0],
        h[3], h[2], h[1], h[0],
        a[5], a[4], a[3], a[2], a[1], a[0] | v[4],
        v[3], v[2], v[1], v[0],
    ]
    update.extend([0] * (64 - len(update)))

    commit = [
        0xF0, 0x00, 0x01, 0x11, 0x10, 0xBB, 0x00, 0x00,
        0x03, 0x01, 0x00, 0x00, 0xFF, 0xFF, 0x02, 0x00, 0x00, 0x00,
    ]
    commit.extend([0] * (64 - len(commit)))
    return bytes(update), bytes(commit)
