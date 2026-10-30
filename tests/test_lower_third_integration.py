"""Pruebas de contrato para Lower Thirds y la salida HTTP local."""

import copy
import json
import tempfile
import threading
import time
import unittest
from html.parser import HTMLParser
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import servidor
from obs_monitor import OBSMonitor


class PageStructure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.controls = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        props = dict(attrs)
        if props.get("id"):
            self.ids.add(props["id"])
        if tag in ("input", "select", "textarea"):
            self.controls.append(tag)
        if tag == "a":
            self.links.append(props.get("href"))


class LowerThirdIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original = (servidor.ROOT, servidor.DATA, servidor.draft, servidor.live, servidor.last_visible_state, servidor.OBS_MONITOR)
        with servidor.LOCK:
            servidor.ROOT = Path(__file__).resolve().parents[1]
            servidor.DATA = Path(self.temp.name) / "configuracion.json"
            servidor.draft = copy.deepcopy(servidor.DEFAULT)
            servidor.live = copy.deepcopy(servidor.DEFAULT)
            servidor.last_visible_state = None
            servidor.OBS_MONITOR = OBSMonitor(Path(self.temp.name) / "conexion_obs.json", start_worker=False)
        self.http = ThreadingHTTPServer(("127.0.0.1", 0), servidor.Handler)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.http.server_port}"

    def tearDown(self):
        self.http.shutdown()
        self.http.server_close()
        self.thread.join(timeout=2)
        with servidor.LOCK:
            servidor.ROOT, servidor.DATA, servidor.draft, servidor.live, servidor.last_visible_state, servidor.OBS_MONITOR = self.original
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

    def test_restore_recovers_last_visible_graphic_not_a_new_draft(self):
        original_colors = {**servidor.DEFAULT["colors"], "accent": "#c38044"}
        self.post("draft", updates={
            "mode": "lectura", "title": "Primera lectura", "reference": "Is 35, 1-6",
            "colors": original_colors, "lower_third": {"name": "Lector anterior"},
        })
        self.post("publish")
        previous = self.get("/api/state")

        self.post("clean")
        self.post("clean")  # No reemplazar el historial por una pantalla vacía.
        self.post("draft", updates={
            "mode": "cierre", "title": "Gracias por acompañarnos",
            "colors": {**original_colors, "accent": "#123456"},
            "lower_third": {"name": "Nuevo lector"},
        })
        self.post("restore")
        restored = self.get("/api/state")
        for key in servidor.SCREEN_STATE_FIELDS:
            with self.subTest(field=key):
                self.assertEqual(restored[key], previous[key])
        self.assertEqual(self.get("/api/draft")["title"], "Gracias por acompañarnos")

        self.post("restore")  # Restaurar no altera un gráfico que ya esté visible.
        self.assertEqual(self.get("/api/state")["title"], "Primera lectura")

    def test_clean_restore_preserves_timer_runtime(self):
        self.post("timer_set", minutes=7)
        self.post("timer_start")
        self.post("clean")
        self.post("restore")
        restored = self.get("/api/state")
        self.assertEqual(restored["mode"], "espera")
        self.assertTrue(restored["running"])
        self.assertGreater(restored["remaining"], 0)
        self.assertLessEqual(restored["remaining"], 420)

    def test_technical_incident_requires_explicit_confirmation(self):
        self.post("draft", updates={"mode": "incidencia", "title": "Dificultades técnicas"})
        before = self.get("/api/state")
        for options in ({}, {"confirm_incidence": False}, {"confirm_incidence": "true"}):
            with self.subTest(options=options), self.assertRaises(HTTPError) as error:
                self.post("publish", **options)
            self.assertEqual(error.exception.code, 400)
            self.assertEqual(self.get("/api/state"), before)
        self.post("publish", confirm_incidence=True)
        self.assertEqual(self.get("/api/state")["mode"], "incidencia")

    def test_obs_program_confirmation_and_secret_protection(self):
        unverified = self.get("/api/obs-status")
        self.assertEqual(unverified["graphic_status"], "sin_verificar")
        request = Request(
            self.base + "/api/obs-config",
            data=json.dumps({"port": 4455, "source_name": "Navegador 2", "password": "clave-solo-en-memoria"}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=3) as response:
            result = json.load(response)
        self.assertTrue(result["config"]["has_password"])
        self.assertNotIn("password", result["config"])
        saved = (Path(self.temp.name) / "conexion_obs.json").read_text(encoding="utf-8")
        self.assertNotIn("clave-solo-en-memoria", saved)
        self.assertNotIn("password", saved)

        with servidor.OBS_MONITOR.lock:
            servidor.OBS_MONITOR.status = {"connected": True, "streaming": True,
                                          "source_active": True, "error": "", "checked_at": time.time()}
        self.assertEqual(self.get("/api/obs-status")["graphic_status"], "al_aire")
        self.post("clean")
        self.assertEqual(self.get("/api/obs-status")["graphic_status"], "imagen_limpia")
        self.post("restore")
        self.assertEqual(self.get("/api/obs-status")["graphic_status"], "al_aire")
        with servidor.OBS_MONITOR.lock:
            servidor.OBS_MONITOR.status["source_active"] = False
        self.assertEqual(self.get("/api/obs-status")["graphic_status"], "fuera_de_programa")
        with servidor.OBS_MONITOR.lock:
            servidor.OBS_MONITOR.status["connected"] = False
        self.assertEqual(self.get("/api/obs-status")["graphic_status"], "sin_verificar")

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

    def test_draft_text_does_not_reset_saved_animation(self):
        self.post("draft", updates={"lower_third": {"template": "liturgical", "enter": "rise", "exit": "right"}})
        self.post("draft", updates={"mode": "lower_third", "lower_third": {"name": "Nombre desde Dock", "role": "Lector"}})
        current = self.get("/api/draft")["lower_third"]
        self.assertEqual(current["name"], "Nombre desde Dock")
        self.assertEqual(current["template"], "liturgical")
        self.assertEqual(current["enter"], "rise")
        self.assertEqual(current["exit"], "right")

    def test_dock_launch_uses_web_configuration_without_editing_it(self):
        self.post("draft", updates={
            "mode": "lectura", "title": "Primera lectura",
            "participants": {"celebrante": "P. Ejemplo", "diacono": "", "lectores": ["Ana"], "monitores": []},
            "lower_third": {"name": "Panelista", "template": "modern"},
        })
        prepared = self.get("/api/draft")
        for selected in ("lower_third", "participante"):
            with self.subTest(mode=selected):
                self.post("launch", mode=selected)
                live = self.get("/api/state")
                self.assertEqual(live["mode"], selected)
                self.assertTrue(live["visible"])
                self.assertEqual(self.get("/api/draft"), prepared)
        self.assertEqual(self.get("/api/state")["lower_third"]["template"], "modern")
        with self.assertRaises(HTTPError) as error:
            self.post("launch", mode="espera")
        self.assertEqual(error.exception.code, 400)
        self.post("draft", updates={"mode": "espera", "title": "Santa Misa"})
        self.post("launch", mode="espera")
        self.assertEqual(self.get("/api/state")["title"], "Santa Misa")
        with self.assertRaises(HTTPError) as error:
            self.post("launch", mode="incidencia")
        self.assertEqual(error.exception.code, 400)

    def test_configuration_stays_in_web_panel_and_studio(self):
        pages = {}
        for name in ("dock.html", "panel.html", "studio.html"):
            page = PageStructure()
            page.feed((Path(__file__).resolve().parents[1] / name).read_text(encoding="utf-8"))
            pages[name] = page
        self.assertFalse(pages["dock.html"].controls, "El Dock no debe incluir campos de edición")
        self.assertIn("/panel.html", pages["dock.html"].links)
        self.assertIn("/studio.html", pages["dock.html"].links)
        self.assertIn("/panel.html", pages["studio.html"].links)
        for control in ("mode", "modeHelp", "contentFields", "applySuggestion", "logoSettings", "colorSettings", "coverSettings"):
            self.assertIn(control, pages["panel.html"].ids)
        for control in ("mobileClean", "mobileRestore", "mobileLiveState"):
            self.assertIn(control, pages["panel.html"].ids)
        for control in ("obsSettings", "obsConnect", "obs_source_name", "liveState", "onAirGraphic"):
            self.assertIn(control, pages["panel.html"].ids)
        for control in ("airBadge", "airGraphic", "statePrepared", "stateLower", "statePerson", "stateWait"):
            self.assertIn(control, pages["dock.html"].ids)
        self.assertNotIn("template", pages["panel.html"].ids)


if __name__ == "__main__":
    unittest.main()
