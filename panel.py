import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import threading
import os
import sys
import json
import webbrowser

# Intentamos cargar pyngrok por si decides usar la opción de Ngrok
try:
    from pyngrok import ngrok
    NGROK_DISPONIBLE = True
except ImportError:
    NGROK_DISPONIBLE = False

CONFIG_FILE = "playtuve_config.json"

# --- LA FUNCIÓN MÁGICA PARA PYINSTALLER ---
def obtener_ruta_recurso(nombre_archivo):
    """
    Obtiene la ruta absoluta del recurso.
    Funciona tanto en desarrollo normal como compilado en un .exe
    """
    try:
        # Si está compilado, PyInstaller extrae los datos aquí:
        ruta_base = sys._MEIPASS
    except Exception:
        # Si no está compilado, usa la carpeta actual:
        ruta_base = os.path.abspath(".")
    
    return os.path.join(ruta_base, nombre_archivo)


class PlayTuveDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("PlayTuve - Centro de Control Híbrido")
        self.root.geometry("700x580")
        self.root.resizable(False, False)
        
        # Estética Oscura / Rojo PlayTuve
        self.bg_color = "#121212"
        self.card_color = "#1e1e1e"
        self.accent_color = "#ff3333"
        self.text_color = "#ffffff"
        self.root.configure(bg=self.bg_color)
        
        # Control de procesos
        self.proceso_servidor = None
        self.proceso_playit = None
        self.ngrok_tunnel = None
        self.hilo_lectura = None
        
        # Cargar configuración
        self.config = self._cargar_config()
        self._crear_interfaz()

    def _cargar_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"ngrok_token": ""}

    def _guardar_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f)

    def _crear_interfaz(self):
        lbl_titulo = tk.Label(
            self.root, text="🕹️ PLAYTUVE - DASHBOARD DE CONTROL", 
            font=("Arial", 14, "bold"), bg=self.bg_color, fg=self.accent_color
        )
        lbl_titulo.pack(pady=15)

        frame_servidores = tk.LabelFrame(
            self.root, text=" Modos de Hospedaje ", font=("Arial", 9, "bold"),
            bg=self.bg_color, fg="#aaaaaa", bd=1, padx=10, pady=10
        )
        frame_servidores.pack(fill="x", padx=20, pady=5)

        self.btn_local = tk.Button(
            frame_servidores, text="🌐 Modo Local (WiFi)", font=("Arial", 9, "bold"),
            bg=self.card_color, fg=self.text_color, activebackground="#333333", activeforeground="white",
            width=18, pady=8, bd=0, cursor="hand2", command=self.iniciar_local
        )
        self.btn_local.pack(side="left", padx=10)

        self.btn_playit = tk.Button(
            frame_servidores, text="🚀 Modo Público (Playit)", font=("Arial", 9, "bold"),
            bg=self.card_color, fg=self.text_color, activebackground="#333333", activeforeground="white",
            width=20, pady=8, bd=0, cursor="hand2", command=self.iniciar_playit
        )
        self.btn_playit.pack(side="left", padx=10)

        self.btn_ngrok = tk.Button(
            frame_servidores, text="🔥 Modo Público (Ngrok)", font=("Arial", 9, "bold"),
            bg=self.card_color, fg=self.text_color, activebackground="#333333", activeforeground="white",
            width=20, pady=8, bd=0, cursor="hand2", command=self.iniciar_ngrok
        )
        self.btn_ngrok.pack(side="left", padx=10)

        frame_herramientas = tk.Frame(self.root, bg=self.bg_color)
        frame_herramientas.pack(fill="x", padx=20, pady=15)

        self.btn_config = tk.Button(
            frame_herramientas, text="⚙️ Configuración", font=("Arial", 9, "bold"),
            bg="#333333", fg="white", activebackground="#555555", activeforeground="white",
            width=16, pady=8, bd=0, cursor="hand2", command=self.abrir_configuracion
        )
        self.btn_config.pack(side="left", padx=(0, 5))

        self.btn_limpiar = tk.Button(
            frame_herramientas, text="🗑️ Vaciar Residuos", font=("Arial", 9, "bold"),
            bg="#4d0000", fg="white", activebackground="#800000", activeforeground="white",
            width=18, pady=8, bd=0, cursor="hand2", command=self.limpiar_residuos
        )
        self.btn_limpiar.pack(side="left", padx=5)

        self.btn_apagar = tk.Button(
            frame_herramientas, text="🛑 APAGAR TODO", font=("Arial", 9, "bold"),
            bg=self.accent_color, fg="white", activebackground="#cc0000", activeforeground="white",
            width=18, pady=8, bd=0, cursor="hand2", state="disabled", command=self.apagar_servidor
        )
        self.btn_apagar.pack(side="right")

        lbl_logs = tk.Label(self.root, text="Logs del Sistema en Tiempo Real:", bg=self.bg_color, fg="#888888", font=("Arial", 9))
        lbl_logs.pack(anchor="w", padx=20, pady=(10, 0))
        
        self.consola = scrolledtext.ScrolledText(
            self.root, height=15, bg="#000000", fg="#33ff33", 
            font=("Consolas", 9), bd=0, padx=10, pady=10, state="disabled"
        )
        self.consola.pack(fill="both", padx=20, pady=5, expand=True)

    def log(self, mensaje):
        self.consola.config(state="normal")
        self.consola.insert(tk.END, mensaje + "\n")
        self.consola.see(tk.END)
        self.consola.config(state="disabled")

    def abrir_configuracion(self):
        ventana_cfg = tk.Toplevel(self.root)
        ventana_cfg.title("Configuración de Servicios")
        ventana_cfg.geometry("450x250")
        ventana_cfg.configure(bg=self.bg_color)
        ventana_cfg.resizable(False, False)

        tk.Label(ventana_cfg, text="Authtoken de Ngrok:", bg=self.bg_color, fg="white", font=("Arial", 10, "bold")).pack(pady=(20, 5))
        
        entry_token = tk.Entry(ventana_cfg, width=50, bg=self.card_color, fg="white", bd=1, insertbackground="white")
        entry_token.pack(pady=5)
        entry_token.insert(0, self.config.get("ngrok_token", ""))

        def guardar():
            self.config["ngrok_token"] = entry_token.get().strip()
            self._guardar_config()
            messagebox.showinfo("Guardado", "Authtoken guardado correctamente.", parent=ventana_cfg)
            ventana_cfg.destroy()

        tk.Button(
            ventana_cfg, text="💾 Guardar Token", bg=self.accent_color, fg="white", bd=0, 
            padx=15, pady=5, cursor="hand2", command=guardar
        ).pack(pady=10)

        tk.Label(ventana_cfg, text="¿No tienes cuenta de Ngrok?", bg=self.bg_color, fg="#aaaaaa").pack(pady=(15, 0))
        tk.Button(
            ventana_cfg, text="Obtener Authtoken aquí", bg=self.bg_color, fg="#3399ff", bd=0, 
            cursor="hand2", command=lambda: webbrowser.open("https://dashboard.ngrok.com/get-started/your-authtoken")
        ).pack()

    def _leer_consola_flask(self):
        if self.proceso_servidor:
            for linea in iter(self.proceso_servidor.stdout.readline, ''):
                self.log(linea.strip())
            self.proceso_servidor.stdout.close()

    def _arrancar_flask_base(self):
        ruta_app = obtener_ruta_recurso("app.py")
        self.proceso_servidor = subprocess.Popen(
            ["python", ruta_app],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        self.hilo_lectura = threading.Thread(target=self._leer_consola_flask, daemon=True)
        self.hilo_lectura.start()

    def iniciar_local(self):
        if self.proceso_servidor: return
        self.consola.config(state="normal")
        self.consola.delete("1.0", tk.END)
        self.log(">>> Levantando backend en Red Local...")
        self._arrancar_flask_base()
        self._conmutar_botones(activo=True)

    def iniciar_playit(self):
        if self.proceso_servidor: return
        
        # Usamos la ruta protegida por si estamos compilados en .exe
        ruta_playit = obtener_ruta_recurso("playit.exe")
        
        if not os.path.exists(ruta_playit):
            respuesta = messagebox.askyesno(
                "Playit no encontrado", 
                "No se encontró 'playit.exe'.\n\n"
                "¿Deseas abrir la página oficial para descargarlo? (Recuerda renombrarlo y ponerlo junto al panel)"
            )
            if respuesta:
                webbrowser.open("https://playit.gg/download")
            return

        self.consola.config(state="normal")
        self.consola.delete("1.0", tk.END)
        self.log(">>> Lanzando servidor Flask...")
        self._arrancar_flask_base()
        
        self.log(">>> Abriendo agente Playit.gg...")
        self.proceso_playit = subprocess.Popen(
            [ruta_playit],
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
        self._conmutar_botones(activo=True)

    def iniciar_ngrok(self):
        if self.proceso_servidor: return
        if not NGROK_DISPONIBLE:
            messagebox.showerror("Librería Faltante", "Instala pyngrok:\npip install pyngrok")
            return

        token = self.config.get("ngrok_token", "")
        if not token:
            messagebox.showwarning("Falta Authtoken", "Ve a '⚙️ Configuración' y guarda tu Authtoken de Ngrok primero.")
            return

        self.consola.config(state="normal")
        self.consola.delete("1.0", tk.END)
        self.log(">>> Solicitando túnel dinámico a Ngrok...")
        
        try:
            ngrok.set_auth_token(token)
            self.ngrok_tunnel = ngrok.connect(5000)
            url_publica = self.ngrok_tunnel.public_url
            
            self.log("=" * 60)
            self.log(f"🌍 LINK PÚBLICO NGROK: {url_publica}")
            self.log("=" * 60)
            
            self._arrancar_flask_base()
            self._conmutar_botones(activo=True)
        except Exception as e:
            self.log(f"❌ Error al mapear Ngrok: {str(e)}")

    def apagar_servidor(self):
        self.log("\n>>> Iniciando apagado controlado...")
        
        if self.proceso_servidor:
            self.proceso_servidor.terminate()
            self.proceso_servidor.wait()
            self.proceso_servidor = None
            self.log("✅ Servidor Flask detenido.")
            
        if self.proceso_playit:
            self.proceso_playit.terminate()
            self.proceso_playit = None
            self.log("✅ Túnel Playit cerrado.")
            
        if self.ngrok_tunnel:
            ngrok.disconnect(self.ngrok_tunnel.public_url)
            self.ngrok_tunnel = None
            self.log("✅ Túnel Ngrok destruido.")
            
        self._conmutar_botones(activo=False)

    def limpiar_residuos(self):
        ruta_descargas = os.path.join(os.getcwd(), "descargas")
        if not os.path.exists(ruta_descargas):
            self.log(">>> Escaneo: Carpeta vacía.")
            return
            
        archivos = [f for f in os.listdir(ruta_descargas) if f.endswith('.m4a')]
        if not archivos:
            self.log(">>> Escaneo: 0 residuos detectados.")
            return
            
        confirmar = messagebox.askyesno("Limpiar", f"¿Eliminar {len(archivos)} residuos?")
        if confirmar:
            eliminados = 0
            for archivo in archivos:
                try:
                    os.remove(os.path.join(ruta_descargas, archivo))
                    eliminados += 1
                except Exception:
                    pass
            self.log(f"🗑️ Limpieza: {eliminados} archivos removidos.")

    def _conmutar_botones(self, activo):
        estado_inversor = "disabled" if activo else "normal"
        self.btn_local.config(state=estado_inversor)
        self.btn_playit.config(state=estado_inversor)
        self.btn_ngrok.config(state=estado_inversor)
        self.btn_apagar.config(state="normal" if activo else "disabled")

def al_cerrar_ventana():
    if dashboard.proceso_servidor or dashboard.proceso_playit or dashboard.ngrok_tunnel:
        dashboard.apagar_servidor()
    ventana.destroy()

if __name__ == "__main__":
    ventana = tk.Tk()
    dashboard = PlayTuveDashboard(ventana)
    ventana.protocol("WM_DELETE_WINDOW", al_cerrar_ventana)
    ventana.mainloop()