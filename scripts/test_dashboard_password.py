import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from dashboard_password import load_password


class PasswordTests(unittest.TestCase):
    def test_environment_precedes_file(self):
        with patch.dict(os.environ, {'ABS_DASHBOARD_PASSWORD': 'test-env'}, clear=True):
            self.assertEqual(load_password(), 'test-env')

    def test_private_file_and_unsafe_permissions(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'password'
            path.write_text('test-local\n')
            path.chmod(0o600)
            with patch.dict(os.environ, {}, clear=True), patch('dashboard_password.password_path', return_value=path):
                self.assertEqual(load_password(), 'test-local')
                path.chmod(0o644)
                with self.assertRaises(RuntimeError):
                    load_password()

    def test_missing_empty_symlink_and_custom_environment(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'password'
            with patch.dict(os.environ, {}, clear=True), patch('dashboard_password.password_path', return_value=path):
                with self.assertRaises(RuntimeError):
                    load_password()
                path.write_text('')
                path.chmod(0o600)
                with self.assertRaises(RuntimeError):
                    load_password()
                target = Path(temp) / 'target'
                target.write_text('test-local')
                target.chmod(0o600)
                path.unlink()
                path.symlink_to(target)
                with self.assertRaises(RuntimeError):
                    load_password()
                with self.assertRaises(RuntimeError):
                    load_password('CUSTOM_PASSWORD')


if __name__ == '__main__':
    unittest.main()
