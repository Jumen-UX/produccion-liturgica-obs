from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
from pathlib import Path
import json, copy, time, uuid, re, threading, os

ROOT=Path(os.environ.get("LITURGIA_APP_DIR",Path(__file__).resolve().parent)).resolve()
DATA=ROOT/"configuracion.json"
LOCK=threading.RLock()
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
MODES={"espera","cintillo","lectura","salmo","evangelio","homilia","ofertorio","comunion","avisos","cierre","limpio","incidencia","participante","lower_third"}
THEMES={"ordinario","adviento","navidad","cuaresma","pascua","pentecostes","martires","blanco","rojo","verde","morado","rosa","negro","personalizado"}
MEDIA_RE=re.compile(r"^/media/[a-f0-9]{32}\.(?:png|jpg|webp|mp4|webm)$")
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
    def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
    def log_message(self,*a):pass
    def respond(self,value,status=200):
        b=json.dumps(value,ensure_ascii=False).encode("utf-8")
        self.send_response(status);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Cache-Control","no-store");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
    def do_GET(self):
        path=urlparse(self.path).path
        if path in ("/api/state","/api/draft"):
            with LOCK:self.respond(snapshot() if path=="/api/state" else copy.deepcopy(draft))
        else:super().do_GET()
    def do_POST(self):
        path=urlparse(self.path).path
        if path not in ("/api/update","/api/logo","/api/image","/api/logo-video"):return self.respond({"error":"Ruta inválida"},404)
        try:
            size=int(self.headers.get("Content-Length","0"))
            if size<1 or size>35*1024*1024:raise ValueError("Tamaño inválido")
            body=self.rfile.read(size)
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
            with LOCK:
                cmd=data.get("command")
                if cmd=="draft":draft.update(sanitized(data.get("updates",{})));persist()
                elif cmd=="publish":
                    for k in EDIT:live[k]=copy.deepcopy(draft[k])
                elif cmd=="social_show":live["social_now"]=True
                elif cmd=="social_hide":live["social_now"]=False
                elif cmd=="logo_toggle":live["logo_persistent"]=not live.get("logo_persistent",True)
                elif cmd=="clean":live.update(visible=False,mode="limpio")
                elif cmd=="restore":live.update(visible=True,mode=draft["mode"] if draft["mode"]!="limpio" else "cintillo")
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
                self.respond({"ok":True,"live":snapshot(),"draft":copy.deepcopy(draft)})
        except (ValueError,TypeError,KeyError,IndexError) as exc:self.respond({"error":str(exc)},400)
if __name__=="__main__":
    print("Panel: http://127.0.0.1:8765/panel.html",flush=True)
    ThreadingHTTPServer(("127.0.0.1",8765),Handler).serve_forever()
