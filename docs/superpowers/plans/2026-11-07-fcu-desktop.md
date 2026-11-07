# FCU Desktop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a free standalone utility that shows local time/date on a WINCTRL 32 FCU and exposes its controls for later bindings.

**Architecture:** Pure formatting and report-codec modules sit behind a small HID transport interface, allowing tests without hardware. A CLI first runs discovery, then a conservative display/input diagnostic.

**Tech Stack:** Python 3.11+, standard library, `hidapi` only for real hardware, `unittest`.

**Spec:** `docs/superpowers/specs/2026-11-07-fcu-desktop-design.md`

## Global Constraints

- Target Windows and Linux without simulator or paid dependencies.
- Never run MobiFlight or SimAppPro concurrently with this application.
- Preserve GPL-3.0 attribution for protocol material derived from `schenlap/winwing_fcu`.

## Review Focus

- Single-digit local hour/minute/day/month retain leading zeroes.
- Midnight and month boundaries produce valid fields.
- Missing FCU produces a clear error without a crash loop.
- Unknown input bits are logged rather than executed.
- Transport cleanup blanks or safely releases the device on exit.

---

### Task 1: Time and date display model

**Files:** Create `tests/test_clock.py`, `src/fcu_desktop/clock.py`, package files.

- [ ] Write tests for `ClockFields.from_datetime()` including `07:03` and `7 November`.
- [ ] Run tests and verify failure because the package is missing.
- [ ] Implement the immutable numeric display fields.
- [ ] Run the complete test suite.

### Task 2: FCU display report codec

**Files:** Create `tests/test_protocol.py`, `src/fcu_desktop/protocol.py`.

- [ ] Add golden-vector tests based on the documented FCU protocol.
- [ ] Verify the tests fail before implementation.
- [ ] Implement only SPD, HDG, ALT and V/S report generation plus brightness.
- [ ] Run the complete test suite.

### Task 3: HID discovery and input decoding

**Files:** Create `tests/test_inputs.py`, `src/fcu_desktop/device.py`, `src/fcu_desktop/inputs.py`.

- [ ] Test VID/PID selection, press/release transitions, and known FCU control IDs.
- [ ] Verify red, implement minimal discovery/decoding, then verify green.
- [ ] Log unknown bits safely.

### Task 4: Diagnostic CLI and live verification

**Files:** Create `src/fcu_desktop/cli.py`, `pyproject.toml`, `README.md`.

- [ ] Test CLI dependency injection and clean missing-device error.
- [ ] Implement `discover` and `clock` commands.
- [ ] Install the free HID dependency and run all automated tests.
- [ ] With MobiFlight and SimAppPro closed, run discovery and a short live clock test.

