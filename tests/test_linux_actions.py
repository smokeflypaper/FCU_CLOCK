"""Linux boundaries use recorded command results, never the real desktop."""
import json
import subprocess
import unittest
from unittest.mock import patch

from fcu_desktop.linux_actions import LinuxAppVolume, LinuxActions, LinuxBackend, foreground_pid, run_command


def stream(index, pid, left=32768, right=32768, mute=False):
    return {'index': index, 'properties': {'application.process.id': str(pid)},
            'volume': {'front-left': {'value': left}, 'front-right': {'value': right}}, 'mute': mute}


class AudioCommands:
    def __init__(self, streams=()):
        self.streams = list(streams)
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)
        if args == ('pactl', '-f', 'json', 'list', 'sink-inputs'):
            return json.dumps(self.streams)
        if args == ('pactl', '-f', 'json', 'list', 'sinks'):
            return json.dumps([dict(stream(1, 0), name='speaker')])
        if args == ('pactl', 'get-default-sink'):
            return 'speaker'
        return ''


class AudioTests(unittest.TestCase):
    def audio(self, commands, pid=100):
        return LinuxAppVolume(run=commands, foreground=lambda: pid, process_ids=lambda p: {p, 101})

    def test_only_foreground_process_and_children_change(self):
        cmd = AudioCommands([stream(1, 100), stream(2, 101), stream(3, 999)])
        self.assertAlmostEqual(self.audio(cmd).change(.05), .55, places=4)
        changes = [c for c in cmd.calls if 'set-sink-input-volume' in c]
        self.assertEqual(changes, [('pactl', 'set-sink-input-volume', '1', '36045', '36045'),
                                   ('pactl', 'set-sink-input-volume', '2', '36045', '36045')])

    def test_clamps_and_preserves_channel_differences(self):
        cmd = AudioCommands([stream(1, 100, 65000, 10000)])
        self.assertEqual(self.audio(cmd).change(.05), 1.0)
        self.assertIn(('pactl', 'set-sink-input-volume', '1', '65536', '13277'), cmd.calls)
        cmd = AudioCommands([stream(1, 100, 1000, 0)])
        self.assertEqual(self.audio(cmd).change(-.05), 0.0)

    def test_no_foreground_uses_named_default_output(self):
        cmd = AudioCommands([stream(1, 999)])
        self.assertAlmostEqual(self.audio(cmd, pid=None).change(.05), .55, places=4)
        self.assertIn(('pactl', 'set-sink-volume', 'speaker', '36045', '36045'), cmd.calls)
        self.assertFalse(any('set-sink-input-volume' in c for c in cmd.calls))

    def test_mute_sets_all_matching_streams_to_same_state(self):
        cmd = AudioCommands([stream(1, 100, mute=True), stream(2, 101)])
        self.assertTrue(self.audio(cmd).toggle_mute())
        self.assertIn(('pactl', 'set-sink-input-mute', '1', '0'), cmd.calls)
        self.assertIn(('pactl', 'set-sink-input-mute', '2', '0'), cmd.calls)

    def test_no_matching_stream_mutes_default_output(self):
        cmd = AudioCommands([stream(1, 999)])
        self.assertTrue(self.audio(cmd).toggle_mute())
        self.assertIn(('pactl', 'set-sink-mute', 'speaker', '1'), cmd.calls)

    def test_malformed_pid_does_not_hide_valid_stream(self):
        cmd = AudioCommands([stream(2, 'unknown'), stream(1, 100)])
        self.assertAlmostEqual(self.audio(cmd).change(.05), .55, places=4)

    def test_failed_application_write_does_not_change_master(self):
        cmd = AudioCommands([stream(1, 100)])
        def run(*args):
            if 'set-sink-input-volume' in args:
                raise RuntimeError('Audio stream vanished')
            return cmd(*args)
        with self.assertRaisesRegex(RuntimeError, 'vanished'):
            self.audio(run).change(.05)
        self.assertFalse(any('set-sink-volume' in c for c in cmd.calls))

    def test_missing_audio_server_is_an_action_error(self):
        with patch('subprocess.run', side_effect=FileNotFoundError):
            with self.assertRaisesRegex(RuntimeError, 'pactl'):
                run_command('pactl', 'info')
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('pactl', 2)):
            with self.assertRaisesRegex(RuntimeError, 'pactl'):
                run_command('pactl', 'info')

    def test_wayland_never_uses_xwayland_active_window(self):
        calls = []
        self.assertIsNone(foreground_pid(env={'XDG_SESSION_TYPE': 'wayland', 'XDG_CURRENT_DESKTOP': 'GNOME'}, run=lambda *a: calls.append(a)))
        self.assertEqual(calls, [])

    def test_kde_uses_kdotool_and_x11_uses_xdotool(self):
        for env, tool in [({'XDG_SESSION_TYPE': 'wayland', 'XDG_CURRENT_DESKTOP': 'KDE'}, 'kdotool'),
                          ({'XDG_SESSION_TYPE': 'x11'}, 'xdotool')]:
            calls = []
            def run(*args):
                calls.append(args)
                return '123\n'
            self.assertEqual(foreground_pid(env=env, run=run), 123)
            self.assertEqual(calls, [(tool, 'getactivewindow', 'getwindowpid')])


class Device:
    def __init__(self):
        self.events = []
        self.closed = False
    def write(self, *event):
        self.events.append(event)
    def syn(self):
        self.events.append(('syn',))
    def close(self):
        self.closed = True


class InputTests(unittest.TestCase):
    def test_hotkey_releases_in_reverse_order_and_syncs(self):
        device = Device()
        backend = LinuxBackend(device=device)
        backend.hotkey(125, 32)
        self.assertEqual(device.events, [(1,125,1),(1,32,1),('syn',),(1,32,0),(1,125,0),('syn',)])
        backend.close()
        self.assertTrue(device.closed)

    def test_scroll_direction_and_key_mapping(self):
        device = Device()
        actions = LinuxActions(backend=LinuxBackend(device=device), app_volume=object(), env={})
        actions.invoke('scroll_down')
        actions.invoke('right')
        self.assertEqual(device.events, [(2,8,-1),('syn',),(1,106,1),('syn',),(1,106,0),('syn',)])

    def test_kde_show_desktop_toggles_actual_state(self):
        calls = []
        def run(*args):
            calls.append(args)
            return 'true' if args[-1] == 'org.kde.KWin.showingDesktop' else ''
        actions = LinuxActions(backend=object(), app_volume=object(), env={'XDG_CURRENT_DESKTOP':'KDE'}, run=run)
        with patch('shutil.which', return_value='/usr/bin/qdbus6'):
            actions.invoke('show_desktop')
        self.assertEqual(calls[-1][-2:], ('org.kde.KWin.showDesktop', 'false'))

    def test_invalid_action_is_explicit(self):
        actions = LinuxActions(backend=object(), app_volume=object())
        with self.assertRaises(ValueError):
            actions.invoke('nonsense')

class DesktopToggleRegressionTests(unittest.TestCase):
    def test_kde_prefers_persistent_minimize_all_over_peek(self):
        calls = []
        def run(*args):
            calls.append(args)
            if args[-1] == 'org.kde.kglobalaccel.Component.shortcutNames':
                return 'Show Desktop\nMinimizeAll\nMinimizeAllActiveScreen'
            return ''
        actions = LinuxActions(backend=object(), app_volume=object(), env={'XDG_CURRENT_DESKTOP':'KDE'}, run=run)
        with patch('shutil.which', return_value='/usr/bin/qdbus6'):
            actions.invoke('show_desktop')
            actions.invoke('show_desktop')
        toggles = [c for c in calls if 'org.kde.kglobalaccel.Component.invokeShortcut' in c]
        self.assertEqual(toggles, [('/usr/bin/qdbus6','org.kde.kglobalaccel','/component/kwin',
                                   'org.kde.kglobalaccel.Component.invokeShortcut','MinimizeAll')]*2)
        self.assertFalse(any('org.kde.KWin.showDesktop' in c for c in calls))
