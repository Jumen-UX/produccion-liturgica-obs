"""El editor no publica; el Dock lanza una copia congelada de la composición."""
import copy
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import servidor
from layered_composition import starter_composition
from production_library import ProductionLibrary


class ComposerRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.original = (servidor.PRODUCTIONS, servidor.draft, servidor.live,
                         servidor.DATA, servidor.last_visible_state)
        with servidor.LOCK:
            servidor.DATA = Path(self.temp.name) / "configuracion.json"
            servidor.PRODUCTIONS = ProductionLibrary(Path(self.temp.name) / "producciones.json")
            servidor.draft = copy.deepcopy(servidor.DEFAULT)
            servidor.live = copy.deepcopy(servidor.DEFAULT)
            servidor.last_visible_state = None
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), servidor.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        with servidor.LOCK:
            (servidor.PRODUCTIONS, servidor.draft, servidor.live,
             servidor.DATA, servidor.last_visible_state) = self.original

    def request(self, path, body=None):
        request = Request(self.base + path, data=json.dumps(body).encode("utf-8") if body else None,
                          headers={"Content-Type": "application/json"} if body else {})
        with urlopen(request, timeout=3) as response:
            return json.load(response)

    def test_preparation_launch_restore_and_snapshot(self):
        with urlopen(self.base + "/compositor.html", timeout=3) as response:
            self.assertEqual(response.status, 200)
        self.assertEqual(self.request("/api/composition-starter"), starter_composition())
        before = self.request("/api/state")
        original_draft = self.request("/api/draft")
        comp = starter_composition()
        comp["minutes"] = 12
        result = self.request("/api/productions", {"action": "add", "item": {
            "type": "pantalla", "name": "Espera especial", "data": comp}})
        self.assertEqual(self.request("/api/state"), before)
        self.assertEqual(self.request("/api/draft"), original_draft)
        production = result["productions"][0]
        item = production["items"][-1]
        launched = self.request("/api/update", {"command": "library_launch",
            "production_id": production["id"], "item_id": item["id"]})
        self.assertEqual(launched["live"]["mode"], "espera")
        self.assertEqual(launched["live"]["timer_minutes"], 12)
        self.assertEqual(launched["live"]["remaining"], 720)
        self.assertFalse(launched["live"]["running"])
        self.assertEqual(launched["live"]["composition"]["layers"][1]["text"],
                         "Bienvenidos a nuestra celebración")
        comp["layers"][1]["text"] = "Cambios sin lanzar"
        self.request("/api/productions", {"action": "update", "item_id": item["id"],
            "item": {"name": "Espera especial", "data": comp}})
        self.assertNotEqual(self.request("/api/state")["composition"]["layers"][1]["text"],
                            "Cambios sin lanzar")
        self.request("/api/update", {"command": "clean"})
        self.assertFalse(self.request("/api/state")["visible"])
        restored = self.request("/api/update", {"command": "restore"})["live"]
        self.assertEqual(restored["composition"]["layers"][1]["text"],
                         "Bienvenidos a nuestra celebración")
        self.request("/api/update", {"command": "timer_start"})
        self.assertTrue(self.request("/api/state")["running"])
        self.request("/api/update", {"command": "launch", "mode": "espera"})
        self.assertIsNone(self.request("/api/state")["composition"])

    def test_invalid_composition_cannot_be_launched_or_saved(self):
        comp = starter_composition()
        comp["layers"][0]["asset"] = "https://remote.example/bg.png"
        with self.assertRaises(HTTPError) as ctx:
            self.request("/api/productions", {"action": "add", "item": {
                "type": "pantalla", "name": "Riesgo", "data": comp}})
        self.assertEqual(ctx.exception.code, 400)

    def test_timer_shortcuts_extend_remaining_without_stopping_or_editing_draft(self):
        self.request('/api/update', {'command': 'timer_set', 'minutes': 12})
        self.assertEqual(self.request('/api/update', {'command': 'timer_adjust', 'minutes': 1})['live']['remaining'], 780)
        self.assertEqual(self.request('/api/update', {'command': 'timer_adjust', 'minutes': 5})['live']['remaining'], 1080)
        self.request('/api/update', {'command': 'timer_start'})
        before = self.request('/api/state')
        after = self.request('/api/update', {'command': 'timer_adjust', 'minutes': 10})['live']
        self.assertTrue(after['running'])
        self.assertEqual(after['timer_minutes'], 28)
        self.assertGreaterEqual(after['remaining']-before['remaining'], 598)
        self.assertLessEqual(after['remaining']-before['remaining'], 600)
        self.assertEqual(self.request('/api/draft')['timer_minutes'], 12)
        self.request('/api/update', {'command': 'timer_pause'})
        self.request('/api/update', {'command': 'timer_adjust', 'minutes': 15})
        reset = self.request('/api/update', {'command': 'timer_reset'})['live']
        self.assertFalse(reset['running'])
        self.assertEqual(reset['remaining'], 43 * 60)
        for value in (0, -1, 99, '5', True):
            with self.subTest(value=value), self.assertRaises(HTTPError) as error:
                self.request('/api/update', {'command': 'timer_adjust', 'minutes': value})
            self.assertEqual(error.exception.code, 400)
        self.request('/api/update', {'command': 'timer_set', 'minutes': 999})
        with self.assertRaises(HTTPError) as error:
            self.request('/api/update', {'command': 'timer_adjust', 'minutes': 1})
        self.assertEqual(error.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
