# Active Application Volume Design

## Intent

SPD must control audible volume reliably when Windows routes Brave independently of the default device. Rotation changes the foreground application's audio-session volume; PUSH toggles that session's mute state.

## Constraints

- Keep every existing FCU mapping except SPD volume behavior unchanged.
- On Windows, target the foreground process's Core Audio sessions.
- If the foreground process has no audio session, fall back to the existing global media-volume keys.
- Add only free Python libraries (`pycaw` and `comtypes`), not a separately running program.
- Keep non-Windows imports functional so a Linux backend can be added later.

## Approaches

- Selected: Windows Core Audio application sessions. This directly controls the Brave slider visible in Volume Mixer and works for other foreground audio applications.
- Rejected: YouTube keyboard shortcuts, because they depend on browser focus and only work on YouTube.
- Rejected: retain global volume and repair routing, because the user's Brave session demonstrably responds to its application slider but not the device master control.

## Behavior

Volume changes use a small fixed step and clamp to 0–100%. Mute toggles all audio sessions belonging to the foreground process. If no matching session exists or session access fails, the existing global Windows action is used.
