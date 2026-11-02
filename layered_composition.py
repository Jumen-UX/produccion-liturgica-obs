"""Composiciones declarativas para pantallas de espera 1920x1080.

Los mismos datos validados se usan en el editor, la vista previa y la salida OBS.
"""
import copy
import json
import re

WIDTH, HEIGHT = 1920, 1080
KINDS = {"background", "text", "liturgy", "timer", "logo", "image", "shape"}
EFFECTS = {"none", "fade", "left", "right", "rise", "zoom"}
MEDIA = re.compile(r"/media/[a-f0-9]{32}\.(?:png|jpg|webp|mp4|webm)$")
PARISH_LOGO = re.compile(r"/logo_parroquial\.(?:png|jpg|webp)(?:\?v=\d+)?$")
COLOR = re.compile(r"#[A-Fa-f0-9]{6}$")
LAYER_ID = re.compile(r"[a-zA-Z0-9_-]{1,45}$")


def starter_composition():
    """Plantilla editable; no depende de nombres ni logos de una parroquia concreta."""
    return {
        "version": 1, "minutes": 15,
        "layers": [
            {"id": "fondo", "type": "background", "name": "Fondo", "x": 0, "y": 0,
             "w": WIDTH, "h": HEIGHT, "fill": "#102635", "locked": True},
            {"id": "titulo", "type": "text", "name": "Bienvenida", "x": 110, "y": 295,
             "w": 850, "h": 175, "text": "Bienvenidos a nuestra celebración",
             "fontSize": 64, "fontWeight": 700},
            {"id": "liturgia", "type": "liturgy", "name": "Liturgia del día", "x": 115, "y": 520,
             "w": 790, "h": 120, "text": "Celebración eucarística", "fontSize": 38,
             "color": "#E1C58C"},
            {"id": "reloj", "type": "timer", "name": "Cuenta regresiva", "x": 1150,
             "y": 275, "w": 510, "h": 510, "timerStyle": "circle", "color": "#D6B678"},
            {"id": "logo", "type": "logo", "name": "Logo parroquial", "x": 95,
             "y": 80, "w": 160, "h": 160},
        ],
    }


def _number(value, name, minimum, maximum, integer=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name}: número inválido")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name}: fuera de los límites")
    return int(value) if integer else round(float(value), 3)


def _color(value, name):
    if not isinstance(value, str) or not COLOR.fullmatch(value):
        raise ValueError(f"{name}: color inválido")
    return value


def validate_composition(data):
    if not isinstance(data, dict) or set(data) - {"version", "minutes", "layers"}:
        raise ValueError("Composición inválida")
    if data.get("version") != 1:
        raise ValueError("Versión de composición no admitida")
    minutes = _number(data.get("minutes"), "Minutos", 1, 999, True)
    source = data.get("layers")
    if not isinstance(source, list) or not 1 <= len(source) <= 30:
        raise ValueError("La composición requiere entre 1 y 30 capas")
    layers = []
    ids = set()
    allowed = {"id", "type", "name", "x", "y", "w", "h", "visible", "locked", "opacity",
               "text", "color", "fill", "fontSize", "fontWeight", "align", "asset",
               "fit", "timerStyle", "enter", "exit", "duration"}
    for raw in source:
        if not isinstance(raw, dict) or set(raw) - allowed:
            raise ValueError("Propiedad de capa no admitida")
        ident = raw.get("id")
        if not isinstance(ident, str) or not LAYER_ID.fullmatch(ident) or ident in ids:
            raise ValueError("Cada capa necesita un identificador único")
        ids.add(ident)
        kind = raw.get("type")
        if kind not in KINDS:
            raise ValueError("Tipo de capa no admitido")
        name = raw.get("name", kind)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Cada capa necesita un nombre")
        x = _number(raw.get("x"), "X", 0, WIDTH, True)
        y = _number(raw.get("y"), "Y", 0, HEIGHT, True)
        w = _number(raw.get("w"), "Ancho", 30, WIDTH, True)
        h = _number(raw.get("h"), "Alto", 20, HEIGHT, True)
        if x + w > WIDTH or y + h > HEIGHT:
            raise ValueError("La capa debe permanecer dentro del lienzo")
        asset = raw.get("asset", "")
        if not isinstance(asset, str) or (asset and not MEDIA.fullmatch(asset) and
                                        not (kind == "logo" and PARISH_LOGO.fullmatch(asset))):
            raise ValueError("Archivo de capa no autorizado")
        if kind == "background" and asset and not MEDIA.fullmatch(asset):
            raise ValueError("Fondo no autorizado")
        if kind == "background" and (x, y, w, h) != (0, 0, WIDTH, HEIGHT):
            raise ValueError("El fondo debe cubrir todo el lienzo")
        color = _color(raw.get("color", "#FFFFFF"), "Texto")
        fill = _color(raw.get("fill", "#102635"), "Fondo")
        text = raw.get("text", "")
        if not isinstance(text, str):
            raise ValueError("Texto inválido")
        text = text[:500]
        weight = raw.get("fontWeight", 600)
        if weight not in (400, 500, 600, 700, 800):
            raise ValueError("Grosor de fuente inválido")
        align = raw.get("align", "left")
        if align not in ("left", "center", "right"):
            raise ValueError("Alineación inválida")
        fit = raw.get("fit", "contain")
        if fit not in ("contain", "cover"):
            raise ValueError("Ajuste de imagen inválido")
        timer_style = raw.get("timerStyle", "circle")
        if timer_style not in ("circle", "digital", "bar"):
            raise ValueError("Estilo de cuenta regresiva inválido")
        enter, leave = raw.get("enter", "fade"), raw.get("exit", "fade")
        if enter not in EFFECTS or leave not in EFFECTS:
            raise ValueError("Animación de capa inválida")
        layers.append({
            "id": ident, "type": kind, "name": name.strip()[:85], "x": x, "y": y,
            "w": w, "h": h, "visible": bool(raw.get("visible", True)),
            "locked": kind == "background" or bool(raw.get("locked", False)),
            "opacity": _number(raw.get("opacity", 1), "Opacidad", 0, 1),
            "text": text, "color": color, "fill": fill,
            "fontSize": _number(raw.get("fontSize", 54), "Fuente", 16, 180, True),
            "fontWeight": weight, "align": align, "asset": asset, "fit": fit,
            "timerStyle": timer_style, "enter": enter, "exit": leave,
            "duration": _number(raw.get("duration", 650), "Duración", 150, 2500, True),
        })
    # Una única capa de fondo, situada detrás de todos los elementos.
    if layers[0]["type"] != "background" or sum(
        layer["type"] == "background" for layer in layers
    ) != 1:
        raise ValueError("La composición requiere un único fondo como primera capa")
    # Sólo datos JSON sencillos. Nunca HTML, CSS ni enlaces arbitrarios.
    if len(json.dumps(layers, ensure_ascii=False).encode("utf-8")) > 30000:
        raise ValueError("La composición contiene demasiados datos")
    return {"version": 1, "minutes": minutes, "layers": copy.deepcopy(layers)}
