"""Control audio sessions belonging to the foreground Windows process."""

import ctypes
from collections.abc import Callable, Iterable
from typing import Any


def _foreground_pid() -> int:
    process_id = ctypes.c_ulong()
    window = ctypes.windll.user32.GetForegroundWindow()
    ctypes.windll.user32.GetWindowThreadProcessId(window, ctypes.byref(process_id))
    return process_id.value


def _audio_sessions() -> Iterable[Any]:
    from pycaw.constants import DEVICE_STATE, EDataFlow
    from pycaw.pycaw import AudioUtilities

    devices = AudioUtilities.GetAllDevices(
        EDataFlow.eRender.value,
        DEVICE_STATE.ACTIVE.value,
    )
    return _sessions_from_devices(devices)


def _sessions_from_devices(
    devices: Iterable[Any],
    *,
    session_factory: Callable[[Any], Any] | None = None,
    query_control: Callable[[Any], Any] | None = None,
) -> list[Any]:
    if session_factory is None or query_control is None:
        from pycaw.pycaw import AudioSession, IAudioSessionControl2

        session_factory = session_factory or AudioSession
        query_control = query_control or (
            lambda control: control.QueryInterface(IAudioSessionControl2)
        )

    sessions = []
    for device in devices:
        manager = device.AudioSessionManager
        if manager is None:
            continue
        enumerator = manager.GetSessionEnumerator()
        for index in range(enumerator.GetCount()):
            control = enumerator.GetSession(index)
            if control is not None:
                sessions.append(session_factory(query_control(control)))
    return sessions


def _process_family(root_pid: int) -> set[int]:
    import psutil

    root = psutil.Process(root_pid)
    return {root_pid, *(child.pid for child in root.children(recursive=True))}


class WindowsAppVolume:
    def __init__(
        self,
        *,
        foreground_pid: Callable[[], int] = _foreground_pid,
        sessions: Callable[[], Iterable[Any]] = _audio_sessions,
        process_ids: Callable[[int], set[int]] = _process_family,
    ) -> None:
        self._foreground_pid = foreground_pid
        self._sessions = sessions
        self._process_ids = process_ids

    def _matching_volumes(self) -> list[Any]:
        process_ids = self._process_ids(self._foreground_pid())
        return [
            session.SimpleAudioVolume
            for session in self._sessions()
            if session.Process is not None and session.Process.pid in process_ids
        ]

    def change(self, step: float) -> float | None:
        try:
            volumes = self._matching_volumes()
            result = None
            for volume in volumes:
                level = max(0.0, min(1.0, volume.GetMasterVolume() + step))
                volume.SetMasterVolume(level, None)
                if result is None:
                    result = level
            return result
        except Exception:
            return None

    def toggle_mute(self) -> bool:
        try:
            volumes = self._matching_volumes()
            if not volumes:
                return False
            muted = not bool(volumes[0].GetMute())
            for volume in volumes:
                volume.SetMute(muted, None)
            return True
        except Exception:
            return False
