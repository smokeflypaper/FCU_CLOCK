"""Decode button and encoder transitions from WINCTRL FCU input reports."""

from dataclasses import dataclass


CONTROL_NAMES = (
    "MACH", "LOC", "TRK", "AP1", "AP2", "A/THR", "EXPED", "METRIC",
    "APPR", "SPD DEC", "SPD INC", "SPD PUSH", "SPD PULL", "HDG DEC",
    "HDG INC", "HDG PUSH", "HDG PULL", "ALT DEC", "ALT INC", "ALT PUSH",
    "ALT PULL", "VS DEC", "VS INC", "VS PUSH", "VS PULL", "ALT 100",
    "ALT 1000",
)


@dataclass(frozen=True, slots=True)
class InputEvent:
    control: str
    pressed: bool


def decode_transitions(report: bytes, previous_state: int) -> tuple[list[InputEvent], int]:
    if len(report) < 5:
        raise ValueError("FCU input report must contain at least 5 bytes")
    if report[0] != 1:
        return [], previous_state
    state = int.from_bytes(report[1:5], byteorder="little")
    changed = state ^ previous_state
    events = []
    for bit in range(32):
        mask = 1 << bit
        if changed & mask:
            name = CONTROL_NAMES[bit] if bit < len(CONTROL_NAMES) else f"UNKNOWN {bit}"
            events.append(InputEvent(name, bool(state & mask)))
    return events, state
