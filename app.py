from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid
import threading
from waitress import serve 

app = Flask(__name__)

# --- CONFIGURACIÓN DE RUTAS ---
DIRECTORIO_RAIZ = os.getcwd()
DOWNLOAD_FOLDER = os.path.join(DIRECTORIO_RAIZ, "descargas")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

cola_descargas = threading.Lock()

def es_conexion_local(req):
    host = req.host.lower()
    if "127.0.0.1" in host or "192.168." in host or "localhost" in host:
        return True
    return False

@app.route("/")
def home():
    return jsonify({"status": "ok", "mensaje": "PlayTuve backend funcionando perfectamente"})

@app.route("/info", methods=["POST"])
def obtener_info():
    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "Falta el parámetro 'url'"}), 400

    url = data["url"]
    opciones = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "ffmpeg_location": DIRECTORIO_RAIZ,
    }

    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=False)

        return jsonify({
            "titulo": info.get("title"),
            "duracion": info.get("duration"),
            "canal": info.get("uploader"),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/descargar", methods=["POST"])
def descargar_audio():
    data = request.get_json()

    if not data or "url" not in data:
        return jsonify({"error": "Falta el parámetro 'url'"}), 400

    url = data["url"]
    nombre_archivo = str(uuid.uuid4())
    ruta_salida = os.path.join(DOWNLOAD_FOLDER, f"{nombre_archivo}.%(ext)s")

    modo_libre = es_conexion_local(request)
    limite_minutos = 20 # Límite para invitados

    try:
        opciones_info = {
            "quiet": True, "no_warnings": True, "skip_download": True,
            "ffmpeg_location": DIRECTORIO_RAIZ
        }
        with yt_dlp.YoutubeDL(opciones_info) as ydl:
            info_previa = ydl.extract_info(url, download=False)
            duracion = info_previa.get("duration", 0)
            titulo = info_previa.get("title", "audio")

        if not modo_libre and duracion > (limite_minutos * 60):
            print(f"❌ [Bloqueado] Audio demasiado largo: {duracion / 60:.2f} min.")
            return jsonify({"error": f"El video es muy largo para descargas públicas (Máx {limite_minutos} min)."}), 403

    except Exception as e:
        return jsonify({"error": f"Error al analizar el video: {str(e)}"}), 500

    print(f"📥 [En cola] Descargando '{titulo}'... (Modo Libre: {modo_libre})")
    
    with cola_descargas:
        opciones_descarga = {
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "outtmpl": ruta_salida,
            "ffmpeg_location": DIRECTORIO_RAIZ, 
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "m4a",
                    "preferredquality": "192",
                }
            ],
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        }

        try:
            with yt_dlp.YoutubeDL(opciones_descarga) as ydl:
                ydl.download([url])
        except Exception as e:
            return jsonify({"error": f"Error durante la descarga: {str(e)}"}), 500

    ruta_final = os.path.join(DOWNLOAD_FOLDER, f"{nombre_archivo}.m4a")

    if not os.path.exists(ruta_final):
        return jsonify({"error": "No se pudo generar el archivo de audio"}), 500

    print(f"✅ ¡Enviando '{titulo}' al celular!")
    return send_file(
        ruta_final,
        as_attachment=True,
        download_name=f"{titulo}.m4a", 
        mimetype="audio/mp4",
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    
    print("===================================================")
    print(f"🚀 SERVIDOR PLAYTUVE (WSGI WAITRESS) EN PUERTO {port}")
    print("===================================================")
    serve(app, host="0.0.0.0", port=port, threads=6)