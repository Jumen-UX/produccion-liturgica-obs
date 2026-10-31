"""Contrato HTTP del catálogo, los gráficos preparados y la rotación en OBS."""
import copy
import json
import tempfile
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import servidor
from production_library import ProductionLibrary


class ProductionRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.original = (servidor.PRODUCTIONS, servidor.draft, servidor.live, servidor.DATA, servidor.last_visible_state)
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
            servidor.PRODUCTIONS, servidor.draft, servidor.live, servidor.DATA, servidor.last_visible_state = self.original

    def get(self, path):
        with urlopen(self.base + path, timeout=3) as response:
            return json.load(response)

    def post(self, path, payload):
        req = Request(self.base + path, data=json.dumps(payload).encode("utf-8"),
                      headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=3) as response:
            return json.load(response)

    def test_local_library_keeps_multiple_items_and_example_values(self):
        state = self.get("/api/productions")
        self.assertEqual(state["productions"][0]["name"], "Producción de ejemplo")
        self.assertEqual(len([x for x in state["productions"][0]["items"] if x["type"]=="red_social"]), 2)
        new = self.post("/api/productions", {"action":"add","item":{
            "type":"lower_third","name":"Segundo lector","data":{"name":"María Pérez","role":"Lectura"}}})
        self.assertEqual(len([x for x in new["productions"][0]["items"] if x["type"]=="lower_third"]),3)
        self.assertTrue(Path(self.temp.name, "producciones.json").exists())
        for page in ("/biblioteca.html", "/overlay.html?preview=1", "/studio.html", "/dock.html"):
            with urlopen(self.base + page, timeout=3) as response:
                self.assertEqual(response.status, 200)

    def test_individual_launch_uses_saved_design_without_touching_draft(self):
        self.post("/api/update", {"command":"draft","updates":{"lower_third":{
            "template":"modern","background":"#223344","accent":"#CCAA55"}}})
        before = self.get("/api/draft")
        state = self.get("/api/productions")
        production = state["productions"][0]
        item = next(x for x in production["items"] if x["type"]=="lower_third")
        self.post("/api/update", {"command":"library_launch",
                 "production_id":production["id"],"item_id":item["id"]})
        output = self.get("/api/state")
        self.assertEqual(output["mode"],"lower_third")
        self.assertEqual(output["lower_third"]["template"],"modern")
        self.assertEqual(output["lower_third"]["name"],item["data"]["name"])
        self.assertEqual(output["library_item"]["item_id"],item["id"])
        self.assertEqual(self.get("/api/draft"),before)
        self.post("/api/update", {"command":"clean"})
        self.assertFalse(self.get("/api/state")["visible"])
        self.post("/api/update", {"command":"restore"})
        self.assertTrue(self.get("/api/state")["visible"])
        self.assertEqual(self.get("/api/state")["library_item"]["item_id"],item["id"])
        self.post("/api/update", {"command":"launch","mode":"lower_third"})
        self.assertNotIn("library_item",self.get("/api/state"))

    def test_rotation_is_one_snapshot_and_can_be_stopped(self):
        state = self.get("/api/productions")
        pid = state["active_id"]
        started = self.post("/api/update", {"command":"social_rotation_start","production_id":pid})
        rotation = started["live"]["social_rotation"]
        self.assertEqual(len(rotation["items"]),2)
        self.assertGreater(rotation["started_at"],time.time()-5)
        self.assertTrue(started["live"]["social_now"])
        self.post("/api/productions",{"action":"add","item":{
            "type":"red_social","name":"Facebook", "data":{
                "network":"facebook","handle":"Página","phrase":"Dale like","logo":""}}})
        self.assertEqual(len(self.get("/api/state")["social_rotation"]["items"]),2)
        stopped = self.post("/api/update", {"command":"social_rotation_stop"})
        self.assertIsNone(stopped["live"]["social_rotation"])
        self.assertFalse(stopped["live"]["social_now"])
        with self.assertRaises(HTTPError) as error:
            self.post("/api/update", {"command":"library_launch",
                "production_id":pid,"item_id":"no-existe"})
        self.assertEqual(error.exception.code,400)


if __name__=="__main__":
    unittest.main()
