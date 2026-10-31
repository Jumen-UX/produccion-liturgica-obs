"""Pruebas del inicio directo sin lanzar ventanas ni navegadores reales."""
import io
import json
import unittest
from unittest.mock import patch
import launcher


class StartupTests(unittest.TestCase):
    def test_existing_panel_requires_expected_api(self):
        response = io.BytesIO(json.dumps({"parish_name": "Prueba", "mode": "espera"}).encode())
        with patch.object(launcher, "urlopen", return_value=response):
            self.assertTrue(launcher.existing_panel_available())

    def test_foreign_server_is_not_accepted(self):
        response = io.BytesIO(b'{"service":"otro"}')
        with patch.object(launcher, "urlopen", return_value=response):
            self.assertFalse(launcher.existing_panel_available())

    def test_second_instance_opens_existing_panel_only(self):
        with patch.object(launcher, "acquire_single_instance", return_value=(None, False)), \
             patch.object(launcher, "existing_panel_available", return_value=True), \
             patch.object(launcher.webbrowser, "open") as browser, \
             patch.object(launcher, "Launcher") as application:
            launcher.main()
            browser.assert_called_once_with(launcher.PANEL)
            application.assert_not_called()


if __name__ == "__main__":
    unittest.main()
