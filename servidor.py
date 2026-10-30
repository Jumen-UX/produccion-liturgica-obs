from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from http.cookies import SimpleCookie, CookieError
from ipaddress import ip_address
import json, copy, time, uuid, re, threading, os
from obs_monitor import OBSMonitor, graphic_state
from lan_access import LANAccess, LANRuntime, local_addresses

ROOT=Path(os.environ.get("LITURGIA_APP_DIR",Path(__file__).resolve().parent)).resolve()
DATA=ROOT/"configuracion.json"
OBS_MONITOR=OBSMonitor(ROOT/"conexion_obs.json")
LAN_ACCESS=LANAccess(ROOT/"acceso_lan.json")
LAN_RUNTIME=None
LOCK=threading.RLock()
EVENT_CONDITION=threading.Condition()
EVENT_VERSION=0
def announce_change():
    global EVENT_VERSION
    with EVENT_CONDITION:
        EVENT_VERSION+=1
        EVENT_CONDITION.notify_all()
LOWER_DEFAULT={"template":"classic","enter":"fade","exit":"fade","duration":650,"opacity":94,"background":"#152941","accent":"#D6B678","name":"Nombre del participante","role":"Participante","subtitle":""}
LOWER_TEMPLATES={"classic","minimal","liturgical","modern"}
LOWER_EFFECTS={"fade","left","right","rise","zoom","none"}
def validated_lower_third(value):
    if not isinstance(value,dict):raise ValueError("Lower Third inválido")
    unknown=set(value)-set(LOWER_DEFAULT)
    if unknown:raise ValueError("Propiedad de Lower Third desconocida")
    result={**LOWER_DEFAULT,**value}
    if result["template"] not in LOWER_TEMPLATES:raise ValueError("Plantilla inválida")
    if result["enter"] not in LOWER_EFFECTS or result["exit"] not in LOWER_EFFECTS:raise ValueError("Animación inválida")
    for field in ("background","accent"):
        if not isinstance(result[field],str) or not re.fullmatch(r"#[a-fA-F0-9]{6}",result[field]):raise ValueError("Color inválido")
    for field,limit in (("name",85),("role",55),("subtitle",90)):
        result[field]=str(result[field])[:limit]
    result["duration"]=max(150,min(2500,int(result["duration"])))
    result["opacity"]=max(25,min(100,int(result["opacity"])))
    return result
DEFAULT={
"parish_name":"Mi parroquia","mode":"espera","title":"Santa Misa","subtitle":"Bienvenidos a nuestra celebración","detail":"Bienvenidos","reference":"","visible":True,"logo":"","ticker":"","ticker_visible":False,"announcements":["Gracias por acompañarnos","En breve comenzaremos"],"slides":[],"slides_enabled":True,"slide_interval":12,"cover_mode":"default","cover_image":"","social_enabled":False,"social_closing":True,"social_accounts":{"instagram":"","facebook":"","youtube":"","whatsapp":""},"social_qr":"","social_during_mass":False,"social_every":150,"social_duration":9,"social_now":None,"logo_persistent":True,"logo_video":"","participants":{"celebrante":"","diacono":"","lectores":["",""],"monitores":[""]},"role":"celebrante","role_index":0,"theme":"ordinario","colors":{"primary":"#2E986E","background":"#0A1C29","accent":"#D6B678","text":"#F4F7F9","panel":"#102C35"},"lower_third":copy.deepcopy(LOWER_DEFAULT),"timer_minutes":15,"remaining":900,"running":False,"end_at":None}
try:
    saved=json.loads(DATA.read_text(encoding="utf-8"))
    draft={**DEFAULT,**{k:v for k,v in saved.items() if k in DEFAULT and k not in ("running","end_at","remaining")}}
except (ValueError,OSError):
    draft=copy.deepcopy(DEFAULT)
try:draft["lower_third"]=validated_lower_third(draft.get("lower_third",{}))
except (ValueError,TypeError):draft["lower_third"]=copy.deepcopy(LOWER_DEFAULT)
live=copy.deepcopy(draft)
live.update(running=False,end_at=None,remaining=int(live["timer_minutes"])*60)
EDIT=set(DEFAULT)-{"running","end_at","remaining","logo","timer_minutes"}
# La restauración recupera la última salida visible, no el borrador en edición.
SCREEN_STATE_FIELDS=set(DEFAULT)-{"running","end_at","remaining","timer_minutes"}
last_visible_state=None
MODES={"espera","cintillo","lectura","salmo","evangelio","homilia","ofertorio","comunion","avisos","cierre","limpio","incidencia","participante","lower_third"}
THEMES={"ordinario","adviento","navidad","cuaresma","pascua","pentecostes","martires","blanco","rojo","verde","morado","rosa","negro","personalizado"}
MEDIA_RE=re.compile(r"^/media/[a-f0-9]{32}\.(?:png|jpg|webp|mp4|webm)$")
STATIC_PAGES={"/panel.html","/overlay.html","/dock.html","/studio.html","/login.html","/remote.html"}
REMOTE_READ={"/api/state","/api/draft","/api/obs-status","/api/session","/api/events"}
REMOTE_COMMANDS={"publish","launch","clean","restore","timer_start","timer_pause","timer_reset","social_show","social_hide","logo_toggle"}
def persist():
    DATA.write_text(json.dumps({k:v for k,v in draft.items() if k not in ("running","end_at","remaining")},ensure_ascii=False,indent=2),encoding="utf-8")
def snapshot():
    if live.get("running") and live.get("end_at"):
        live["remaining"]=max(0,round(live["end_at"]-time.time()))
        if not live["remaining"]:live.update(running=False,end_at=None)
    return {k:copy.deepcopy(v) for k,v in live.items() if k!="end_at"}
def sanitized(updates):
    if not isinstance(updates,dict):raise ValueError("Actualización inválida")
    out={}
    for k,v in updates.items():
        if k not in EDIT:continue
        if k=="mode" and v not in MODES:raise ValueError("Modo inválido")
        if k=="lower_third":
            if not isinstance(v,dict):raise ValueError("Lower Third inválido")
            v=validated_lower_third({**draft["lower_third"],**v})
        if k=="theme" and v not in THEMES:raise ValueError("Perfil inválido")
        if k=="colors":
            if not isinstance(v,dict) or any(not re.fullmatch(r"#[a-fA-F0-9]{6}",v.get(c,"")) for c in ("primary","background","accent","text","panel")):raise ValueError("Colores inválidos")
        if k=="participants":
            if not isinstance(v,dict):raise ValueError("Participantes inválidos")
            v={"celebrante":str(v.get("celebrante",""))[:110],"diacono":str(v.get("diacono",""))[:110],"lectores":[str(s)[:110] for s in v.get("lectores",[])[:12]],"monitores":[str(s)[:110] for s in v.get("monitores",[])[:12]]}
        if k=="slides":
            if not isinstance(v,list):raise ValueError("Avisos inválidos")
            v=[{"title":str(s.get("title",""))[:110],"body":str(s.get("body",""))[:350],"photo":s.get("photo","") if MEDIA_RE.fullmatch(str(s.get("photo",""))) else ""} for s in v[:24] if isinstance(s,dict)]
        if k in ("cover_image","logo_video","social_qr") and v and not MEDIA_RE.fullmatch(str(v)):raise ValueError("Archivo no autorizado")
        if k=="social_accounts":
            if not isinstance(v,dict):raise ValueError("Redes inválidas")
            v={s:str(v.get(s,""))[:160] for s in ("instagram","facebook","youtube","whatsapp")}
        if k=="slide_interval":v=max(4,min(90,int(v)))
        if k=="social_every":v=max(30,min(900,int(v)))
        if k=="social_duration":v=max(3,min(30,int(v)))
        if k=="role_index":v=max(0,min(11,int(v)))
        if k=="cover_mode" and v not in ("default","image"):raise ValueError("Portada inválida")
        if k=="role" and v not in ("celebrante","diacono","lectores","monitores"):raise ValueError("Cargo inválido")
        if k=="announcements":v=[str(x)[:180] for x in v[:12]] if isinstance(v,list) else []
        if k in ("social_enabled","social_closing","social_during_mass","logo_persistent","visible","ticker_visible","slides_enabled"):v=bool(v)
        if k=="parish_name":v=str(v).strip()[:100] or "Mi parroquia"
        out[k]=v
    return out
class Handler(SimpleHTTPRequestHandler):
    protocol_version="HTTP/1.1"
    def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
    def log_message(self,*a):pass
    @property
    def remote(self):return getattr(self.server,"lan_public",False)
    def end_headers(self):
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Referrer-Policy","no-referrer")
        self.send_header("X-Frame-Options","DENY" if self.remote else "SAMEORIGIN")
        self.send_header("Content-Security-Policy","default-src 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; frame-ancestors 'none'" if self.remote else "frame-ancestors 'self'")
        super().end_headers()
    def respond(self,value,status=200,headers=None):
        b=json.dumps(value,ensure_ascii=False).encode("utf-8")
        self.send_response(status);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Cache-Control","no-store");self.send_header("Content-Length",str(len(b)))
        for name,value in (headers or {}).items():self.send_header(name,value)
        self.end_headers();self.wfile.write(b)
    def trusted_host(self):
        host=self.headers.get("Host","")
        if not host or "@" in host or "/" in host:return False
        name,separator,port=host.rpartition(":")
        if not separator or not port.isdigit() or int(port)!=self.server.server_port:return False
        if not self.remote:return name in ("127.0.0.1","localhost")
        try:return name=="127.0.0.1" or (ip_address(name).version==4 and name in local_addresses())
        except ValueError:return False
    def same_origin(self):
        origin=self.headers.get("Origin")
        if self.remote and not origin:return False
        return not origin or origin=="http://"+self.headers.get("Host","")
    def token(self):
        try:
            cookie=SimpleCookie();cookie.load(self.headers.get("Cookie",""))
            return cookie["plobs_session"].value if "plobs_session" in cookie else ""
        except (CookieError,ValueError):return ""
    def role(self):return LAN_ACCESS.session_role(self.token()) if self.remote else "admin"
    def restricted(self,minimum="viewer"):
        role=self.role()
        if not role:
            self.respond({"error":"Inicia sesión para continuar"},401)
            return True
        if minimum=="operator" and role!="operator":
            self.respond({"error":"Permiso de operador requerido"},403)
            return True
        return False
    def do_HEAD(self):
        self.send_response(405);self.send_header("Content-Length","0");self.end_headers()
    def do_OPTIONS(self):self.respond({"error":"Método no disponible"},405)
    def serve_events(self):
        self.send_response(200)
        self.send_header("Content-Type","text/event-stream; charset=utf-8")
        self.send_header("Cache-Control","no-store")
        self.send_header("Connection","keep-alive")
        self.end_headers()
        # Las notificaciones no llevan datos personales; cada cliente consulta el estado vigente.
        previous=-1
        try:
            while LAN_ACCESS.session_role(self.token()):
                with EVENT_CONDITION:
                    EVENT_CONDITION.wait_for(lambda:EVENT_VERSION!=previous,timeout=1)
                    previous=EVENT_VERSION
                self.wfile.write(f"data: {previous}\n\n".encode("ascii"))
                self.wfile.flush()
        except (BrokenPipeError,ConnectionResetError,OSError):pass
    def do_GET(self):
        if not self.trusted_host():return self.respond({"error":"Host no autorizado"},421)
        parsed=urlparse(self.path);path=parsed.path
        if self.remote:
            if path=="/":path="/remote.html"
            if path in ("/login.html","/remote.html"):
                if path=="/remote.html" and self.restricted():return
                return super().do_GET() if parsed.path==path else self.serve_page(path)
            if path not in REMOTE_READ:return self.respond({"error":"Ruta no disponible en red"},404)
            if self.restricted():return
            if path=="/api/session":return self.respond({"role":self.role()})
            if path=="/api/events":return self.serve_events()
        elif path=="/api/lan/status":
            return self.respond(LAN_ACCESS.details(LAN_RUNTIME.error if LAN_RUNTIME else ""))
        elif path=="/api/lan/qr.svg":
            address=parse_qs(parsed.query).get("address",[""])[0]
            with LAN_ACCESS.lock:
                enabled,port=LAN_ACCESS.config["enabled"],LAN_ACCESS.config["port"]
            if not enabled or address not in local_addresses():return self.respond({"error":"Dirección LAN inválida"},404)
            try:
                import qrcode
                from qrcode.image.svg import SvgPathImage
                qr=qrcode.make(f"http://{address}:{port}/login.html",image_factory=SvgPathImage)
                from io import BytesIO
                buffer=BytesIO();qr.save(buffer);data=buffer.getvalue()
            except ImportError:return self.respond({"error":"Falta instalar la dependencia qrcode"},503)
            self.send_response(200);self.send_header("Content-Type","image/svg+xml");self.send_header("Cache-Control","no-store");self.send_header("Content-Length",str(len(data)));self.end_headers();return self.wfile.write(data)
        if path in ("/api/state","/api/draft"):
            with LOCK:self.respond(snapshot() if path=="/api/state" else copy.deepcopy(draft))
        elif path=="/api/obs-config":
            self.respond(OBS_MONITOR.configuration())
        elif path=="/api/obs-status":
            with LOCK:current=snapshot()
            status=OBS_MONITOR.get_status()
            status.update(graphic_status=graphic_state(current,status),graphic_mode=current.get("mode"),
                          graphic_title=current.get("lower_third",{}).get("name") if current.get("mode")=="lower_third" else current.get("title"))
            self.respond(status)
        elif not self.remote and (path in STATIC_PAGES or MEDIA_RE.fullmatch(path) or re.fullmatch(r"/logo_parroquial\.(png|jpg|webp)",path)):
            super().do_GET()
        else:self.respond({"error":"Archivo no disponible"},404)
    def serve_page(self,path):
        self.path=path
        return super().do_GET()
    def do_POST(self):
        global last_visible_state
        if not self.trusted_host():return self.respond({"error":"Host no autorizado"},421)
        if not self.same_origin():return self.respond({"error":"Origen no autorizado"},403)
        path=urlparse(self.path).path
        if self.remote:
            if path not in ("/api/login","/api/logout","/api/update"):
                return self.respond({"error":"Ruta no disponible en red"},404)
            if path=="/api/update" and self.restricted("operator"):return
            if path=="/api/logout":
                LAN_ACCESS.logout(self.token())
                return self.respond({"ok":True},headers={"Set-Cookie":"plobs_session=; Max-Age=0; HttpOnly; SameSite=Strict; Path=/"})
            if path=="/api/login":
                if self.headers.get("Content-Type","").split(";")[0]!="application/json":
                    return self.respond({"error":"Solo se acepta JSON"},415)
                try:
                    size=int(self.headers.get("Content-Length","0"))
                    if not 0<size<=1024:raise ValueError("Tamaño inválido")
                    credentials=json.loads(self.rfile.read(size))
                    if not isinstance(credentials,dict) or set(credentials)!={"password"}:
                        raise ValueError("Credenciales inválidas")
                    token,role=LAN_ACCESS.login(self.client_address[0],credentials["password"])
                except (ValueError,TypeError,KeyError) as exc:
                    return self.respond({"error":str(exc)},400)
                if not token:return self.respond({"error":role},429 if role.startswith("Demasiados") else 401)
                return self.respond({"ok":True,"role":role},headers={"Set-Cookie":f"plobs_session={token}; Max-Age=28800; HttpOnly; SameSite=Strict; Path=/"})
        elif path=="/api/lan/config":
            try:
                if self.headers.get("Content-Type","").split(";")[0]!="application/json":raise ValueError("Solo se acepta JSON")
                size=int(self.headers.get("Content-Length","0"))
                if not 0<size<=4096:raise ValueError("Tamaño inválido")
                values=json.loads(self.rfile.read(size))
                previous=LAN_ACCESS.configure(values)
                try:
                    if LAN_RUNTIME:LAN_RUNTIME.apply()
                except OSError as exc:
                    LAN_ACCESS.rollback(previous)
                    return self.respond({"error":"No se pudo abrir el puerto LAN: "+str(exc)},409)
                return self.respond({"ok":True,"config":LAN_ACCESS.details()})
            except (ValueError,TypeError,KeyError) as exc:return self.respond({"error":str(exc)},400)
        if path not in ("/api/update","/api/logo","/api/image","/api/logo-video","/api/obs-config"):return self.respond({"error":"Ruta inválida"},404)
        try:
            size=int(self.headers.get("Content-Length","0"))
            if size<1 or size>35*1024*1024:raise ValueError("Tamaño inválido")
            if path=="/api/obs-config" and size>4096:raise ValueError("Configuración OBS demasiado grande")
            if self.remote and (path!="/api/update" or size>4096):raise ValueError("Solicitud remota no permitida")
            if self.remote and self.headers.get("Content-Type","").split(";")[0]!="application/json":
                return self.respond({"error":"Solo se acepta JSON"},415)
            body=self.rfile.read(size)
            if path=="/api/obs-config":
                if self.headers.get("Content-Type","").split(";")[0]!="application/json":
                    raise ValueError("Solo se acepta JSON para conectar OBS")
                return self.respond({"ok":True,"config":OBS_MONITOR.configure(json.loads(body))})
            if path!="/api/update":
                kind=self.headers.get("Content-Type","").split(";")[0]
                image_types={"image/png":(b"\x89PNG\r\n\x1a\n","png"),"image/jpeg":(b"\xff\xd8\xff","jpg"),"image/webp":(b"RIFF","webp")}
                video_types={"video/mp4":(b"","mp4"),"video/webm":(bytes.fromhex("1a45dfa3"),"webm")}
                allowed=video_types if path=="/api/logo-video" else image_types
                if kind not in allowed or (allowed[kind][0] and not body.startswith(allowed[kind][0])):raise ValueError("Formato inválido")
                if kind=="video/mp4" and b"ftyp" not in body[:32]:raise ValueError("MP4 inválido")
                if kind=="image/webp" and body[8:12]!=b"WEBP":raise ValueError("WEBP inválido")
                ext=allowed[kind][1]
                if path=="/api/logo":
                    name="logo_parroquial."+ext
                    (ROOT/name).write_bytes(body)
                    with LOCK:
                        draft["logo"]="/"+name+"?v="+str(int(time.time()))
                        live["logo"]=draft["logo"];persist()
                    return self.respond({"ok":True,"logo":draft["logo"]})
                folder=ROOT/"media";folder.mkdir(exist_ok=True)
                name=uuid.uuid4().hex+"."+ext
                (folder/name).write_bytes(body)
                return self.respond({"ok":True,"url":"/media/"+name})
            data=json.loads(body)
            if self.remote and (not isinstance(data,dict) or data.get("command") not in REMOTE_COMMANDS):
                return self.respond({"error":"Comando no permitido en acceso remoto"},403)
            with LOCK:
                cmd=data.get("command")
                if cmd=="draft":draft.update(sanitized(data.get("updates",{})));persist()
                elif cmd=="publish":
                    if draft["mode"]=="incidencia" and data.get("confirm_incidence") is not True:
                        raise ValueError("Confirma expresamente el aviso de dificultades técnicas antes de mostrarlo")
                    for k in EDIT:live[k]=copy.deepcopy(draft[k])
                elif cmd=="launch":
                    mode=data.get("mode")
                    if mode not in ("espera","participante","lower_third"):raise ValueError("Gráfico no disponible para lanzamiento directo")
                    if mode=="espera" and draft["mode"]!="espera":raise ValueError("Prepara primero la pantalla de espera en el panel")
                    for k in EDIT:live[k]=copy.deepcopy(draft[k])
                    live.update(mode=mode,visible=True)
                elif cmd=="social_show":live["social_now"]=True
                elif cmd=="social_hide":live["social_now"]=False
                elif cmd=="logo_toggle":live["logo_persistent"]=not live.get("logo_persistent",True)
                elif cmd=="clean":
                    if live.get("visible") and live.get("mode")!="limpio":
                        last_visible_state={k:copy.deepcopy(live[k]) for k in SCREEN_STATE_FIELDS}
                    live.update(visible=False,mode="limpio")
                elif cmd=="restore":
                    if not live.get("visible") or live.get("mode")=="limpio":
                        if last_visible_state:
                            for k in SCREEN_STATE_FIELDS:live[k]=copy.deepcopy(last_visible_state[k])
                        live["visible"]=True
                elif cmd=="timer_set":
                    n=max(1,min(999,int(data.get("minutes",15))))
                    for obj in (draft,live):obj.update(timer_minutes=n,remaining=n*60,running=False,end_at=None)
                    persist()
                elif cmd=="timer_start":
                    if not live["running"] and live["remaining"]>0:live.update(running=True,end_at=time.time()+live["remaining"])
                elif cmd=="timer_pause":
                    if live["running"]:snapshot()
                    live.update(running=False,end_at=None)
                elif cmd=="timer_reset":live.update(running=False,end_at=None,remaining=live["timer_minutes"]*60)
                else:raise ValueError("Comando desconocido")
                announce_change()
                self.respond({"ok":True,"live":snapshot(),"draft":copy.deepcopy(draft)})
        except (ValueError,TypeError,KeyError,IndexError) as exc:self.respond({"error":str(exc)},400)
if __name__=="__main__":
    print("Panel: http://127.0.0.1:8765/panel.html",flush=True)
    LAN_RUNTIME=LANRuntime(LAN_ACCESS,Handler)
    try:LAN_RUNTIME.apply()
    except OSError as exc:print("Acceso LAN desactivado:",exc,flush=True);LAN_RUNTIME.error=str(exc)
    try:ThreadingHTTPServer(("127.0.0.1",8765),Handler).serve_forever()
    finally:LAN_RUNTIME.stop()
