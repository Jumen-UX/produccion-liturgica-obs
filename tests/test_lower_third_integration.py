"""Pruebas de contrato para Lower Thirds y la salida HTTP local."""

import copy
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import servidor


class LowerThirdIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original = (servidor.ROOT, servidor.DATA, servidor.draft, servidor.live)
        with servidor.LOCK:
            servidor.ROOT = Path(__file__).resolve().parents[1]
            servidor.DATA = Path(self.temp.name) / "configuracion.json"
            servidor.draft = copy.deepcopy(servidor.DEFAULT)
            servidor.live = copy.deepcopy(servidor.DEFAULT)
        self.http = ThreadingHTTPServer(("127.0.0.1", 0), servidor.Handler)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.http.server_port}"

    def tearDown(self):
        self.http.shutdown()
        self.http.server_close()
        self.thread.join(timeout=2)
        with servidor.LOCK:
            servidor.ROOT, servidor.DATA, servidor.draft, servidor.live = self.original
        self.temp.cleanup()

    def get(self, path):
        with urlopen(self.base + path, timeout=3) as response:
            return json.load(response)

    def post(self, command, **kwargs):
        request = Request(
            self.base + "/api/update",
            data=json.dumps({"command": command, **kwargs}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=3) as response:
            return json.load(response)

    def test_draft_publish_clean_restore(self):
        settings = {
            **servidor.LOWER_DEFAULT,
            "template": "modern",
            "enter": "left",
            "exit": "zoom",
            "name": "Nombre de prueba",
            "role": "Panelista",
        }
        self.post("draft", updates={"mode": "lower_third", "lower_third": settings})
        self.assertEqual(self.get("/api/draft")["lower_third"]["template"], "modern")
        self.assertEqual(self.get("/api/state")["mode"], "espera")
        self.assertTrue(servidor.DATA.exists())

        self.post("publish")
        live = self.get("/api/state")
        self.assertEqual(live["mode"], "lower_third")
        self.assertEqual(live["lower_third"]["name"], "Nombre de prueba")
        self.post("clean")
        self.assertFalse(self.get("/api/state")["visible"])
        self.post("restore")
        live = self.get("/api/state")
        self.assertTrue(live["visible"])
        self.assertEqual(live["mode"], "lower_third")

    def test_invalid_style_is_rejected_without_changing_draft(self):
        original = self.get("/api/draft")["lower_third"]
        for bad in (
            {"template": "unsafe"},
            {"accent": "red;position:fixed"},
            {"enter": "javascript:alert(1)"},
            {"unknown": "value"},
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(HTTPError) as error:
                    self.post("draft", updates={"lower_third": bad})
                self.assertEqual(error.exception.code, 400)
                self.assertEqual(self.get("/api/draft")["lower_third"], original)

    def test_limits_and_served_pages(self):
        self.post("draft", updates={"lower_third": {"name": "A" * 200, "duration": 9000, "opacity": 0}})
        saved = self.get("/api/draft")["lower_third"]
        self.assertEqual(len(saved["name"]), 85)
        self.assertEqual(saved["duration"], 2500)
        self.assertEqual(saved["opacity"], 25)
        for page in ("/studio.html", "/dock.html", "/overlay.html"):
            with self.subTest(page=page), urlopen(self.base + page, timeout=3) as response:
                self.assertEqual(response.status, 200)

    def test_dock_quick_text_does_not_reset_saved_animation(self):
        self.post("draft", updates={"lower_third": {"template": "liturgical", "enter": "rise", "exit": "right"}})
        self.post("draft", updates={"mode": "lower_third", "lower_third": {"name": "Nombre desde Dock", "role": "Lector"}})
        current = self.get("/api/draft")["lower_third"]
        self.assertEqual(current["name"], "Nombre desde Dock")
        self.assertEqual(current["template"], "liturgical")
        self.assertEqual(current["enter"], "rise")
        self.assertEqual(current["exit"], "right")


if __name__ == "__main__":
    unittest.main()
