"""Read-only installation diagnostics; no simulated keys or display writes."""
import importlib.util
import os
import shutil
import sys


def diagnose(hid_module, descriptor, output):
    failed = False
    def check(ok, message):
        nonlocal failed
        failed |= not ok
        print(f"{'OK' if ok else 'FAIL'}: {message}", file=output)

    print(f'Platform: {sys.platform}; session: {os.environ.get("XDG_SESSION_TYPE", "unknown")}; '
          f'desktop: {os.environ.get("XDG_CURRENT_DESKTOP", "unknown")}', file=output)
    check(descriptor is not None, 'WINCTRL 32 FCU connected')
    if descriptor is not None:
        handle = hid_module.device()
        try:
            handle.open_path(descriptor['path'])
            check(True, 'FCU HID access')
        except OSError as error:
            check(False, f'FCU HID access: {error}. See README Linux udev setup.')
        finally:
            handle.close()
    if sys.platform == 'linux':
        from .linux_actions import foreground_pid, run_command
        check(importlib.util.find_spec('evdev') is not None, 'Python evdev installed')
        check(os.access('/dev/uinput', os.W_OK), '/dev/uinput writable (see README udev setup)')
        try:
            run_command('pactl', 'info')
            check(True, 'PulseAudio / PipeWire audio connection')
        except RuntimeError as error:
            check(False, str(error))
        pid = foreground_pid()
        if pid:
            print(f'OK: foreground application detected (PID {pid})', file=output)
        else:
            print('NOTE: foreground application unavailable; SPD uses default output volume. '
                  'KDE Wayland: install kdotool; X11: install xdotool.', file=output)
        if 'KDE' in os.environ.get('XDG_CURRENT_DESKTOP', '').upper().split(':'):
            if not (shutil.which('qdbus6') or shutil.which('qdbus')):
                print('NOTE: install qdbus6/qdbus for KDE show-desktop; otherwise Super+D is used.', file=output)
    return 1 if failed else 0
