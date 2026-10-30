"""Comprobación local, de solo lectura, de la salida de programa de OBS.

Cliente mínimo para obs-websocket 5.x (RFC 6455). No necesita instalar
dependencias ni envía comandos que modifiquen escenas o transmisiones.
"""

import base64
import hashlib
import json
import os
import socket
import struct
import threading
import time
import uuid
from pathlib import Path


class OBSConnectionError(Exception):
    pass


class OBSRequestError(OBSConnectionError):
    pass


class OBSWebSocket:
    """Cliente WebSocket de texto para OBS en 127.0.0.1."""

    MAX_MESSAGE = 1024 * 1024

    def __init__(self, port, password="", timeout=1.8):
        self.sock = socket.create_connection(("127.0.0.1", port), timeout=timeout)
        self.sock.settimeout(timeout)
        self.buffer = b""
        try:
            self._handshake()
            greeting = self.receive()
            if greeting.get("op") != 0:
                raise OBSConnectionError("OBS no respondió con el protocolo WebSocket 5.x")
            auth = greeting.get("d", {}).get("authentication")
            identify = {"rpcVersion": 1}
            if auth:
                if not password:
                    raise OBSConnectionError("OBS solicita contraseña: introdúcela en el panel web")
                challenge = auth["challenge"]
                salt = auth["salt"]
                secret = base64.b64encode(hashlib.sha256((password + salt).encode()).digest()).decode()
                identify["authentication"] = base64.b64encode(
                    hashlib.sha256((secret + challenge).encode()).digest()
                ).decode()
            self.send({"op": 1, "d": identify})
            if self.receive().get("op") != 2:
                raise OBSConnectionError("OBS rechazó la identificación WebSocket")
        except Exception:
            self.close()
            raise

    def _read(self, size):
        while len(self.buffer) < size:
            part = self.sock.recv(max(4096, size - len(self.buffer)))
            if not part:
                raise OBSConnectionError("OBS cerró la conexión")
            self.buffer += part
        data, self.buffer = self.buffer[:size], self.buffer[size:]
        return data

    def _handshake(self):
        key = base64.b64encode(os.urandom(16)).decode()
        request = (
            "GET / HTTP/1.1\r\nHost: 127.0.0.1\r\nUpgrade: websocket\r\n"
            "Connection: Upgrade\r\nSec-WebSocket-Key: " + key +
            "\r\nSec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(request.encode("ascii"))
        while b"\r\n\r\n" not in self.buffer:
            if len(self.buffer) > 8192:
                raise OBSConnectionError("Respuesta HTTP de OBS demasiado grande")
            part = self.sock.recv(4096)
            if not part:
                raise OBSConnectionError("OBS no aceptó WebSocket")
            self.buffer += part
        headers, self.buffer = self.buffer.split(b"\r\n\r\n", 1)
        lines = headers.decode("latin-1").split("\r\n")
        fields = dict(line.split(":", 1) for line in lines[1:] if ":" in line)
        fields = {k.strip().lower(): v.strip() for k, v in fields.items()}
        expected = base64.b64encode(hashlib.sha1(
            (key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()
        ).digest()).decode()
        if " 101 " not in lines[0] + " " or fields.get("sec-websocket-accept") != expected:
            raise OBSConnectionError("Respuesta WebSocket de OBS inválida")

    def _send_frame(self, payload, opcode=1):
        size = len(payload)
        if size < 126:
            header = bytes((0x80 | opcode, 0x80 | size))
        elif size < 65536:
            header = bytes((0x80 | opcode, 0xFE)) + struct.pack("!H", size)
        else:
            header = bytes((0x80 | opcode, 0xFF)) + struct.pack("!Q", size)
        mask = os.urandom(4)
        data = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        self.sock.sendall(header + mask + data)

    def send(self, message):
        self._send_frame(json.dumps(message).encode("utf-8"))

    def receive(self):
        while True:
            first, second = self._read(2)
            opcode, length = first & 0x0F, second & 0x7F
            if not first & 0x80:
                raise OBSConnectionError("OBS envió un mensaje WebSocket fragmentado")
            if length == 126:
                length = struct.unpack("!H", self._read(2))[0]
            elif length == 127:
                length = struct.unpack("!Q", self._read(8))[0]
            if length > self.MAX_MESSAGE:
                raise OBSConnectionError("Mensaje de OBS demasiado grande")
            mask = self._read(4) if second & 0x80 else None
            payload = self._read(length)
            if mask:
                payload = bytes(byte ^ mask[i % 4] for i, byte in enumerate(payload))
            if opcode == 8:
                raise OBSConnectionError("OBS cerró WebSocket")
            if opcode == 9:
                self._send_frame(payload, opcode=10)
                continue
            if opcode != 1:
                continue
            try:
                return json.loads(payload)
            except (ValueError, UnicodeDecodeError) as exc:
                raise OBSConnectionError("Mensaje JSON de OBS inválido") from exc

    def request(self, name, parameters=None):
        request_id = uuid.uuid4().hex
        data = {"requestType": name, "requestId": request_id}
        if parameters:
            data["requestData"] = parameters
        self.send({"op": 6, "d": data})
        while True:
            reply = self.receive()
            if reply.get("op") != 7 or reply.get("d", {}).get("requestId") != request_id:
                continue
            result = reply["d"]
            if not result.get("requestStatus", {}).get("result"):
                raise OBSRequestError(result.get("requestStatus", {}).get("comment") or
                                      "OBS rechazó la consulta " + name)
            return result.get("responseData", {})

    def close(self):
        self.sock.close()


def graphic_state(graphic, obs):
    """Nunca presentar como AL AIRE un estado sin confirmación de OBS."""
    if not obs.get("configured") or not obs.get("connected"):
        return "sin_verificar"
    if graphic.get("visible") is False or graphic.get("mode") == "limpio":
        return "imagen_limpia"
    if obs.get("source_active") is not True:
        return "fuera_de_programa" if obs.get("source_active") is False else "sin_verificar"
    if obs.get("streaming") is None:
        return "sin_verificar"
    return "al_aire" if obs.get("streaming") is True else "en_programa"


class OBSMonitor:
    POLL_SECONDS = 2.0
    STALE_SECONDS = 7.0

    def __init__(self, config_path, start_worker=True):
        self.path = Path(config_path)
        self.lock = threading.RLock()
        self.wake = threading.Event()
        self.config = {"port": 4455, "source_name": ""}
        self.password = ""  # Solo en memoria; nunca en el archivo ni en respuestas HTTP.
        self.generation = 0
        self.status = {"connected": False, "streaming": None, "source_active": None,
                       "error": "Configura la fuente de navegador de OBS", "checked_at": 0}
        try:
            saved = json.loads(self.path.read_text(encoding="utf-8"))
            self.config = self._validated(saved)
        except (ValueError, OSError, TypeError, KeyError):
            pass
        if start_worker:
            threading.Thread(target=self._worker, daemon=True, name="OBSReadOnlyMonitor").start()

    @staticmethod
    def _validated(value):
        if not isinstance(value, dict):
            raise ValueError("Configuración OBS inválida")
        port = value.get("port", 4455)
        if isinstance(port, bool) or str(port).strip() != str(int(port)):
            raise ValueError("Puerto OBS inválido")
        port = int(port)
        if not 1024 <= port <= 65535:
            raise ValueError("Puerto OBS fuera de rango")
        source = value.get("source_name", "")
        if not isinstance(source, str) or len(source) > 100:
            raise ValueError("Nombre de fuente OBS inválido")
        return {"port": port, "source_name": source.strip()}

    def configuration(self):
        with self.lock:
            return {**self.config, "has_password": bool(self.password)}

    def configure(self, values):
        updated = self._validated(values)
        password = values.get("password", None)
        if password is not None and (not isinstance(password, str) or len(password) > 256):
            raise ValueError("Contraseña OBS inválida")
        with self.lock:
            self.config = updated
            if password is not None:
                self.password = password
            self.generation += 1
            self.status = {"connected": False, "streaming": None, "source_active": None,
                           "error": "Comprobando conexión con OBS…", "checked_at": 0}
            self.path.write_text(json.dumps(updated, ensure_ascii=False, indent=2), encoding="utf-8")
        self.wake.set()
        return self.configuration()

    def get_status(self):
        with self.lock:
            state = dict(self.status)
            state["configured"] = bool(self.config["source_name"])
            state["source_name"] = self.config["source_name"]
            if state["connected"] and time.time() - state["checked_at"] > self.STALE_SECONDS:
                state.update(connected=False, streaming=None, source_active=None,
                             error="La comprobación con OBS ha caducado")
            return state

    def _worker(self):
        while True:
            with self.lock:
                config, password, generation = dict(self.config), self.password, self.generation
            if config["source_name"]:
                client = None
                try:
                    client = OBSWebSocket(config["port"], password)
                    stream = client.request("GetStreamStatus")
                    stream_active = stream.get("outputActive")
                    if not isinstance(stream_active, bool):
                        raise OBSConnectionError("OBS no confirmó el estado de transmisión")
                    reconnecting = stream.get("outputReconnecting") is True
                    state = {"connected": True, "streaming": None if reconnecting else stream_active,
                             "source_active": None, "error": "", "checked_at": time.time()}
                    if reconnecting:
                        state["error"] = "OBS está reconectando la transmisión"
                    try:
                        active = client.request("GetSourceActive", {"sourceName": config["source_name"]})
                        video_active = active.get("videoActive")
                        state["source_active"] = video_active if isinstance(video_active, bool) else None
                    except OBSRequestError:
                        state["source_active"] = False
                        state["error"] = "Comprueba el nombre de la fuente de navegador en OBS"
                except (OBSConnectionError, OSError, ValueError, KeyError, TypeError) as exc:
                    state = {"connected": False, "streaming": None, "source_active": None,
                             "error": str(exc) or "No se pudo conectar con OBS", "checked_at": time.time()}
                finally:
                    if client:
                        client.close()
                with self.lock:
                    if self.generation == generation:
                        self.status = state
            self.wake.wait(self.POLL_SECONDS)
            self.wake.clear()
