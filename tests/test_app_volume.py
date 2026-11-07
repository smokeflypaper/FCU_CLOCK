import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fcu_desktop.app_volume import WindowsAppVolume, _sessions_from_devices


class FakeVolume:
    def __init__(self, level=0.5, muted=False):
        self.level = level
        self.muted = muted

    def GetMasterVolume(self):
        return self.level

    def SetMasterVolume(self, level, _context):
        self.level = level

    def GetMute(self):
        return self.muted

    def SetMute(self, muted, _context):
        self.muted = bool(muted)


class FakeProcess:
    def __init__(self, pid):
        self.pid = pid


class FakeSession:
    def __init__(self, pid, level=0.5, muted=False):
        self.Process = FakeProcess(pid) if pid is not None else None
        self.SimpleAudioVolume = FakeVolume(level, muted)


class WindowsAppVolumeTests(unittest.TestCase):
    def adapter(self, sessions, pid=42, process_ids=None):
        return WindowsAppVolume(
            foreground_pid=lambda: pid,
            sessions=lambda: sessions,
            process_ids=process_ids or (lambda root: {root}),
        )

    def test_change_updates_every_matching_session_only(self):
        first = FakeSession(42, 0.30)
        second = FakeSession(42, 0.80)
        other = FakeSession(7, 0.40)

        changed = self.adapter([first, second, other]).change(0.05)

        self.assertAlmostEqual(changed, 0.35)
        self.assertAlmostEqual(first.SimpleAudioVolume.level, 0.35)
        self.assertAlmostEqual(second.SimpleAudioVolume.level, 0.85)
        self.assertAlmostEqual(other.SimpleAudioVolume.level, 0.40)

    def test_change_clamps_volume_to_zero_and_one(self):
        low = FakeSession(42, 0.02)
        high = FakeSession(42, 0.98)
        self.assertEqual(self.adapter([low]).change(-0.05), 0.0)
        self.assertEqual(self.adapter([high]).change(0.05), 1.0)
        self.assertEqual(low.SimpleAudioVolume.level, 0.0)
        self.assertEqual(high.SimpleAudioVolume.level, 1.0)

    def test_no_matching_session_returns_false(self):
        self.assertIsNone(self.adapter([FakeSession(7), FakeSession(None)]).change(0.05))
        self.assertFalse(self.adapter([FakeSession(7)]).toggle_mute())

    def test_toggle_mute_uses_one_consistent_state_for_all_matching_sessions(self):
        first = FakeSession(42, muted=False)
        second = FakeSession(42, muted=True)

        changed = self.adapter([first, second]).toggle_mute()

        self.assertTrue(changed)
        self.assertTrue(first.SimpleAudioVolume.muted)
        self.assertTrue(second.SimpleAudioVolume.muted)

    def test_session_api_failure_returns_false(self):
        def broken_sessions():
            raise RuntimeError("Core Audio unavailable")

        adapter = WindowsAppVolume(foreground_pid=lambda: 42, sessions=broken_sessions)
        self.assertIsNone(adapter.change(0.05))
        self.assertFalse(adapter.toggle_mute())

    def test_foreground_process_descendant_audio_session_is_matched(self):
        audio_child = FakeSession(99, 0.40)
        adapter = self.adapter(
            [audio_child],
            pid=42,
            process_ids=lambda root: {root, 99},
        )

        self.assertAlmostEqual(adapter.change(0.05), 0.45)
        self.assertAlmostEqual(audio_child.SimpleAudioVolume.level, 0.45)

    def test_sessions_are_collected_from_every_render_device(self):
        class Enumerator:
            def __init__(self, controls):
                self.controls = controls

            def GetCount(self):
                return len(self.controls)

            def GetSession(self, index):
                return self.controls[index]

        class Manager:
            def __init__(self, controls):
                self.enumerator = Enumerator(controls)

            def GetSessionEnumerator(self):
                return self.enumerator

        class Device:
            def __init__(self, controls):
                self.AudioSessionManager = Manager(controls)

        first = object()
        non_default = object()
        sessions = _sessions_from_devices(
            [Device([first]), Device([non_default])],
            query_control=lambda control: control,
            session_factory=lambda control: control,
        )

        self.assertEqual(sessions, [first, non_default])


if __name__ == "__main__":
    unittest.main()
