# FCU Desktop design

## Intent

Turn a WINCTRL 32 FCU into a free desktop information and control panel that works without a flight simulator, first on Windows and later on Linux.

## First milestone

- Show the local Windows hour on SPD and minutes on HDG.
- Show day and month on ALT, subject to the FCU segment layout.
- Detect and log every FCU button, encoder direction, and push/pull action.
- Do not launch arbitrary commands yet; action bindings follow after the hardware map is verified.
- Do not modify MobiFlight profiles. MobiFlight and SimAppPro must be closed while FCU Desktop owns the device.

## Architecture

A small Python application separates time formatting, FCU USB protocol encoding, HID transport, and configurable actions. Hardware-independent logic is covered by automated tests. The existing GPL-3.0 `schenlap/winwing_fcu` implementation and its documented VID/PID `4098:BB10` are protocol references; reused code must retain compatible licensing and attribution.

## Approaches considered

- SPAD.neXt: already proven for an FCU clock, but rejected because continued use is paid.
- MobiFlight only: free, but it does not provide Windows local time as a standalone data source.
- Standalone cross-platform HID utility: selected because it is free, simulator-independent, and can later map controls to Windows and Linux actions.

## Constraints

- Windows and Linux are target platforms.
- No simulator dependency.
- No paid runtime dependency.
- Commands are configured explicitly and never derived from remote data.
- Hardware writes begin with a reversible display-only test.

