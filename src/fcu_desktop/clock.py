"""Local clock values formatted for numeric FCU display fields."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ClockFields:
    hour: str
    minute: str
    day: str
    month: str

    @classmethod
    def from_datetime(cls, value: datetime) -> "ClockFields":
        return cls(
            hour=f"{value.hour:02d}",
            minute=f"{value.minute:02d}",
            day=f"{value.day:02d}",
            month=f"{value.month:02d}",
        )
