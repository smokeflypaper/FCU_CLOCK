# FCU_CLOCK

Use a **WINCTRL 32 FCU** as a standalone clock and desktop controller.

![FCU_CLOCK display and control layout](docs/assets/fcu-clock-controls-2026.png)

## Status

- **Windows 10/11:** and **Linux:** supported
- **License:** GPL-3.0-or-later

The USB display/input protocol is shared across platforms.

## What the displays show

| FCU display | Desktop value |
|---|---|
| SPD | Local hour; temporarily shows application volume (`0–100`) for 3 seconds after turning the SPD knob |
| HDG | Local minute |
| ALT | Local date as `DD MM` |
| V/S | Current outdoor temperature for the configured location |

## Default controls

| FCU control | Action |
|---|---|
| SPD/MACH button (far left) | Show the desktop on all monitors; press again to restore windows |
| SPD knob | Change the foreground application's volume |
| SPD PUSH | Mute/unmute the foreground application |
| HDG knob | Left/Right arrow, for example seek in YouTube |
| HDG PUSH | Media Play/Pause |
| ALT knob, selector at `100` | Display brightness |
| ALT knob, selector at `1000` | Button and encoder backlight brightness |
| V/S knob | Mouse wheel up/down |
| V/S PUSH | Home key |

## Requirements

- WINCTRL 32 FCU connected by USB
- Python 3.11 or newer
- Windows 10 or Windows 11 / linux

> [!IMPORTANT]
> Close MobiFlight and SimAppPro before starting FCU_CLOCK. Only one program can control the FCU HID device at a time.

## Install and run on Windows

```powershell
git clone https://github.com/smokeflypaper/FCU_CLOCK.git
cd FCU_CLOCK
python -m pip install -e .
fcu-desktop discover
fcu-desktop clock
```

Use `Ctrl+C` to stop it. Run `fcu-desktop clock --once` for a single display update and hardware check.

## Customize FCU_CLOCK

FCU_CLOCK is intentionally small and easy to modify. At the moment mappings are edited in Python; there is no graphical configuration editor yet. Make a copy of the project or create a Git branch before experimenting, then restart FCU_CLOCK after every change.

### 1. Map a control to an existing action

The default mapping lives in [`src/fcu_desktop/controls.py`](src/fcu_desktop/controls.py):

```python
ACTION_MAP = {
    "MACH": "show_desktop",
    "SPD DEC": "volume_down",
    "SPD INC": "volume_up",
    "SPD PUSH": "volume_mute",
    "HDG DEC": "left",
    "HDG INC": "right",
    "HDG PUSH": "media_play_pause",
    "VS DEC": "scroll_down",
    "VS INC": "scroll_up",
    "VS PUSH": "home",
}
```

The action names already available on Windows are:

| Action name | Result |
|---|---|
| `show_desktop` | Press `Win+D` |
| `volume_down`, `volume_up` | Change the foreground application's volume |
| `volume_mute` | Mute/unmute the foreground application |
| `media_play_pause` | Send the global media Play/Pause key |
| `left`, `right`, `home` | Send that keyboard key |
| `scroll_up`, `scroll_down` | Send one mouse-wheel step |

For example, this makes `AP1` Play/Pause and `AP2` show the desktop:

```python
ACTION_MAP = {
    # Keep any mappings you still want here.
    "AP1": "media_play_pause",
    "AP2": "show_desktop",
}
```

Every physical input name that can be used on the left side is listed in [`src/fcu_desktop/inputs.py`](src/fcu_desktop/inputs.py):

```text
MACH, LOC, TRK, AP1, AP2, A/THR, EXPED, METRIC, APPR
SPD DEC, SPD INC, SPD PUSH, SPD PULL
HDG DEC, HDG INC, HDG PUSH, HDG PULL
ALT DEC, ALT INC, ALT PUSH, ALT PULL
VS DEC, VS INC, VS PUSH, VS PULL
ALT 100, ALT 1000
```

`DEC` and `INC` mean turning an encoder left or right. `PUSH` and `PULL` are the two encoder button directions.

> [!NOTE]
> `ALT DEC`, `ALT INC`, `ALT 100` and `ALT 1000` are currently intercepted by `DesktopController` for FCU brightness. They cannot be reassigned only by changing `ACTION_MAP`; remove or modify that brightness block in `controls.py` first.

### 2. Add another keyboard key

Windows virtual-key codes are defined in [`src/fcu_desktop/system_actions.py`](src/fcu_desktop/system_actions.py). Add a new entry to `VIRTUAL_KEYS`, then use its name in `ACTION_MAP`.

This example turns `LOC` into the otherwise rarely used `F13` key, which is useful for OBS, Discord, AutoHotkey or another application with its own shortcut settings:

```python
# system_actions.py
VIRTUAL_KEYS = {
    # Existing entries stay here.
    "f13": 0x7C,
}
```

```python
# controls.py
ACTION_MAP = {
    "LOC": "f13",
}
```

Useful virtual-key codes include `F13`–`F24` (`0x7C`–`0x87`), `Page Up` (`0x21`), `Page Down` (`0x22`), `End` (`0x23`) and `Space` (`0x20`). Microsoft maintains the full [Windows virtual-key code list](https://learn.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes).

### 3. Add a keyboard shortcut

Add a named branch inside `WindowsActions.invoke()` before its final `else` block. This example opens File Explorer with `Win+E`:

```python
# system_actions.py, inside WindowsActions.invoke()
elif action == "open_explorer":
    self._backend.hotkey(0x5B, 0x45)  # Win + E
```

Then assign it to a control:

```python
# controls.py
ACTION_MAP = {
    "AP1": "open_explorer",
}
```

### 4. Launch an application

First add the standard-library import at the top of `system_actions.py`:

```python
import subprocess
```

Then add an action inside `WindowsActions.invoke()`:

```python
elif action == "open_notepad":
    subprocess.Popen(["notepad.exe"])
```

Map it to any unused button:

```python
ACTION_MAP = {
    "AP2": "open_notepad",
}
```

For another application, replace `notepad.exe` with its executable path. Always use a list of arguments rather than building one long command string.

### 5. Run your own PowerShell script

Add another action to `WindowsActions.invoke()`:

```python
elif action == "run_my_script":
    subprocess.Popen(
        [
            "powershell.exe",
            "-NoProfile",
            "-File",
            r"C:\Tools\my-script.ps1",
        ]
    )
```

Then map it, for example, to `A/THR`:

```python
ACTION_MAP = {
    "A/THR": "run_my_script",
}
```

Only run scripts you wrote or trust. Do not commit personal paths, usernames, coordinates, tokens or passwords to a public repository.

### 6. Configure weather for your location

FCU_CLOCK deliberately does not contain a built-in location. Set your latitude and longitude before launching it:

```powershell
$env:FCU_CLOCK_LATITUDE = "50.0755"
$env:FCU_CLOCK_LONGITUDE = "14.4378"
fcu-desktop clock
```

Those example coordinates point to Prague. For a permanent private launcher, put the two `set` commands in your local `.cmd` file, but do not commit that launcher if it contains your exact location.

```bat
@echo off
set "FCU_CLOCK_LATITUDE=50.0755"
set "FCU_CLOCK_LONGITUDE=14.4378"
fcu-desktop clock
```

### More customization ideas

| FCU control idea | Possible desktop use |
|---|---|
| `LOC` / `APPR` | Previous/next browser tab or media track |
| `AP1` / `AP2` | Launch two favorite applications |
| `A/THR` | Run a microphone mute script |
| `EXPED` | Open Task Manager or Windows Task View |
| `METRIC` | Switch audio device using your own script |
| Encoder `PULL` actions | Undo/redo, copy/paste, fullscreen or screenshot |
| Unused encoder rotation | Zoom, brush size, timeline scrubbing or application-specific shortcuts |
| `F13`–`F24` mappings | Trigger OBS scenes, Discord controls or automation software without conflicting with normal keys |

The operating-system actions are implemented in [`src/fcu_desktop/system_actions.py`](src/fcu_desktop/system_actions.py). Hardware input names and transitions are decoded in [`src/fcu_desktop/inputs.py`](src/fcu_desktop/inputs.py), while mapping and FCU brightness behavior live in [`src/fcu_desktop/controls.py`](src/fcu_desktop/controls.py).

ALT brightness is handled separately in `DesktopController`, because it sends brightness commands directly back to the FCU rather than invoking an operating-system action.

## Development

```powershell
python -m pip install -e .
python -m unittest discover -s tests -v
```

## Credits and license

FCU_CLOCK is licensed under **GPL-3.0-or-later**. USB report encoding was derived from the GPL-3.0 project [schenlap/winwing_fcu](https://github.com/schenlap/winwing_fcu).
