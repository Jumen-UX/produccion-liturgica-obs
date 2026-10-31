"""Pruebas del protocolo local de OBS y de la clasificación de estados."""

import base64
import hashlib
import json
import socketserver
import struct
import tempfile
import threading
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from obs_monitor import (OBSAuthRejected, OBSAuthRequired, OBSMonitor,
                         OBSProtocolIncompatible, OBSWebSocket, graphic_state)


class FakeOBS(socketserver.BaseRequestHandler):
    """Servidor de prueba mínimo; nunca inicia una transmisión real."""

    def _read(self, size):
        result = b""
        while len(result) < size:
            part = self.request.recv(size - len(result))
            if not part:
                raise ConnectionError("Cliente desconectado")
            result += part
        return result

    def _receive(self):
        header = self._read(2)
        size = header[1] & 0x7F
        if size == 126:
            size = struct.unpack("!H", self._read(2))[0]
        elif size == 127:
            size = struct.unpack("!Q", self._read(8))[0]
        assert header[1] & 0x80, "El cliente debe enmascarar los mensajes WebSocket"
        mask = self._read(4)
        value = self._read(size)
        return json.loads(bytes(byte ^ mask[index % 4] for index, byte in enumerate(value)))

    def _send(self, value):
        payload = json.dumps(value).encode()
        if len(payload) < 126:
            head = bytes((0x81, len(payload)))
        else:
            head = b"\x81\x7e" + struct.pack("!H", len(payload))
        self.request.sendall(head + payload)

    def handle(self):
        request = b""
        while b"\r\n\r\n" not in request:
            request += self.request.recv(4096)
        headers = request.decode().split("\r\n")
        key = next(line.split(":", 1)[1].strip() for line in headers if line.lower().startswith("sec-websocket-key:"))
        accept = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
        self.request.sendall(("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\n"
                              "Connection: Upgrade\r\nSec-WebSocket-Accept: " + accept + "\r\n\r\n").encode())
        self._send({"op": 0, "d": {"obsWebSocketVersion": "5.0", "rpcVersion": 1,
                                 "authentication": {"challenge": "prueba-challenge", "salt": "prueba-salt"}}})
        identify = self._receive()
        secret = base64.b64encode(hashlib.sha256("clave-pruebaprueba-salt".encode()).digest()).decode()
        expected = base64.b64encode(hashlib.sha256((secret + "prueba-challenge").encode()).digest()).decode()
        assert identify["op"] == 1 and identify["d"]["authentication"] == expected
        self._send({"op": 2, "d": {"negotiatedRpcVersion": 1}})
        for _ in range(2):
            call = self._receive()
            assert call["op"] == 6
            name = call["d"]["requestType"]
            assert name in ("GetStreamStatus", "GetSourceActive")
            if name == "GetSourceActive":
                assert call["d"]["requestData"]["sourceName"] == "Navegador 2"
            self._send({"op": 7, "d": {"requestId": call["d"]["requestId"],
                                     "requestType": name, "requestStatus": {"result": True, "code": 100},
                                     "responseData": {"outputActive": True} if name == "GetStreamStatus"
                                                     else {"videoActive": True, "videoShowing": True}}})


class OBSMonitorTests(unittest.TestCase):
    def test_websocket_diagnostic_works_before_source_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            monitor = OBSMonitor(Path(directory) / "conexion_obs.json", start_worker=False)
            client = MagicMock()
            with patch("obs_monitor.OBSWebSocket", return_value=client) as socket_client:
                result = monitor.diagnostic()
            self.assertEqual(result, {"state": "ready", "port": 4455,
                                      "source_configured": False})
            socket_client.assert_called_once_with(4455, "")
            client.close.assert_called_once()

    def test_websocket_diagnostic_distinguishes_failure_modes_without_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            monitor = OBSMonitor(Path(directory) / "conexion_obs.json", start_worker=False)
            failures = (
                (OBSAuthRequired("password required"), "password_required"),
                (OBSAuthRejected("password rejected"), "auth_failed"),
                (OBSProtocolIncompatible("old protocol"), "incompatible"),
                (ConnectionRefusedError("OBS not running"), "unavailable"),
            )
            for failure, expected in failures:
                with self.subTest(state=expected), patch("obs_monitor.OBSWebSocket", side_effect=failure):
                    result = monitor.diagnostic()
                self.assertEqual(result["state"], expected)
                self.assertNotIn("password", result)
                self.assertNotIn("OBS not running", str(result))

    def test_detects_only_our_browser_source_without_changing_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            monitor = OBSMonitor(Path(directory) / "conexion_obs.json", start_worker=False)
            client = MagicMock()

            def respond(command, data=None):
                if command == "GetInputList":
                    return {"inputs": [
                        {"inputName": "Logo", "inputKind": "image_source"},
                        {"inputName": "Gráficos", "inputKind": "browser_source"},
                        {"inputName": "Noticias", "inputKind": "browser_source"},
                    ]}
                if data["inputName"] == "Gráficos":
                    return {"inputSettings": {"url": "http://127.0.0.1:8765/overlay.html"}}
                return {"inputSettings": {"url": "https://example.org"}}

            client.request.side_effect = respond
            with patch("obs_monitor.OBSWebSocket", return_value=client) as websocket:
                result = monitor.detect_graphic_sources(4455, "clave temporal")
            self.assertEqual(result, {"matches": ["Gráficos"], "port": 4455})
            self.assertFalse(monitor.configuration()["has_password"])
            self.assertEqual(monitor.configuration()["source_name"], "")
            websocket.assert_called_once_with(4455, "clave temporal")
            self.assertEqual([call.args[0] for call in client.request.call_args_list],
                             ["GetInputList", "GetInputSettings", "GetInputSettings"])
            client.close.assert_called_once()

    def test_detection_does_not_guess_when_two_browser_sources_match(self):
        with tempfile.TemporaryDirectory() as directory:
            monitor = OBSMonitor(Path(directory) / "conexion_obs.json", start_worker=False)
            client = MagicMock()
            client.request.side_effect = lambda command, data=None: (
                {"inputs": [{"inputName": "A", "inputKind": "browser_source"},
                            {"inputName": "B", "inputKind": "browser_source"}]}
                if command == "GetInputList" else
                {"inputSettings": {"url": "http://localhost:8765/overlay.html?test=1"}}
            )
            with patch("obs_monitor.OBSWebSocket", return_value=client):
                result = monitor.detect_graphic_sources()
            self.assertEqual(result["matches"], ["A", "B"])
            self.assertFalse(monitor.configuration()["source_name"])

    def test_graphic_status_never_claims_air_without_obs_confirmation(self):
        graphic = {"visible": True, "mode": "lectura"}
        status = {"configured": True, "connected": True, "source_active": True, "streaming": True}
        self.assertEqual(graphic_state(graphic, status), "al_aire")
        self.assertEqual(graphic_state(graphic, {**status, "streaming": False}), "en_programa")
        self.assertEqual(graphic_state(graphic, {**status, "streaming": None}), "sin_verificar")
        self.assertEqual(graphic_state(graphic, {**status, "source_active": False}), "fuera_de_programa")
        self.assertEqual(graphic_state(graphic, {**status, "connected": False}), "sin_verificar")
        self.assertEqual(graphic_state(graphic, {**status, "configured": False}), "sin_verificar")
        self.assertEqual(graphic_state({**graphic, "visible": False}, status), "imagen_limpia")

    def test_configuration_persists_only_non_secret_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "conexion_obs.json"
            monitor = OBSMonitor(path, start_worker=False)
            monitor.configure({"port": 4455, "source_name": "Navegador 2", "password": "secreto"})
            self.assertTrue(monitor.configuration()["has_password"])
            self.assertNotIn("secreto", path.read_text(encoding="utf-8"))
            restored = OBSMonitor(path, start_worker=False)
            self.assertEqual(restored.configuration()["source_name"], "Navegador 2")
            self.assertFalse(restored.configuration()["has_password"])
            for bad in ({"port": 80}, {"port": "falso"}, {"port": 4455, "source_name": 42}):
                with self.subTest(bad=bad), self.assertRaises((ValueError, TypeError)):
                    monitor.configure(bad)

    def test_authenticated_read_only_obs_websocket(self):
        server = socketserver.TCPServer(("127.0.0.1", 0), FakeOBS)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = OBSWebSocket(server.server_address[1], "clave-prueba")
            try:
                self.assertTrue(client.request("GetStreamStatus")["outputActive"])
                self.assertTrue(client.request("GetSourceActive", {"sourceName": "Navegador 2"})["videoActive"])
            finally:
                client.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
