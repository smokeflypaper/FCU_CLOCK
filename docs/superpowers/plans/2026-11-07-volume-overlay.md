# SPD Volume Overlay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Temporarily display foreground-application volume percentage on SPD for three seconds after rotation.

**Architecture:** Have the application-volume adapter return the resulting level, pass successful SPD values through the controller to the CLI, and let the CLI own the monotonic overlay deadline and display refresh.

**Tech Stack:** Python 3.11+, pycaw, unittest, HID protocol.

**Spec:** `docs/superpowers/specs/2026-11-07-volume-overlay-design.md`

## Global Constraints

- Mute never changes the overlay.
- Global fallback never shows an application percentage.
- Every successful rotation resets the deadline to three seconds.
- Clock restoration uses current local time.

## Review Focus

- Volume boundaries display exactly `0` and `100`.
- Repeated turns extend the deadline from the latest turn.
- Expiry restores the current hour without disturbing minute/date/temperature.
- Failed app-session update uses global fallback without showing stale percentage.
- Mute does not create or extend an overlay.

---

### Task 1: Return the changed application volume

**Files:**
- Modify: `src/fcu_desktop/app_volume.py`
- Modify: `src/fcu_desktop/system_actions.py`
- Modify: `tests/test_app_volume.py`
- Modify: `tests/test_system_actions.py`

**Interfaces:**
- Produces: `WindowsAppVolume.change(step: float) -> float | None` and `WindowsActions.invoke(action: str) -> float | None`; volume actions return a `0.0..1.0` result only when the application session was updated.

- [ ] Write failing tests for returned levels, multi-session behavior, fallback, and mute returning no level.
- [ ] Run focused tests and confirm RED.
- [ ] Implement the minimal return-value changes while preserving fallback.
- [ ] Run focused tests and confirm GREEN.
- [ ] Commit.

### Task 2: Timed SPD display overlay

**Files:**
- Modify: `src/fcu_desktop/controls.py`
- Modify: `src/fcu_desktop/cli.py`
- Modify: `src/fcu_desktop/protocol.py` if a focused SPD-only write is required.
- Modify: `tests/test_controls.py`
- Modify: `tests/test_cli.py`

**Interfaces:**
- Consumes: `WindowsActions.invoke(action: str) -> float | None`.
- Produces: a successful SPD rotation starts or refreshes a three-second percentage overlay; expiry restores clock output.

- [ ] Write failing tests for percent formatting, deadline refresh, expiry, mute, and fallback.
- [ ] Run focused tests and confirm RED.
- [ ] Implement the overlay with an injected monotonic clock for deterministic tests.
- [ ] Run focused tests and confirm GREEN.
- [ ] Run the full suite and confirm all tests pass.
- [ ] Restart exactly one FCU Desktop instance and physically verify Brave at `0`, an intermediate value, and expiry.
- [ ] Commit.
