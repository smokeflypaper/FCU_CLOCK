"""WINCTRL 32 FCU HID identity and selection."""

from collections.abc import Iterable, Mapping
from typing import Any


VENDOR_ID = 0x4098
PRODUCT_ID = 0xBB10


def select_fcu(devices: Iterable[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    for device in devices:
        if device.get("vendor_id") == VENDOR_ID and device.get("product_id") == PRODUCT_ID:
            return device
    return None
