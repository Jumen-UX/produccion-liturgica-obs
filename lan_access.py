"""Acceso LAN opcional, aislado del servicio local de OBS.

Solo se exponen el lanzador remoto y las consultas necesarias. La identidad
administrativa siempre permanece en el puerto de loopback.
"""

from collections import defaultdict, deque
from http.server import ThreadingHTTPServer
from ipaddress import ip_address
from pathlib import Path
import copy
import hashlib
import hmac
import json
import secrets
import socket
import threading
import time


ITERATIONS = 310_000
SESSION_SECONDS = 8 * 60 * 60
ATTEMPT_WINDOW = 5 * 60
MAX_ATTEMPTS = 5


def local_addresses():
    """Direcciones IPv4 locales para mostrar; no hace consultas a Internet."""
    addresses = set()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("192.0.2.1", 9))
            addresses.add(sock.getsockname()[0])
    except OSError:
        pass
    try:
        for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            addresses.add(item[4][0])
    except OSError:
        pass
    return sorted(address for address in addresses if ip_address(address).is_private
                  and not ip_address(address).is_loopback and not ip_address(address).is_link_local)


def _verifier(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return {"salt": salt.hex(), "digest": digest.hex()}


class LANAccess:
    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.RLock()
        self.sessions = {}
        self.failures = defaultdict(deque)
        self.config = {"enabled": False, "port": 8766, "operator": None, "viewer": None}
        try:
            saved = json.loads(self.path.read_text(encoding="utf-8"))
            port = saved["port"]
            if type(port) is int and 1024 <= port <= 65535 and port not in (8765, 4455):
                for role in ("operator", "viewer"):
                    value = saved.get(role)
                    if value is not None:
                        if not isinstance(value, dict):
                            raise ValueError("Credencial inválida")
                        for key, length in (("salt", 32), ("digest", 64)):
                            try:
                                if len(value[key]) != length or len(bytes.fromhex(value[key])) * 2 != length:
                                    raise ValueError("Credencial inválida")
                            except (KeyError, TypeError):
                                raise ValueError("Credencial inválida")
                self.config = {"enabled": saved.get("enabled") is True and bool(saved.get("operator")),
                               "port": port, "operator": saved.get("operator"), "viewer": saved.get("viewer")}
        except (OSError, ValueError, KeyError, TypeError):
            pass

    def _persist(self):
        self.path.write_text(json.dumps(self.config, indent=2), encoding="utf-8")
        try:
            self.path.chmod(0o600)
        except OSError:
            pass

    def configure(self, values):
        if not isinstance(values, dict) or set(values) - {"enabled", "port", "operator_password", "viewer_password", "revoke_sessions"}:
            raise ValueError("Configuración LAN inválida")
        with self.lock:
            previous = copy.deepcopy(self.config)
            port = values.get("port", previous["port"])
            if type(port) is not int or port < 1024 or port > 65535 or port in (8765, 4455):
                raise ValueError("Selecciona un puerto entre 1024 y 65535, distinto de 8765 y 4455")
            updated = {**previous, "port": port}
            for role in ("operator", "viewer"):
                key = role + "_password"
                if key in values:
                    password = values[key]
                    if not isinstance(password, str) or (password and not 12 <= len(password) <= 128):
                        raise ValueError("La contraseña debe tener entre 12 y 128 caracteres")
                    if role == "operator" and not password:
                        raise ValueError("El operador necesita una contraseña")
                    updated[role] = _verifier(password) if password else None
            if "enabled" in values:
                if type(values["enabled"]) is not bool:
                    raise ValueError("Estado LAN inválido")
                updated["enabled"] = values["enabled"]
            if updated["enabled"] and not updated["operator"]:
                raise ValueError("Define primero la contraseña del operador")
            if "revoke_sessions" in values and type(values["revoke_sessions"]) is not bool:
                raise ValueError("Acción de revocación inválida")
            self.config = updated
            if updated != previous or values.get("revoke_sessions"):
                self.sessions.clear()
            self._persist()
            return previous

    def rollback(self, previous):
        with self.lock:
            self.config = previous
            self._persist()

    def details(self, server_error=""):
        with self.lock:
            port = self.config["port"]
            return {"enabled": self.config["enabled"], "port": port,
                    "operator_configured": bool(self.config["operator"]),
                    "viewer_configured": bool(self.config["viewer"]),
                    "sessions": len(self.sessions), "error": server_error,
                    "urls": [f"http://{address}:{port}/login.html" for address in local_addresses()]
                    if self.config["enabled"] and not server_error else []}

    def _matches(self, password, verifier):
        if not verifier:
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                                     bytes.fromhex(verifier["salt"]), ITERATIONS)
        return hmac.compare_digest(digest, bytes.fromhex(verifier["digest"]))

    def login(self, address, password):
        if not isinstance(password, str) or len(password) > 128:
            return None, "Credenciales inválidas"
        now = time.monotonic()
        with self.lock:
            if not self.config["enabled"]:
                return None, "Acceso remoto desactivado"
            failures = self.failures[address]
            while failures and now - failures[0] > ATTEMPT_WINDOW:
                failures.popleft()
            if len(failures) >= MAX_ATTEMPTS:
                return None, "Demasiados intentos. Espera cinco minutos"
            # Dos verificaciones para evitar pistas sobre el rol existente.
            operator = self._matches(password, self.config["operator"])
            viewer = self._matches(password, self.config["viewer"])
            role = "operator" if operator else "viewer" if viewer else None
            if role is None:
                failures.append(now)
                return None, "Credenciales inválidas"
            failures.clear()
            for token, session in list(self.sessions.items()):
                if session["expires"] < now:
                    del self.sessions[token]
            if len(self.sessions) >= 64:
                return None, "Límite de dispositivos conectados"
            token = secrets.token_urlsafe(32)
            self.sessions[token] = {"role": role, "expires": now + SESSION_SECONDS}
            return token, role

    def session_role(self, token):
        with self.lock:
            if not self.config["enabled"]:
                return None
            session = self.sessions.get(token)
            if not session:
                return None
            if session["expires"] < time.monotonic():
                self.sessions.pop(token, None)
                return None
            return session["role"]

    def logout(self, token):
        with self.lock:
            self.sessions.pop(token, None)


class LANServer(ThreadingHTTPServer):
    daemon_threads = True
    lan_public = True


class LANRuntime:
    def __init__(self, access, handler):
        self.access = access
        self.handler = handler
        self.server = None
        self.error = ""
        self.lock = threading.RLock()

    def apply(self):
        with self.lock:
            config = self.access.config
            if config["enabled"]:
                if self.server and self.server.server_port == config["port"]:
                    self.error = ""
                    return
                server = LANServer(("0.0.0.0", config["port"]), self.handler)
                threading.Thread(target=server.serve_forever, daemon=True, name="OBSRemoteLAN").start()
            else:
                server = None
            old, self.server = self.server, server
            self.error = ""
            if old:
                old.shutdown()
                old.server_close()

    def stop(self):
        with self.lock:
            if self.server:
                self.server.shutdown()
                self.server.server_close()
                self.server = None
