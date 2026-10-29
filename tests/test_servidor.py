"""Pruebas de integración del servidor local. Ejecutar: python -m unittest discover -s tests -v"""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from urllib import request

ROOT = pathlib.Path(__file__).resolve().parents[1]

class TestServidor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.work = pathlib.Path(cls.temp.name)
        for file in ("servidor.py", "panel.html", "overlay.html"):
            shutil.copy(ROOT / file, cls.work / file)
        cls.process = subprocess.Popen([sys.executable, str(cls.work / "servidor.py")],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        for _ in range(50):
            try:
                cls.get("/api/state")
                break
            except OSError:
                time.sleep(.1)
        else:
            raise RuntimeError("No inició el servidor")
    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()
        cls.process.wait(timeout=5)
        cls.process.stderr.close()
        cls.temp.cleanup()

    @staticmethod
    def get(path):
        with request.urlopen("http://127.0.0.1:8765" + path, timeout=2) as r:
            return r.read()

    @staticmethod
    def command(command, **payload):
        body = json.dumps({"command": command, **payload}).encode()
        req = request.Request("http://127.0.0.1:8765/api/update", data=body,
                              headers={"Content-Type": "application/json"})
        with request.urlopen(req, timeout=2) as r:
            return json.load(r)

    def test_pages(self):
        self.assertIn(b"<html", self.get("/panel.html").lower())
        self.assertIn(b"<html", self.get("/overlay.html").lower())

    def test_salmista_y_respuesta_sin_publicacion_automatica(self):
        original = json.loads(self.get("/api/state"))
        self.command("draft", updates={
            "parish_name": "Parroquia de prueba",
            "participants": {"celebrante": "P. Ejemplo", "diacono": "",
                             "salmista": "María", "lectores": ["Ana"], "monitores": ["Rosa"]},
            "salmo_respuesta": "El Señor es mi pastor"
        })
        draft = json.loads(self.get("/api/draft"))
        before = json.loads(self.get("/api/state"))
        self.assertEqual(draft["participants"]["salmista"], "María")
        self.assertEqual(draft["salmo_respuesta"], "El Señor es mi pastor")
        self.assertEqual(before["participants"].get("salmista"), original["participants"].get("salmista"))
        self.command("publish")
        after = json.loads(self.get("/api/state"))
        self.assertEqual(after["participants"]["salmista"], "María")
        self.assertEqual(after["salmo_respuesta"], "El Señor es mi pastor")
        self.assertTrue((self.work / "configuracion.json").exists())

    def test_cronometro_e_imagen_limpia(self):
        self.command("timer_set", minutes=1)
        self.command("timer_start")
        self.assertTrue(json.loads(self.get("/api/state"))["running"])
        self.command("timer_pause")
        self.command("clean")
        self.assertFalse(json.loads(self.get("/api/state"))["visible"])
        self.command("restore")
        self.assertTrue(json.loads(self.get("/api/state"))["visible"])

if __name__ == "__main__":
    unittest.main()
