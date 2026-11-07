# Linux verification, 2026-11-07

Tested on Arch Linux, KDE Plasma 6, Wayland, Python 3.14, PipeWire with PulseAudio compatibility, and a USB WINCTRL 32 FCU (4098:bb10).

- 70 automated unittest cases pass, including the original 44 tests and Linux routing/audio/input/error cases.
- `pip check`, wheel build, `bash -n scripts/run-linux.sh`, and `git diff --check` pass.
- `doctor`: actual FCU open/close, uinput access, audio-server connection, and KDE active PID lookup pass.
- `clock --once`: actual HID backlight/time/date writes succeed using hidraw. The installed hidapi wheel's libusb module could enumerate but could not open the USB device with the local permissions; the hidraw module works without root.
- Virtual input round-trip through the kernel verifies right-key press/release and wheel direction. KDE also delivered both to an XWayland xev test window. This does not prove every application's native Wayland input handling.
- A silent, temporary paplay stream verified application-volume write/readback and mute on actual PipeWire. No unrelated application's volume was changed.
- Windows action/volume modules, shared protocol, mappings and input decoder are unchanged. Windows hardware was not available. CI is configured for Windows/Ubuntu with Python 3.11/3.13; hosted CI has not yet run for these local changes.

Remaining user validation: physically turn/press each FCU control and confirm the display, brightness channels and application-specific media behavior. Other distributions/desktops and sandboxed audio applications need real-world testing. Weather is unchanged and requires user-provided coordinates.

## Follow-up after user reported failure

The previously launched foreground process was no longer running; its exit cause was not retained, so the original failure is not diagnosed. During a supervised restart, physical SPD/HDG/ALT/V/S rotations, the ALT selector, MACH, SPD PUSH and HDG PUSH arrived and were handled without reported action errors. The audio server reported Brave at 70% after the SPD exercise. Display appearance and perceived behavior still require user confirmation.

Added an optional systemd user background launcher with journal capture and restart-on-failure. It was started locally and verified active with exclusive local FCU ownership; this launch does not depend on an open terminal and does not enable login autostart.
