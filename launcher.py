"""Iniciador local para Producción Litúrgica OBS (Windows)."""
import os
import sys
import threading
import webbrowser
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from http.server import ThreadingHTTPServer

# Archivos HTML empaquetados con PyInstaller se leen desde _MEIPASS.
# Datos y multimedia permanecen junto al ejecutable.
APP_DIR = (Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "ProduccionLiturgicaOBS") if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
APP_DIR.mkdir(parents=True, exist_ok=True)
RES_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
os.environ["LITURGIA_APP_DIR"] = str(APP_DIR)
for filename in ("panel.html", "overlay.html", "dock.html", "studio.html", "login.html", "remote.html"):
    destination = APP_DIR / filename
    source = RES_DIR / filename
    if source.exists() and source.resolve() != destination.resolve():
        # Reemplazar recursos del programa en cada actualización, nunca medios o configuración del usuario.
        destination.write_bytes(source.read_bytes())
import servidor

HOST="127.0.0.1"
PORT=8765
PANEL=f"http://{HOST}:{PORT}/panel.html"
OVERLAY=f"http://{HOST}:{PORT}/overlay.html"

class Launcher:
    def __init__(self):
        self.root=tk.Tk()
        self.root.title("Producción Litúrgica OBS")
        self.root.geometry("390x240")
        self.root.resizable(False,False)
        self.root.protocol("WM_DELETE_WINDOW",self.minimize)
        self.server=None
        self.tray=None
        tk.Label(self.root,text="Producción Litúrgica OBS",font=("Segoe UI",17,"bold")).pack(pady=(18,8))
        self.status=tk.StringVar(value="Iniciando servidor...")
        tk.Label(self.root,textvariable=self.status,font=("Segoe UI",10)).pack(pady=6)
        tk.Button(self.root,text="Abrir panel de control",command=lambda:webbrowser.open(PANEL),width=29).pack(pady=4)
        tk.Button(self.root,text="Abrir vista OBS",command=lambda:webbrowser.open(OVERLAY),width=29).pack(pady=4)
        tk.Button(self.root,text="Cerrar sistema",command=self.confirm_exit,width=29).pack(pady=4)
        self.launch_server()
        self.configure_tray()
        self.root.after(1000,lambda:webbrowser.open(PANEL))
    def launch_server(self):
        try:
            self.server=ThreadingHTTPServer((HOST,PORT),servidor.Handler)
            self.worker=threading.Thread(target=self.server.serve_forever,daemon=True)
            self.worker.start()
            self.status.set("Servidor activo · 127.0.0.1:8765")
            servidor.LAN_RUNTIME=servidor.LANRuntime(servidor.LAN_ACCESS,servidor.Handler)
            try:
                servidor.LAN_RUNTIME.apply()
            except OSError as exc:
                servidor.LAN_RUNTIME.error=str(exc)
                self.status.set("Panel local activo · acceso LAN no disponible")
        except OSError:
            # Nunca se detiene un proceso externo: puede pertenecer a otra instancia.
            self.status.set("Puerto 8765 ocupado; revisa si el sistema ya está abierto.")
    def configure_tray(self):
        try:
            import pystray
            from PIL import Image,ImageDraw
            picture=Image.new("RGB",(64,64),"#142B42")
            draw=ImageDraw.Draw(picture)
            draw.ellipse((16,12,48,44),outline="#D9B979",width=4)
            def restore(icon,item):
                self.root.after(0,self.show)
            def exit_app(icon,item):
                self.root.after(0,self.confirm_exit)
            self.tray=pystray.Icon("LiturgiaOBS",picture,"Producción Litúrgica OBS",menu=pystray.Menu(
                pystray.MenuItem("Abrir panel",restore,default=True),
                pystray.MenuItem("Cerrar sistema",exit_app)))
            threading.Thread(target=self.tray.run,daemon=True).start()
        except ImportError:
            self.tray=None
    def show(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    def minimize(self):
        if self.tray:self.root.withdraw()
        else:self.root.iconify()
    def confirm_exit(self):
        if not messagebox.askyesno("Cerrar el sistema","¿Ha finalizado la transmisión? Al cerrar, OBS dejará de recibir los gráficos locales."):
            return
        if self.server:self.server.shutdown();self.server.server_close()
        if servidor.LAN_RUNTIME:servidor.LAN_RUNTIME.stop()
        if self.tray:self.tray.stop()
        self.root.destroy()
    def run(self):
        self.root.mainloop()

if __name__=="__main__":
    Launcher().run()
