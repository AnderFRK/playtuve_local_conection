import os
import tkinter as tk
from tkinter import messagebox, filedialog

class LimpiadorResiduos:
    def __init__(self, root):
        self.root = root
        self.root.title("PlayTuve Backend - Limpiador de Residuos")
        self.root.geometry("550x400")
        self.root.resizable(False, False)
        
        # Paleta de colores (Estilo Oscuro / Rojo PlayTuve)
        self.bg_color = "#121212"
        self.card_color = "#1e1e1e"
        self.accent_color = "#ff3333"
        self.text_color = "#ffffff"
        self.text_muted = "#aaaaaa"
        
        self.root.configure(bg=self.bg_color)
        
        # Ruta por defecto (Busca la carpeta 'descargas' al lado de este script)
        self.ruta_actual = os.path.join(os.path.dirname(os.path.abspath(__file__)), "descargas")
        if not os.path.exists(self.ruta_actual):
            self.ruta_actual = os.getcwd() # Si no existe, usa la carpeta raíz
            
        self.archivos_encontrados = []
        
        self._crear_interfaz()
        self.escanear_carpeta()

    def _crear_interfaz(self):
        # Título Principal
        lbl_titulo = tk.Label(
            self.root, text="Limpiador de Residuos .m4a", 
            font=("Arial", 16, "bold"), bg=self.bg_color, fg=self.accent_color
        )
        lbl_titulo.pack(pady=15)
        
        # Selector de Ruta (Card)
        frame_ruta = tk.Frame(self.root, bg=self.card_color, padx=10, pady=10, bd=0)
        frame_ruta.pack(fill="x", padx=20, pady=5)
        
        self.lbl_ruta = tk.Label(
            frame_ruta, text=f"Carpeta: {self.ruta_actual}", 
            font=("Arial", 10), bg=self.card_color, fg=self.text_color, anchor="w"
        )
        self.lbl_ruta.pack(side="left", fill="x", expand=True)
        
        btn_cambiar = tk.Button(
            frame_ruta, text="Cambiar", font=("Arial", 9, "bold"),
            bg=self.accent_color, fg="white", activebackground="#cc0000",
            activeforeground="white", bd=0, padx=10, pady=5, command=self.seleccionar_carpeta
        )
        btn_cambiar.pack(side="right")

        # Contenedor de Estado / Consola visual
        self.txt_consola = tk.Text(
            self.root, height=10, bg="#000000", fg="#33ff33", 
            font=("Consolas", 10), bd=0, padx=10, pady=10
        )
        self.txt_consola.pack(fill="both", padx=20, pady=15, expand=True)
        
        # Panel de Información de almacenamiento
        self.lbl_info = tk.Label(
            self.root, text="Archivos: 0 | Espacio total: 0.00 MB", 
            font=("Arial", 11, "bold"), bg=self.bg_color, fg=self.text_muted
        )
        self.lbl_info.pack(pady=5)
        
        # Botón de Acción Masiva
        self.btn_eliminar = tk.Button(
            self.root, text="ELIMINAR ARCHIVOS RESIDUALES", font=("Arial", 11, "bold"),
            bg="#b30000", fg="white", activebackground="#800000",
            activeforeground="white", bd=0, pady=10, cursor="hand2", command=self.eliminar_archivos
        )
        self.btn_eliminar.pack(fill="x", padx=20, pady=15)

    def seleccionar_carpeta(self):
        carpeta = filedialog.askdirectory(initialdir=self.ruta_actual, title="Seleccionar carpeta con audios")
        if carpeta:
            self.ruta_actual = carpeta
            self.lbl_ruta.config(text=f"Carpeta: {self.ruta_actual}")
            self.escanear_carpeta()

    def escanear_carpeta(self):
        self.archivos_encontrados = []
        peso_total = 0
        
        self.txt_consola.config(state="normal")
        self.txt_consola.delete("1.0", tk.END)
        self.txt_consola.insert(tk.END, ">>> Escaneando directorio en busca de archivos .m4a...\n")
        
        if not os.path.exists(self.ruta_actual):
            self.txt_consola.insert(tk.END, "❌ La ruta especificada no existe.\n")
            self.txt_consola.config(state="disabled")
            return
            
        try:
            for item in os.listdir(self.ruta_actual):
                if item.endswith(".m4a"):
                    ruta_completa = os.path.join(self.ruta_actual, item)
                    self.archivos_encontrados.append(ruta_completa)
                    
                    # Calcular peso del archivo
                    peso_bytes = os.path.getsize(ruta_completa)
                    peso_total += peso_bytes
                    
                    self.txt_consola.insert(tk.END, f"Found: {item} ({round(peso_bytes / (1024*1024), 2)} MB)\n")
                    
            peso_mb = peso_total / (1024 * 1024)
            self.lbl_info.config(text=f"Archivos: {len(self.archivos_encontrados)} | Espacio libre recuperable: {round(peso_mb, 2)} MB")
            
            if len(self.archivos_encontrados) == 0:
                self.txt_consola.insert(tk.END, "✅ ¡Todo limpio! No se encontraron residuos .m4a.\n")
                self.btn_eliminar.config(state="disabled", bg="#333333")
            else:
                self.btn_eliminar.config(state="normal", bg="#b30000")
                
        except Exception as e:
            self.txt_consola.insert(tk.END, f"❌ Error al escanear: {str(e)}\n")
            
        self.txt_consola.config(state="disabled")
        self.txt_consola.see(tk.END)

    def eliminar_archivos(self):
        if not self.archivos_encontrados:
            return
            
        confirmar = messagebox.askyesno(
            "Confirmar acción masiva", 
            f"¿Estás seguro de que deseas eliminar permanentemente los {len(self.archivos_encontrados)} archivos .m4a detectados?"
        )
        
        if confirmar:
            self.txt_consola.config(state="normal")
            self.txt_consola.insert(tk.END, "\n>>> Iniciando borrado seguro...\n")
            
            eliminados = 0
            errores = 0
            
            for ruta in self.archivos_encontrados:
                try:
                    nombre_archivo = os.path.basename(ruta)
                    os.remove(ruta)
                    self.txt_consola.insert(tk.END, f"Deleted: {nombre_archivo} 🗑️\n")
                    eliminados += 1
                except Exception as e:
                    self.txt_consola.insert(tk.END, f"Error en: {os.path.basename(ruta)} -> {str(e)}\n")
                    errores += 1
                    
            messagebox.showinfo("Limpieza Completada", f"Proceso terminado.\nArchivos eliminados: {eliminados}\nErrores: {errores}")
            self.escanear_carpeta()

if __name__ == "__main__":
    root = tk.Tk()
    app = LimpiadorResiduos(root)
    root.mainloop()