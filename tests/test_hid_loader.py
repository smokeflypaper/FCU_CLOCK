import unittest
from unittest.mock import patch
from fcu_desktop.device import load_hid

class HidLoaderTests(unittest.TestCase):
    def test_linux_prefers_hidraw_to_avoid_claiming_usb_interface(self):
        modules = {'hidraw': object(), 'hid': object()}
        with patch('sys.platform', 'linux'), patch('importlib.import_module', side_effect=modules.__getitem__):
            self.assertIs(load_hid(), modules['hidraw'])

    def test_linux_falls_back_if_distribution_only_provides_hid(self):
        module = object()
        def load(name):
            if name == 'hidraw':
                raise ImportError(name)
            return module
        with patch('sys.platform', 'linux'), patch('importlib.import_module', side_effect=load):
            self.assertIs(load_hid(), module)

    def test_windows_uses_original_hid_module(self):
        modules = {'hid': object()}
        with patch('sys.platform', 'win32'), patch('importlib.import_module', side_effect=modules.__getitem__):
            self.assertIs(load_hid(), modules['hid'])
