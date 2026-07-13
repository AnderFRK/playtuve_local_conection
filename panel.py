import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import threading
import os
import sys
import json
import webbrowser
import socket

try:
    from pyngrok import ngrok
    NGROK_DISPONIBLE = True
except ImportError:
    NGROK_DISPONIBLE = False

CONFIG_FILE = "playtuve_config.json"

def obtener_ruta_recurso(nombre_archivo):
    try:
        ruta_base = sys._MEIPASS
    except Exception:
        ruta_base = os.path.abspath(".")
    return os.path.join(ruta_base, nombre_archivo)


class PlayTuveDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("PlayTuve - Centro de Control Híbrido")
        self.root.geometry("700x680") 
        self.root.resizable(False, False)
        
        self.bg_color = "#121212"
        self.card_color = "#1e1e1e"
        self.accent_color = "#ff3333"
        self.text_color = "#ffffff"
        self.root.configure(bg=self.bg_color)
        
        self.proceso_servidor = None
        self.proceso_playit = None
        self.proceso_ssh = None
        self.ngrok_tunnel = None
        self.hilo_lectura = None
        self.hilo_ssh = None
        
        self.config = self._cargar_config()
        self._crear_interfaz()

    def _cargar_config(self):
        # Añadimos "navegador" por defecto
        config_default = {"ngrok_token": "", "navegador": "firefox"}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    config_default.update(data) # Combina lo guardado con lo default
                    return config_default
            except Exception:
                pass
        return config_default

    def _guardar_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f)

    def _crear_interfaz(self):
        lbl_titulo = tk.Label(
            self.root, text="🕹️ PLAYTUVE - DASHBOARD DE CONTROL", 
            font=("Arial", 14, "bold"), bg=self.bg_color, fg=self.accent_color
        )
        lbl_titulo.pack(pady=10)

        # 1. BOTONES DE SERVIDORES
        frame_servidores = tk.LabelFrame(
            self.root, text=" Modos de Hospedaje ", font=("Arial", 9, "bold"),
            bg=self.bg_color, fg="#aaaaaa", bd=1, padx=20, pady=10
        )
        frame_servidores.pack(fill="x", padx=20, pady=5)
        frame_servidores.columnconfigure(0, weight=1)
        frame_servidores.columnconfigure(1, weight=1)

        self.btn_local = tk.Button(
            frame_servidores, text="🌐 Modo Local (WiFi)", font=("Arial", 9, "bold"),
            bg=self.card_color, fg=self.text_color, activebackground="#333333", activeforeground="white",
            width=25, pady=8, bd=0, cursor="hand2", command=self.iniciar_local
        )
        self.btn_local.grid(row=0, column=0, padx=10, pady=5)

        self.btn_playit = tk.Button(
            frame_servidores, text="🚀 Modo Público (Playit)", font=("Arial", 9, "bold"),
            bg=self.card_color, fg=self.text_color, activebackground="#333333", activeforeground="white",
            width=25, pady=8, bd=0, cursor="hand2", command=self.iniciar_playit
        )
        self.btn_playit.grid(row=0, column=1, padx=10, pady=5)

        self.btn_ngrok = tk.Button(
            frame_servidores, text="🔥 Modo Público (Ngrok)", font=("Arial", 9, "bold"),
            bg=self.card_color, fg=self.text_color, activebackground="#333333", activeforeground="white",
            width=25, pady=8, bd=0, cursor="hand2", command=self.iniciar_ngrok
        )
        self.btn_ngrok.grid(row=1, column=0, padx=10, pady=5)

        self.btn_ssh = tk.Button(
            frame_servidores, text="🕵️ Modo Público (Anónimo)", font=("Arial", 9, "bold"),
            bg=self.card_color, fg=self.text_color, activebackground="#333333", activeforeground="white",
            width=25, pady=8, bd=0, cursor="hand2", command=self.iniciar_ssh
        )
        self.btn_ssh.grid(row=1, column=1, padx=10, pady=5)

        # --- CAJA DE ENLACE ACTIVO ---
        frame_enlace = tk.Frame(self.root, bg="#2a2a2a", pady=10)
        frame_enlace.pack(fill="x", padx=20, pady=10)
        
        tk.Label(frame_enlace, text="🔗 ENLACE ACTIVO:", font=("Arial", 10, "bold"), bg="#2a2a2a", fg="#ffcc00").pack(side="left", padx=15)
        
        self.url_variable = tk.StringVar()
        self.url_variable.set("Servidor apagado...")
        
        self.entry_url = tk.Entry(
            frame_enlace, textvariable=self.url_variable, font=("Consolas", 11, "bold"), 
            bg="#111111", fg="#00ff00", bd=0, state="readonly", readonlybackground="#111111"
        )
        self.entry_url.pack(side="left", fill="x", expand=True, padx=10, ipady=5)

        self.btn_copiar = tk.Button(
            frame_enlace, text="📋 Copiar", font=("Arial", 9, "bold"),
            bg="#ffcc00", fg="black", activebackground="#e6b800", activeforeground="black",
            bd=0, cursor="hand2", padx=15, pady=5, state="disabled", command=self.copiar_enlace
        )
        self.btn_copiar.pack(side="right", padx=15)

        # 2. BOTONES DE HERRAMIENTAS
        frame_herramientas = tk.Frame(self.root, bg=self.bg_color)
        frame_herramientas.pack(fill="x", padx=20, pady=5)

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

        # 3. CONSOLA DE LOGS
        lbl_logs = tk.Label(self.root, text="Logs del Sistema en Tiempo Real:", bg=self.bg_color, fg="#888888", font=("Arial", 9))
        lbl_logs.pack(anchor="w", padx=20, pady=(5, 0))
        
        self.consola = scrolledtext.ScrolledText(
            self.root, height=12, bg="#000000", fg="#33ff33", 
            font=("Consolas", 9), bd=0, padx=10, pady=10, state="disabled"
        )
        self.consola.pack(fill="both", padx=20, pady=5, expand=True)

    def copiar_enlace(self):
        url = self.url_variable.get()
        if "http" in url:
            self.root.clipboard_clear()
            self.root.clipboard_append(url)
            messagebox.showinfo("Copiado", "¡Enlace copiado al portapapeles!\nPégalo en tu app de Flutter.")
    
    def set_url_activa(self, url):
        self.url_variable.set(url)
        self.btn_copiar.config(state="normal")

    def limpiar_url(self):
        self.url_variable.set("Servidor apagado...")
        self.btn_copiar.config(state="disabled")

    def log(self, mensaje):
        self.consola.config(state="normal")
        self.consola.insert(tk.END, mensaje + "\n")
        self.consola.see(tk.END)
        self.consola.config(state="disabled")

    def abrir_configuracion(self):
        ventana_cfg = tk.Toplevel(self.root)
        ventana_cfg.title("Configuración de Servicios")
        ventana_cfg.geometry("450x330")
        ventana_cfg.configure(bg=self.bg_color)
        ventana_cfg.resizable(False, False)

        # --- CAMPO NGROK ---
        tk.Label(ventana_cfg, text="Authtoken de Ngrok:", bg=self.bg_color, fg="white", font=("Arial", 10, "bold")).pack(pady=(20, 5))
        entry_token = tk.Entry(ventana_cfg, width=50, bg=self.card_color, fg="white", bd=1, insertbackground="white")
        entry_token.pack(pady=5)
        entry_token.insert(0, self.config.get("ngrok_token", ""))

        # --- NUEVO CAMPO: NAVEGADOR (Texto Libre) ---
        tk.Label(ventana_cfg, text="Navegador para Cookies (ej: firefox, edge, chrome):", bg=self.bg_color, fg="white", font=("Arial", 10, "bold")).pack(pady=(15, 5))
        entry_nav = tk.Entry(ventana_cfg, width=50, bg=self.card_color, fg="white", bd=1, insertbackground="white")
        entry_nav.pack(pady=5)
        entry_nav.insert(0, self.config.get("navegador", "firefox"))

        def guardar():
            self.config["ngrok_token"] = entry_token.get().strip()
            # Guardamos el navegador siempre en minúsculas para evitar errores en yt-dlp
            self.config["navegador"] = entry_nav.get().strip().lower() 
            self._guardar_config()
            messagebox.showinfo("Guardado", "Configuración guardada correctamente.", parent=ventana_cfg)
            ventana_cfg.destroy()

        tk.Button(
            ventana_cfg, text=" Guardar Cambios", bg=self.accent_color, fg="white", bd=0, 
            padx=15, pady=5, cursor="hand2", command=guardar
        ).pack(pady=20)

        tk.Label(ventana_cfg, text="¿No tienes cuenta de Ngrok?", bg=self.bg_color, fg="#aaaaaa").pack(pady=(0, 0))
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
            encoding="utf-8",
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        self.hilo_lectura = threading.Thread(target=self._leer_consola_flask, daemon=True)
        self.hilo_lectura.start()

    def obtener_ip_local(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def iniciar_local(self):
        if self.proceso_servidor: return
        self.consola.config(state="normal")
        self.consola.delete("1.0", tk.END)
        self.log(">>> Levantando backend en Red Local...")
        
        ip_real = self.obtener_ip_local()
        self.set_url_activa(f"http://{ip_real}:5000")
        
        self._arrancar_flask_base()
        self._conmutar_botones(activo=True)

    def iniciar_playit(self):
        if self.proceso_servidor: return
        ruta_playit = obtener_ruta_recurso("playit.exe")
        if not os.path.exists(ruta_playit):
            respuesta = messagebox.askyesno("Error", "¿Deseas descargar playit.exe?")
            if respuesta: webbrowser.open("https://playit.gg/download")
            return

        self.consola.config(state="normal")
        self.consola.delete("1.0", tk.END)
        self.log(">>> Lanzando servidor Flask...")
        
        self.set_url_activa("Revisa la ventana negra de Playit.gg")
        
        self._arrancar_flask_base()
        self.proceso_playit = subprocess.Popen(
            [ruta_playit], creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
        self._conmutar_botones(activo=True)

    def iniciar_ngrok(self):
        if self.proceso_servidor: return
        if not NGROK_DISPONIBLE: return messagebox.showerror("Error", "Instala pyngrok")
        token = self.config.get("ngrok_token", "")
        if not token: return messagebox.showwarning("Aviso", "Guarda tu token de Ngrok en Configuración.")

        self.consola.config(state="normal")
        self.consola.delete("1.0", tk.END)
        self.log(">>> Solicitando túnel a Ngrok...")
        
        try:
            ngrok.set_auth_token(token)
            self.ngrok_tunnel = ngrok.connect(5000)
            url_publica = self.ngrok_tunnel.public_url
            
            self.set_url_activa(url_publica)
            
            self._arrancar_flask_base()
            self._conmutar_botones(activo=True)
        except Exception as e:
            self.log(f"Error Ngrok: {str(e)}")

    def iniciar_ssh(self):
        if self.proceso_servidor: return
        self.consola.config(state="normal")
        self.consola.delete("1.0", tk.END)
        self.log(">>> Lanzando servidor Flask...")
        self._arrancar_flask_base()
        
        ruta_llave_ssh = os.path.expanduser("~/.ssh/id_rsa")
        if not os.path.exists(ruta_llave_ssh):
            self.log(">>> Generando credenciales invisibles...")
            subprocess.run(["ssh-keygen", "-t", "rsa", "-b", "2048", "-N", "", "-f", ruta_llave_ssh], check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)

        self.log(">>> Conectando a localhost.run...")
        comando_ssh = ["ssh", "-o", "StrictHostKeyChecking=no", "-R", "80:127.0.0.1:5000", "ssh.localhost.run"]
        
        try:
            self.proceso_ssh = subprocess.Popen(
                comando_ssh, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            def leer_ssh():
                for linea in iter(self.proceso_ssh.stdout.readline, ''):
                    if linea:
                        texto = linea.strip()
                        if "lhr.life" in texto or "lhr.run" in texto:
                            url_final = "https://" + texto.split()[-1].replace("https://", "")
                            self.root.after(0, lambda: self.set_url_activa(url_final))
                            self.root.after(0, lambda: self.log("¡Túnel establecido exitosamente!"))
                        elif "==" not in texto and "[7m" not in texto:
                            self.root.after(0, lambda msg=f"[SSH] {texto}": self.log(msg))
                self.proceso_ssh.stdout.close()
                
            self.hilo_ssh = threading.Thread(target=leer_ssh, daemon=True)
            self.hilo_ssh.start()
            self._conmutar_botones(activo=True)
            
        except Exception as e:
            self.log(f"Error SSH: {str(e)}")

    def apagar_servidor(self):
        self.log("\n>>> Iniciando apagado...")
        if self.proceso_servidor:
            self.proceso_servidor.terminate()
            self.proceso_servidor.wait()
            self.proceso_servidor = None
        if self.proceso_playit:
            self.proceso_playit.terminate()
            self.proceso_playit = None
        if self.ngrok_tunnel:
            ngrok.disconnect(self.ngrok_tunnel.public_url)
            self.ngrok_tunnel = None
        if self.proceso_ssh:
            self.proceso_ssh.terminate()
            self.proceso_ssh = None
            
        self.limpiar_url()
        self.log(" Sistema apagado y desconectado.")
        self._conmutar_botones(activo=False)

    def limpiar_residuos(self):
        ruta_descargas = os.path.join(os.getcwd(), "descargas")
        if not os.path.exists(ruta_descargas): return
        archivos = [f for f in os.listdir(ruta_descargas) if f.endswith('.m4a')]
        if not archivos: return
        if messagebox.askyesno("Limpiar", f"¿Eliminar {len(archivos)} residuos?"):
            for archivo in archivos:
                try: os.remove(os.path.join(ruta_descargas, archivo))
                except Exception: pass
            self.log("Limpieza completada.")

    def _conmutar_botones(self, activo):
        estado_inversor = "disabled" if activo else "normal"
        self.btn_local.config(state=estado_inversor)
        self.btn_playit.config(state=estado_inversor)
        self.btn_ngrok.config(state=estado_inversor)
        self.btn_ssh.config(state=estado_inversor)
        self.btn_apagar.config(state="normal" if activo else "disabled")


def al_cerrar_ventana():
    if dashboard.proceso_servidor or dashboard.proceso_playit or dashboard.ngrok_tunnel or dashboard.proceso_ssh:
        dashboard.apagar_servidor()
    ventana.destroy()

if __name__ == "__main__":
    ventana = tk.Tk()
    dashboard = PlayTuveDashboard(ventana)
    ventana.protocol("WM_DELETE_WINDOW", al_cerrar_ventana)
    ventana.mainloop()