import unittest
from unittest.mock import patch
from fcu_desktop.platform_actions import create_actions
from fcu_desktop.system_actions import WindowsActions
from fcu_desktop.linux_actions import LinuxActions

class PlatformTests(unittest.TestCase):
    def test_windows_routes_to_original_backend(self):
        with patch('sys.platform', 'win32'):
            self.assertIsInstance(create_actions(), WindowsActions)

    def test_linux_routes_without_loading_windows_audio(self):
        with patch('sys.platform', 'linux'):
            self.assertIsInstance(create_actions(), LinuxActions)

    def test_unsupported_platform_has_explicit_error(self):
        with patch('sys.platform', 'darwin'):
            with self.assertRaisesRegex(RuntimeError, 'Unsupported'):
                create_actions()
