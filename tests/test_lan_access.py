"""Acceso LAN: permisos, host, sesiones, aislamiento y operación sincronizada."""

import copy
import json
import tempfile
import threading
import unittest
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener, urlopen

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import servidor
from lan_access import LANAccess, LANServer, LANRuntime


class LANAccessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original = (servidor.DATA, servidor.draft, servidor.live, servidor.last_visible_state,
                         servidor.LAN_ACCESS, servidor.LAN_RUNTIME)
        servidor.DATA = Path(self.temp.name) / "configuracion.json"
        servidor.draft = copy.deepcopy(servidor.DEFAULT)
        servidor.live = copy.deepcopy(servidor.DEFAULT)
        servidor.last_visible_state = None
        servidor.LAN_ACCESS = LANAccess(Path(self.temp.name) / "acceso_lan.json")
        servidor.LAN_RUNTIME = None
        self.local = ThreadingHTTPServer(("127.0.0.1", 0), servidor.Handler)
        self.lan = LANServer(("127.0.0.1", 0), servidor.Handler)
        self.workers = [threading.Thread(target=server.serve_forever, daemon=True)
                        for server in (self.local, self.lan)]
        for worker in self.workers:
            worker.start()
        self.local_url = f"http://127.0.0.1:{self.local.server_port}"
        self.lan_url = f"http://127.0.0.1:{self.lan.server_port}"
        self.operator = build_opener(HTTPCookieProcessor(CookieJar()))
        self.viewer = build_opener(HTTPCookieProcessor(CookieJar()))
        self.anonymous = build_opener(HTTPCookieProcessor(CookieJar()))

    def tearDown(self):
        for server in (self.local, self.lan):
            server.shutdown()
            server.server_close()
        for worker in self.workers:
            worker.join(timeout=2)
        (servidor.DATA, servidor.draft, servidor.live, servidor.last_visible_state,
         servidor.LAN_ACCESS, servidor.LAN_RUNTIME) = self.original
        self.temp.cleanup()

    def request(self, url, path, data=None, opener=None, headers=None):
        request_headers = {}
        if data is not None:
            request_headers = {"Content-Type": "application/json", "Origin": url}
        request_headers.update(headers or {})
        request = Request(url + path, data=json.dumps(data).encode() if data is not None else None,
                          headers=request_headers)
        return (opener or self.anonymous).open(request, timeout=4)

    def json(self, url, path, data=None, opener=None, headers=None):
        with self.request(url, path, data, opener, headers) as response:
            return json.load(response)

    def setup_credentials(self):
        self.json(self.local_url, "/api/lan/config", {
            "enabled": True, "port": 8766,
            "operator_password": "operador-secreto-123",
            "viewer_password": "consulta-secreta-456",
        })
        return self.operator_login(), self.viewer_login()

    def operator_login(self):
        return self.json(self.lan_url, "/api/login", {"password": "operador-secreto-123"}, self.operator)

    def viewer_login(self):
        return self.json(self.lan_url, "/api/login", {"password": "consulta-secreta-456"}, self.viewer)

    def assert_denied(self, status, url, path, data=None, opener=None, headers=None):
        with self.assertRaises(HTTPError) as error:
            self.request(url, path, data, opener, headers)
        self.assertEqual(error.exception.code, status)

    def test_disabled_by_default_and_password_hashes_at_rest(self):
        self.assertFalse(self.json(self.local_url, "/api/lan/status")["enabled"])
        self.assert_denied(401, self.lan_url, "/api/login", {"password": "una-clave-falsa"})
        self.setup_credentials()
        saved = (Path(self.temp.name) / "acceso_lan.json").read_text()
        self.assertNotIn("operador-secreto-123", saved)
        self.assertNotIn("consulta-secreta-456", saved)
        status = self.json(self.local_url, "/api/lan/status")
        self.assertTrue(status["operator_configured"])
        self.assertNotIn("digest", json.dumps(status))
        self.assertEqual(self.json(self.lan_url, "/api/session", opener=self.operator)["role"], "operator")
        self.assertEqual(self.json(self.lan_url, "/api/session", opener=self.viewer)["role"], "viewer")

    def test_remote_routes_are_protected_even_after_login(self):
        self.setup_credentials()
        for path in ("/panel.html", "/studio.html", "/overlay.html", "/servidor.py",
                     "/README.md", "/configuracion.json", "/acceso_lan.json",
                     "/api/lan/status", "/api/obs-config", "/api/lan/qr.svg"):
            with self.subTest(path=path):
                self.assert_denied(404, self.lan_url, path, opener=self.operator)
        self.assert_denied(401, self.lan_url, "/api/state")
        self.assert_denied(401, self.lan_url, "/remote.html")
        with self.request(self.lan_url, "/remote.html", opener=self.viewer) as response:
            self.assertEqual(response.status, 200)
        with self.request(self.lan_url, "/login.html") as response:
            self.assertEqual(response.status, 200)

    def test_viewer_read_only_and_operator_changes_same_live_state(self):
        self.setup_credentials()
        self.assert_denied(403, self.lan_url, "/api/update", {"command": "clean"}, self.viewer)
        self.assert_denied(403, self.lan_url, "/api/update", {"command": "draft", "updates": {"title": "Robado"}}, self.operator)
        self.assert_denied(404, self.lan_url, "/api/image", {"anything": 1}, self.operator)
        self.json(self.local_url, "/api/update", {"command": "draft", "updates": {"mode": "lectura", "title": "Lectura de prueba"}})
        self.json(self.lan_url, "/api/update", {"command": "publish"}, self.operator)
        self.assertEqual(self.json(self.local_url, "/api/state")["title"], "Lectura de prueba")
        self.json(self.lan_url, "/api/update", {"command": "clean"}, self.operator)
        self.assertFalse(self.json(self.lan_url, "/api/state", opener=self.viewer)["visible"])
        self.json(self.lan_url, "/api/update", {"command": "restore"}, self.operator)
        self.assertEqual(self.json(self.local_url, "/api/state")["title"], "Lectura de prueba")
        self.assertTrue(self.json(self.local_url, "/api/state")["visible"])

    def test_revocation_logout_and_password_rotation(self):
        self.setup_credentials()
        self.json(self.local_url, "/api/lan/config", {"revoke_sessions": True})
        self.assert_denied(401, self.lan_url, "/api/state", opener=self.operator)
        self.operator_login()
        self.json(self.lan_url, "/api/logout", {}, self.operator)
        self.assert_denied(401, self.lan_url, "/api/state", opener=self.operator)
        self.operator_login()
        self.json(self.local_url, "/api/lan/config", {"operator_password": "nueva-clave-fuerte-999"})
        self.assert_denied(401, self.lan_url, "/api/state", opener=self.operator)
        self.assert_denied(401, self.lan_url, "/api/login", {"password": "operador-secreto-123"})
        self.assertEqual(self.json(self.lan_url, "/api/login", {"password": "nueva-clave-fuerte-999"})["role"], "operator")
        self.json(self.local_url, "/api/lan/config", {"enabled": False})
        self.assert_denied(401, self.lan_url, "/api/state", opener=self.viewer)

    def test_rejects_cross_origin_host_spoofing_and_bruteforce(self):
        self.setup_credentials()
        self.assert_denied(403, self.lan_url, "/api/update", {"command": "clean"}, self.operator,
                           {"Origin": "http://malicioso.example"})
        self.assert_denied(421, self.lan_url, "/api/state", opener=self.operator,
                           headers={"Host": "malicioso.example:" + str(self.lan.server_port)})
        for _ in range(5):
            self.assert_denied(401, self.lan_url, "/api/login", {"password": "incorrecta"})
        self.assert_denied(429, self.lan_url, "/api/login", {"password": "operador-secreto-123"})

    def test_invalid_configuration_does_not_change_current_state(self):
        self.setup_credentials()
        for invalid in ({"port": 8765}, {"port": 4455}, {"enabled": "true"},
                        {"operator_password": "corta"}, {"viewer_password": 123},
                        {"desconocido": True}):
            with self.subTest(invalid=invalid):
                self.assert_denied(400, self.local_url, "/api/lan/config", invalid)
                self.assertTrue(self.json(self.local_url, "/api/lan/status")["enabled"])

    def test_qr_svg_is_generated_locally_and_only_for_known_address(self):
        try:
            import qrcode  # noqa: F401
        except ImportError:
            self.skipTest("qrcode se instala en Windows antes de ejecutar las pruebas")
        self.setup_credentials()
        with patch.object(servidor, "local_addresses", return_value=["192.168.1.40"]):
            with self.request(self.local_url, "/api/lan/qr.svg?address=192.168.1.40") as response:
                self.assertIn("image/svg+xml", response.headers["Content-Type"])
                self.assertIn(b"<svg", response.read())
            self.assert_denied(404, self.local_url, "/api/lan/qr.svg?address=192.168.1.41")

    def test_runtime_start_stop_and_port_collision(self):
        access = LANAccess(Path(self.temp.name) / "runtime.json")
        runtime = LANRuntime(access, servidor.Handler)
        access.configure({"enabled": True, "port": 8767,
                          "operator_password": "clave-segura-1234"})
        # Windows puede permitir bindings solapados entre 127.0.0.1 y 0.0.0.0.
        # Simular el fallo del SO evita una suposición distinta por plataforma.
        with patch("lan_access.LANServer", side_effect=OSError("Puerto ocupado")):
            with self.assertRaises(OSError):
                runtime.apply()
        self.assertIsNone(runtime.server)
        access.configure({"enabled": False})
        runtime.apply()
        self.assertIsNone(runtime.server)

    def test_event_stream_notifies_live_changes_without_private_data(self):
        self.setup_credentials()
        with self.request(self.lan_url, "/api/events", opener=self.operator) as response:
            self.assertEqual(response.headers["Content-Type"], "text/event-stream; charset=utf-8")
            first = response.readline().decode()
            self.assertTrue(first.startswith("data: "))
            self.assertEqual(response.readline(), b"\n")
            self.json(self.local_url, "/api/update", {"command": "clean"})
            second = response.readline().decode()
            self.assertTrue(second.startswith("data: "))
            self.assertNotEqual(first, second)
            self.assertNotIn("password", second)


if __name__ == "__main__":
    unittest.main()
