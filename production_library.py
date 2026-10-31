"""Biblioteca de gráficos organizada por producción, con datos locales independientes."""
import copy
import json
import os
import threading
import uuid
from pathlib import Path

TYPES = {
    "lower_third", "titulo", "lectura", "salmo", "aviso",
    "red_social", "frase", "logo", "qr", "pantalla", "temporizador",
    "credito", "patrocinador", "imagen", "video",
}
DEFAULT_ITEMS = [
    {"type": "lower_third", "name": "Celebrante (ejemplo)", "data": {"name": "P. Nombre Apellido", "role": "Celebrante"}},
    {"type": "lower_third", "name": "Lector (ejemplo)", "data": {"name": "Nombre de la persona", "role": "Primera lectura"}},
    {"type": "aviso", "name": "Aviso de ejemplo", "data": {"title": "Próxima actividad", "body": "Escribe aquí los detalles"}},
    {"type": "red_social", "name": "Instagram (ejemplo)", "data": {"network": "instagram", "handle": "@comunidad", "phrase": "Síguenos", "logo": ""}},
    {"type": "red_social", "name": "YouTube (ejemplo)", "data": {"network": "youtube", "handle": "Nuestro canal", "phrase": "Suscríbete y comparte", "logo": ""}},
    {"type": "frase", "name": "Comparte esta transmisión", "data": {"text": "Dale like y comparte"}},
]


def _text(value, length=180):
    if not isinstance(value, str):
        raise ValueError("El texto debe ser una cadena")
    return value.strip()[:length]


def _item(data, existing=None):
    if not isinstance(data, dict):
        raise ValueError("Elemento inválido")
    kind = data.get("type", existing["type"] if existing else None)
    if kind not in TYPES:
        raise ValueError("Tipo de gráfico no reconocido")
    if existing and kind != existing["type"]:
        raise ValueError("No se puede cambiar el tipo de un elemento")
    name = _text(data.get("name", existing["name"] if existing else ""), 110)
    if not name:
        raise ValueError("Indica un nombre")
    payload = data.get("data", existing["data"] if existing else {})
    if not isinstance(payload, dict) or len(payload) > 40:
        raise ValueError("Configuración del gráfico inválida")
    # La biblioteca guarda solo datos declarativos JSON, nunca HTML ejecutable.
    encoded = json.dumps(payload, ensure_ascii=False, allow_nan=False)
    if len(encoded.encode("utf-8")) > 12000:
        raise ValueError("Configuración demasiado grande")
    return {
        "id": existing["id"] if existing else uuid.uuid4().hex,
        "type": kind,
        "name": name,
        "enabled": bool(data.get("enabled", existing["enabled"] if existing else True)),
        "data": copy.deepcopy(payload),
    }


class ProductionLibrary:
    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.RLock()
        self.productions = []
        self.active_id = None
        self._load()

    def _load(self):
        try:
            saved = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(saved, dict) or not isinstance(saved.get("productions"), list):
                raise ValueError("Formato inválido")
            productions = []
            for production in saved["productions"][:80]:
                if not isinstance(production, dict):
                    continue
                items = [_item(entry) for entry in production.get("items", [])[:300]]
                for index, entry in enumerate(production.get("items", [])[:len(items)]):
                    if isinstance(entry, dict) and isinstance(entry.get("id"), str) and len(entry["id"]) == 32:
                        items[index]["id"] = entry["id"]
                productions.append({
                    "id": str(production["id"]),
                    "name": _text(production["name"], 110),
                    "items": items,
                })
            self.productions = productions
            self.active_id = saved.get("active_id")
            if not any(p["id"] == self.active_id for p in self.productions):
                self.active_id = self.productions[0]["id"] if self.productions else None
        except (OSError, ValueError, TypeError, KeyError):
            self.productions = []
        if not self.productions:
            first = {"id": uuid.uuid4().hex, "name": "Producción de ejemplo", "items": [_item(v) for v in DEFAULT_ITEMS]}
            self.productions = [first]
            self.active_id = first["id"]
            self._save()

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.snapshot(), ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)

    def snapshot(self):
        with self.lock:
            return copy.deepcopy({"active_id": self.active_id, "productions": self.productions})

    def _find(self, pid):
        found = next((p for p in self.productions if p["id"] == pid), None)
        if not found:
            raise ValueError("Producción inexistente")
        return found

    def get_item(self, pid, item_id):
        with self.lock:
            item = next((i for i in self._find(pid)["items"] if i["id"] == item_id), None)
            if item is None:
                raise ValueError("Elemento inexistente")
            if not item["enabled"]:
                raise ValueError("Este elemento está desactivado")
            return copy.deepcopy(item)

    def apply(self, request):
        if not isinstance(request, dict):
            raise ValueError("Solicitud inválida")
        with self.lock:
            action = request.get("action")
            pid = request.get("production_id", self.active_id)
            if action == "create_production":
                if len(self.productions) >= 80:
                    raise ValueError("Límite de producciones")
                name = _text(request.get("name", ""), 110)
                if not name:
                    raise ValueError("Indica un nombre")
                p = {"id": uuid.uuid4().hex, "name": name, "items": []}
                self.productions.append(p)
                self.active_id = p["id"]
            elif action == "select_production":
                self._find(pid)
                self.active_id = pid
            else:
                p = self._find(pid)
                items = p["items"]
                item_id = request.get("item_id")
                if action == "add":
                    if len(items) >= 300:
                        raise ValueError("Límite de gráficos por producción")
                    items.append(_item(request.get("item")))
                elif action in ("update", "duplicate", "delete", "move"):
                    idx = next((i for i, item in enumerate(items) if item["id"] == item_id), None)
                    if idx is None:
                        raise ValueError("Elemento inexistente")
                    if action == "update":
                        items[idx] = _item(request.get("item"), items[idx])
                    elif action == "duplicate":
                        if len(items) >= 300:
                            raise ValueError("Límite de gráficos por producción")
                        duplicate = _item({**items[idx], "name": items[idx]["name"] + " (copia)"})
                        items.insert(idx + 1, duplicate)
                    elif action == "delete":
                        items.pop(idx)
                    else:
                        target = request.get("index")
                        if not isinstance(target, int) or isinstance(target, bool) or not 0 <= target < len(items):
                            raise ValueError("Posición inválida")
                        items.insert(target, items.pop(idx))
                else:
                    raise ValueError("Acción no admitida")
            self._save()
            return self.snapshot()
