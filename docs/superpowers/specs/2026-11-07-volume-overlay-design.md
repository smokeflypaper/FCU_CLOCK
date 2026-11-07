# SPD Volume Overlay Design

## Intent

While SPD rotation adjusts the foreground application's volume, its display temporarily shows the resulting whole-number percentage. This gives immediate feedback without permanently replacing the clock.

## Behavior

- A successful application-volume rotation displays `0` through `100` on SPD.
- Every successful rotation restarts a three-second deadline.
- After three seconds without another rotation, SPD returns to the current local hour.
- SPD PUSH/mute does not alter the display.
- Global-volume fallback has no overlay because no reliable application percentage is available.
- All other displays and controls remain unchanged.

## Approaches

- Selected: return the resulting level from the same Core Audio operation and feed it to a timed display overlay. This avoids querying sessions twice and guarantees that the displayed value is the one just written.
- Rejected: independently query volume after every action, because it duplicates endpoint and process discovery.
