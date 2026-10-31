"""Iniciador local para Producción Litúrgica OBS (Windows)."""
import os
import sys
import threading
import time
import json
from urllib.request import urlopen
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
for filename in ("panel.html", "overlay.html", "dock.html", "studio.html", "biblioteca.html", "login.html", "remote.html"):
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

def existing_panel_available():
    """No abrir el navegador si el puerto pertenece a otro servicio."""
    try:
        with urlopen(f"http://{HOST}:{PORT}/api/state", timeout=0.6) as response:
            state = json.load(response)
        return isinstance(state, dict) and "parish_name" in state and "mode" in state
    except (OSError, ValueError, TypeError):
        return False


def acquire_single_instance():
    """Mutex por sesión Windows: evita dos procesos controlando el mismo servidor."""
    if sys.platform != "win32":
        return None, True
    import ctypes
    kernel = ctypes.windll.kernel32
    kernel.CreateMutexW.argtypes = (ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p)
    kernel.CreateMutexW.restype = ctypes.c_void_p
    mutex = kernel.CreateMutexW(None, False, "Local\\ProduccionLiturgicaOBS-Servidor-8765")
    if not mutex:
        raise OSError("No se pudo comprobar la instancia del programa")
    return mutex, kernel.GetLastError() != 183


class Launcher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # No mostrar un segundo lanzador: el panel web es la interfaz.
        self.root.title("Producción Litúrgica OBS")
        self.root.geometry("390x180")
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        self.server = None
        self.tray = None
        self.error = None
        self.launch_server()
        if self.server is None:
            self.show_error(self.error or "No se pudo iniciar el servidor.")
            return
        self.configure_tray()
        if self.tray is None:
            # Sin icono de bandeja no se puede dejar el proceso invisible sin control.
            self.show_fallback()
        self.root.after(500, self.open_panel)

    def open_panel(self):
        webbrowser.open(PANEL)

    def launch_server(self):
        try:
            self.server = ThreadingHTTPServer((HOST, PORT), servidor.Handler)
            self.worker = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.worker.start()
            servidor.LAN_RUNTIME = servidor.LANRuntime(servidor.LAN_ACCESS, servidor.Handler)
            try:
                servidor.LAN_RUNTIME.apply()
            except OSError as exc:
                servidor.LAN_RUNTIME.error = str(exc)
        except OSError as exc:
            self.error = ("El puerto 8765 está ocupado por otro proceso. "
                          "Cierra ese programa antes de abrir Producción Litúrgica OBS. "
                          f"Detalle: {exc}")
            self.server = None

    def show_fallback(self):
        self.root.deiconify()
        tk.Label(self.root, text="Producción Litúrgica OBS", font=("Segoe UI", 15, "bold")).pack(pady=(18, 8))
        tk.Label(self.root, text="Servidor local activo · 127.0.0.1:8765").pack(pady=4)
        tk.Button(self.root, text="Abrir panel web", command=self.open_panel, width=28).pack(pady=4)
        tk.Button(self.root, text="Cerrar sistema", command=self.confirm_exit, width=28).pack(pady=4)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

    def show_error(self, message):
        self.root.deiconify()
        messagebox.showerror("Producción Litúrgica OBS", message, parent=self.root)
        self.root.destroy()

    def configure_tray(self):
        try:
            import pystray
            from PIL import Image, ImageDraw
            picture = Image.new("RGB", (64, 64), "#142B42")
            draw = ImageDraw.Draw(picture)
            draw.ellipse((16, 12, 48, 44), outline="#D9B979", width=4)

            def open_panel(icon, item):
                self.root.after(0, self.open_panel)

            def exit_app(icon, item):
                self.root.after(0, self.confirm_exit)

            self.tray = pystray.Icon(
                "LiturgiaOBS", picture, "Producción Litúrgica OBS",
                menu=pystray.Menu(
                    pystray.MenuItem("Abrir panel web", open_panel, default=True),
                    pystray.MenuItem("Cerrar sistema", exit_app),
                ),
            )
            threading.Thread(target=self.tray.run, daemon=True).start()
        except (ImportError, OSError):
            self.tray = None

    def hide_window(self):
        if self.tray:
            self.root.withdraw()
        else:
            self.root.iconify()

    def confirm_exit(self):
        if not messagebox.askyesno(
            "Cerrar el sistema",
            "¿Ha finalizado la transmisión? Al cerrar, OBS dejará de recibir los gráficos locales.",
            parent=self.root,
        ):
            return
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if servidor.LAN_RUNTIME:
            servidor.LAN_RUNTIME.stop()
        if self.tray:
            self.tray.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    mutex, first_instance = acquire_single_instance()
    if not first_instance:
        # La primera instancia puede estar terminando de arrancar.
        for _ in range(20):
            if existing_panel_available():
                webbrowser.open(PANEL)
                break
            time.sleep(0.25)
        else:
            messagebox.showerror(
                "Producción Litúrgica OBS",
                "El programa ya está iniciándose, pero su panel todavía no responde.",
            )
        return
    try:
        Launcher().run()
    finally:
        if mutex:
            import ctypes
            ctypes.windll.kernel32.CloseHandle(mutex)


if __name__ == "__main__":
    main()
