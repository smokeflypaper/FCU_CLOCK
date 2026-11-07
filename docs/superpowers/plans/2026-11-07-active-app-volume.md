# Active Application Volume Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make SPD rotation and PUSH control the foreground Windows application's audio session, with global-volume fallback.

**Architecture:** Add a focused Core Audio adapter that discovers sessions for the foreground PID and changes or mutes them. `WindowsBackend` delegates SPD actions to it and retains virtual-key fallback when no session is controllable.

**Tech Stack:** Python 3.13, pycaw, comtypes, unittest, Windows Core Audio

**Spec:** `docs/superpowers/specs/2026-11-07-active-app-volume-design.md`

## Global Constraints

- Existing non-SPD FCU mappings remain unchanged.
- `pycaw` and `comtypes` are Windows-only dependencies.
- Failure to find or access an application session must preserve global volume behavior.
- Non-Windows module import must remain valid.

## Review Focus

- Foreground process with several audio sessions: update every matching session.
- Foreground process with no session: use the existing global key action.
- Session API exception: fall back without terminating FCU Desktop.
- Volume at 0% or 100%: clamp rather than overflow.
- Mute with several sessions: apply the same toggled state to all matches.

---

### Task 1: Foreground application audio adapter

**Files:**
- Create: `src/fcu_desktop/app_volume.py`
- Create: `tests/test_app_volume.py`
- Modify: `pyproject.toml`

**Interfaces:**
- Produces: `WindowsAppVolume.change(step: float) -> bool` and `WindowsAppVolume.toggle_mute() -> bool`; `True` means at least one foreground-process session was updated.

- [ ] Write failing tests for multiple matching sessions, no matching session, clamping, consistent mute, and API failure.
- [ ] Run `python -m unittest tests.test_app_volume -v` and confirm failures are caused by the missing adapter.
- [ ] Implement the adapter with injected foreground-PID and session providers, loading pycaw lazily by default.
- [ ] Add Windows-only `pycaw` and `comtypes` dependencies to `pyproject.toml`.
- [ ] Run `python -m unittest tests.test_app_volume -v` and confirm all adapter tests pass.
- [ ] Commit the adapter and tests.

### Task 2: Route SPD through the adapter with fallback

**Files:**
- Modify: `src/fcu_desktop/system_actions.py`
- Modify: `tests/test_system_actions.py`

**Interfaces:**
- Consumes: `WindowsAppVolume.change(step: float) -> bool`, `WindowsAppVolume.toggle_mute() -> bool`.
- Produces: unchanged `WindowsBackend.key_press(virtual_key: int) -> None` behavior for non-volume keys and fallback.

- [ ] Write failing tests proving volume up/down and mute use the application adapter, while no-session and exception cases use existing virtual keys.
- [ ] Run `python -m unittest tests.test_system_actions -v` and confirm the new routing tests fail.
- [ ] Route the three SPD actions through `WindowsAppVolume` using a 0.05 step, preserving key fallback.
- [ ] Run `python -m unittest tests.test_system_actions -v` and confirm all routing tests pass.
- [ ] Run `python -m unittest discover -v` and confirm the complete suite passes.
- [ ] Install the editable project dependencies, restart exactly one FCU Desktop instance, and physically verify Brave volume and mute.
- [ ] Commit the integration.
