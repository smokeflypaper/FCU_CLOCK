import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


@unittest.skipUnless(shutil.which('bash') and os.name == 'posix', 'Linux launcher')
class BackgroundLauncherTests(unittest.TestCase):
    def test_background_launch_preserves_paths_arguments_and_desktop_environment(self):
        script = Path(__file__).resolve().parents[1] / 'scripts' / 'run-linux-background.sh'
        self.assertTrue(script.exists(), 'background launcher is missing')
        with tempfile.TemporaryDirectory(prefix='fcu launch ') as temp:
            root = Path(temp)
            (root / 'scripts').mkdir()
            copy = root / 'scripts' / script.name
            shutil.copyfile(script, copy)
            runner = root / 'systemd-run'
            runner.write_text('#!/usr/bin/env python3\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\n')
            runner.chmod(0o755)
            env = dict(os.environ, PATH=str(root) + os.pathsep + os.environ['PATH'],
                       XDG_CURRENT_DESKTOP='KDE', WAYLAND_DISPLAY='wayland-test',
                       FCU_CLOCK_LATITUDE='50.0')
            result = subprocess.run(['bash', str(copy), 'clock', '--no-controls'],
                                    env=env, capture_output=True, text=True, check=True)
            args = json.loads(result.stdout)
            self.assertEqual(args[-3:], [str(root / 'scripts' / 'run-linux.sh'), 'clock', '--no-controls'])
            self.assertIn('--setenv=WAYLAND_DISPLAY=wayland-test', args)
            self.assertIn('--setenv=FCU_CLOCK_LATITUDE=50.0', args)
            self.assertIn('--property=Restart=on-failure', args)

    def test_foreground_launcher_loads_persistent_private_weather_config(self):
        script = Path(__file__).resolve().parents[1] / 'scripts' / 'run-linux.sh'
        with tempfile.TemporaryDirectory(prefix='fcu weather ') as temp:
            root = Path(temp)
            (root / 'scripts').mkdir()
            (root / '.venv/bin').mkdir(parents=True)
            config = root / 'config/fcu-clock'
            config.mkdir(parents=True)
            (config / 'config.env').write_text('FCU_CLOCK_LATITUDE=50.0\nFCU_CLOCK_LONGITUDE=15.0\n')
            copy = root / 'scripts/run-linux.sh'
            shutil.copyfile(script, copy)
            runner = root / '.venv/bin/fcu-desktop'
            runner.write_text('#!/usr/bin/env python3\nimport os,json\nprint(json.dumps([os.getenv("FCU_CLOCK_LATITUDE"),os.getenv("FCU_CLOCK_LONGITUDE")]))\n')
            runner.chmod(0o755)
            env = dict(os.environ, XDG_CONFIG_HOME=str(root / 'config'))
            env.pop('FCU_CLOCK_LATITUDE',None)
            env.pop('FCU_CLOCK_LONGITUDE',None)
            result = subprocess.run(['bash', str(copy),'clock','--once'],env=env,capture_output=True,text=True,check=True)
            self.assertEqual(json.loads(result.stdout),['50.0','15.0'])
