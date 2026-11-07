"""Select desktop integration without changing the Windows implementation."""
import sys


class NoActions:
    def invoke(self, action):
        return None


def create_actions():
    if sys.platform == 'win32':
        from .system_actions import WindowsActions
        return WindowsActions()
    if sys.platform == 'linux':
        from .linux_actions import LinuxActions
        return LinuxActions()
    raise RuntimeError(f'Unsupported desktop platform: {sys.platform}. Use clock --no-controls.')
