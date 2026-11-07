# FCU_CLOCK

Use a **WINCTRL 32 FCU** as a standalone clock and desktop controller — no flight simulator required.

![FCU_CLOCK display and control layout](docs/assets/fcu-clock-controls-2026.png)

## Status

- **Windows 10/11:** supported now
- **Linux:** planned; it will live in this same repository
- **Price:** free and open source
- **License:** GPL-3.0-or-later

The USB display/input protocol is shared across platforms. Operating-system actions such as volume, media keys, window control and brightness need a platform-specific backend, so Windows ships first and Linux support can be added without splitting the project.

## What the displays show

| FCU display | Desktop value |
|---|---|
| SPD | Local hour; temporarily shows application volume (`0–100`) for 3 seconds after turning the SPD knob |
| HDG | Local minute |
| ALT | Local date as `DD MM` |
| V/S | Current outdoor temperature for the configured location |

## Default Windows controls

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
- Windows 10 or Windows 11 for the current release

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

## Mapping controls

The current default mapping is defined in [`src/fcu_desktop/controls.py`](src/fcu_desktop/controls.py):

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

Available Windows actions are implemented in [`src/fcu_desktop/system_actions.py`](src/fcu_desktop/system_actions.py). To change a mapping today, edit `ACTION_MAP`, install the project again with `python -m pip install -e .`, and restart FCU_CLOCK. A user-editable configuration file is a good future improvement.

ALT brightness is handled separately in `DesktopController`, because it sends brightness commands directly back to the FCU rather than invoking an operating-system action.

## Linux plan

Linux will be added here, not as a second project. The clock, weather, HID reports and FCU input decoding can remain shared. Only desktop actions need Linux implementations (for example PipeWire volume, media keys and desktop shortcuts).

## Development

```powershell
python -m pip install -e .
python -m unittest discover -s tests -v
```

## Credits and license

FCU_CLOCK is licensed under **GPL-3.0-or-later**. USB report encoding was derived from the GPL-3.0 project [schenlap/winwing_fcu](https://github.com/schenlap/winwing_fcu).
