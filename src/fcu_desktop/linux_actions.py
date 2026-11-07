"""Linux desktop actions for Wayland/X11 and PulseAudio-compatible servers.

No Linux-only imports at module scope: Windows can import and test dispatch.
"""

import json
import os
import shutil
import subprocess
import time


KEYS = {'left': 105, 'right': 106, 'home': 102, 'media_play_pause': 164}
MODIFIERS = {'ctrl': 29, 'alt': 56, 'shift': 42, 'super': 125, 'd': 32}


def run_command(*args):
    try:
        return subprocess.run(args, check=True, capture_output=True, text=True,
                              timeout=2).stdout.strip()
    except (OSError, subprocess.SubprocessError) as error:
        detail = getattr(error, 'stderr', None) or str(error)
        raise RuntimeError(f"{args[0]} failed: {detail.strip()}") from error


def foreground_pid(*, env=None, run=run_command):
    env = os.environ if env is None else env
    if env.get('XDG_SESSION_TYPE') == 'x11':
        tool = 'xdotool'
    elif 'KDE' in env.get('XDG_CURRENT_DESKTOP', '').upper().split(':'):
        tool = 'kdotool'
    else:
        return None
    try:
        pid = int(run(tool, 'getactivewindow', 'getwindowpid'))
        return pid if pid > 0 else None
    except (RuntimeError, ValueError):
        return None


def process_family(pid):
    import psutil
    try:
        return {pid, *(child.pid for child in psutil.Process(pid).children(recursive=True))}
    except psutil.Error:
        return {pid}


class LinuxAppVolume:
    def __init__(self, *, run=run_command, foreground=foreground_pid,
                 process_ids=process_family):
        self.run = run
        self.foreground = foreground
        self.process_ids = process_ids

    def _targets(self):
        pid = self.foreground()
        if pid:
            pids = self.process_ids(pid)
            streams = json.loads(self.run('pactl', '-f', 'json', 'list', 'sink-inputs'))
            matches = []
            for stream in streams:
                try:
                    stream_pid = int(stream.get('properties', {}).get('application.process.id', ''))
                except (TypeError, ValueError):
                    continue
                if stream_pid in pids:
                    matches.append((str(stream['index']), stream))
            if matches:
                return 'sink-input', matches
        # Resolve the name once so an output switch cannot redirect the write.
        name = self.run('pactl', 'get-default-sink')
        sinks = json.loads(self.run('pactl', '-f', 'json', 'list', 'sinks'))
        for sink in sinks:
            if sink.get('name') == name:
                return 'sink', [(name, sink)]
        raise RuntimeError('No default audio output. Check pactl info / PipeWire or PulseAudio.')

    def change(self, step):
        kind, targets = self._targets()
        result = None
        for index, stream in targets:
            channels = stream.get('volume', {})
            if not channels:
                raise RuntimeError('Audio server returned no volume channels.')
            levels = [max(0, min(65536, round(channel['value'] + step * 65536)))
                      for channel in channels.values()]
            self.run('pactl', f'set-{kind}-volume', index, *(str(level) for level in levels))
            if result is None:
                result = max(levels) / 65536
        return result

    def toggle_mute(self):
        kind, targets = self._targets()
        muted = not targets[0][1]['mute']
        for index, _ in targets:
            self.run('pactl', f'set-{kind}-mute', index, str(int(muted)))
        return True


class LinuxBackend:
    def __init__(self, *, device=None):
        if device is None:
            from evdev import UInput, ecodes
            try:
                device = UInput({ecodes.EV_KEY: sorted(set(KEYS.values()) | set(MODIFIERS.values()) | {272}),
                                 ecodes.EV_REL: [ecodes.REL_X, ecodes.REL_Y, ecodes.REL_WHEEL]},
                                name='FCU CLOCK desktop controls')
            except OSError as error:
                raise RuntimeError('Cannot open /dev/uinput. Install packaging/linux/70-fcu-clock.rules '
                                   'as described in README.md, then log in again.') from error
            # Allow the compositor to discover the new keyboard before its first key.
            time.sleep(0.3)
        self.device = device

    def hotkey(self, *keys):
        pressed = []
        try:
            for key in keys:
                self.device.write(1, key, 1)
                pressed.append(key)
            self.device.syn()
        finally:
            for key in reversed(pressed):
                self.device.write(1, key, 0)
            self.device.syn()

    def wheel(self, delta):
        self.device.write(2, 8, delta)
        self.device.syn()

    def close(self):
        self.device.close()


class LinuxActions:
    def __init__(self, backend=None, *, app_volume=None, env=None, run=run_command):
        self._backend = backend
        self._app_volume = app_volume if app_volume is not None else LinuxAppVolume()
        self.env = os.environ if env is None else env
        self.run = run

    def prepare(self):
        if self._backend is None:
            self._backend = LinuxBackend()

    def invoke(self, action):
        if action == 'volume_down':
            return self._app_volume.change(-.05)
        if action == 'volume_up':
            return self._app_volume.change(.05)
        if action == 'volume_mute':
            self._app_volume.toggle_mute()
            return None
        if action == 'show_desktop':
            if 'KDE' in self.env.get('XDG_CURRENT_DESKTOP', '').upper().split(':'):
                qdbus = shutil.which('qdbus6') or shutil.which('qdbus')
                if qdbus:
                    shortcuts = self.run(qdbus, 'org.kde.kglobalaccel', '/component/kwin',
                                         'org.kde.kglobalaccel.Component.shortcutNames').splitlines()
                    if 'MinimizeAll' in shortcuts:
                        # KDE's peek-at-desktop mode can immediately dismiss itself
                        # (for example with focus-following/desktop effects). The
                        # built-in script remembers exactly which windows to restore.
                        self.run(qdbus, 'org.kde.kglobalaccel', '/component/kwin',
                                 'org.kde.kglobalaccel.Component.invokeShortcut', 'MinimizeAll')
                        return None
                    state = self.run(qdbus, 'org.kde.KWin', '/KWin', 'org.kde.KWin.showingDesktop')
                    self.run(qdbus, 'org.kde.KWin', '/KWin', 'org.kde.KWin.showDesktop',
                             'false' if state == 'true' else 'true')
                    return None
            shortcut = self.env.get('FCU_CLOCK_DESKTOP_SHORTCUT', 'super+d').lower().split('+')
            try:
                keys = [MODIFIERS[key] for key in shortcut]
            except KeyError as error:
                raise ValueError('FCU_CLOCK_DESKTOP_SHORTCUT: use super+d or ctrl+alt+d.') from error
            self.prepare()
            self._backend.hotkey(*keys)
        elif action in ('scroll_up', 'scroll_down'):
            self.prepare()
            self._backend.wheel(1 if action == 'scroll_up' else -1)
        elif action in KEYS:
            self.prepare()
            self._backend.hotkey(KEYS[action])
        else:
            raise ValueError(f'Unknown Linux action: {action}')
        return None

    def close(self):
        if self._backend is not None:
            self._backend.close()
            self._backend = None
