from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

DOWNLOAD_FOLDER = "descargas"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# 🔥 LA FUNCIÓN MAESTRA (Configuración Base)
def opciones_comunes():
    return {
        "cookiesfrombrowser": ("firefox",),
        "js_runtimes": {
            "node": {
                "path": r"C:\Program Files\nodejs\node.exe" 
            }
        },
        "extractor_args": {
            "youtube": {
                "player_client": ["web"]
            }
        },
        "remote_components": ["ejs:github"],
        "nocheckcertificate": True,
        "noplaylist": True,
        "quiet": False,
        "no_warnings": False
    }

@app.route("/")
def home():
    return jsonify({"status": "ok", "mensaje": "PlayTuve backend local en terminal funcionando"})

@app.route("/descargar", methods=["POST"])
def descargar_audio():
    data = request.get_json()

    if not data or "url" not in data:
        return jsonify({"error": "Falta el parámetro 'url'"}), 400

    url = data["url"]
    nombre_archivo = str(uuid.uuid4())
    ruta_salida = os.path.join(DOWNLOAD_FOLDER, f"{nombre_archivo}.%(ext)s")

    print(f"\n[TERMINAL] 📥 Solicitud de descarga recibida: {url}")

    # Traemos las opciones base y le sumamos las de descarga
    opciones = opciones_comunes()
    opciones.update({
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": ruta_salida,
        "ratelimit": 2 * 1024 * 1024, # 2 MB/s          
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "m4a",
                "preferredquality": "192",
            }
        ]
    })

    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=True)
            titulo = info.get("title", "audio")

        ruta_final = os.path.join(DOWNLOAD_FOLDER, f"{nombre_archivo}.m4a")

        if not os.path.exists(ruta_final):
            return jsonify({"error": "No se pudo generar el archivo de audio"}), 500

        print(f"[TERMINAL] ✅ Descarga completa, enviando: {titulo}")

        return send_file(
            ruta_final,
            as_attachment=True,
            download_name=f"{titulo}.m4a",
            mimetype="audio/mp4",
        )

    except Exception as e:
        print(f"[TERMINAL] ❌ Error en descarga: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/info", methods=["POST"])
def obtener_info():
    data = request.get_json()

    if not data or "url" not in data:
        return jsonify({"error": "Falta el parámetro 'url'"}), 400

    url = data["url"]
    print(f"\n[TERMINAL] 🔎 Solicitud de información recibida: {url}")

    # Traemos las opciones base y le sumamos la orden de NO descargar
    opciones = opciones_comunes()
    opciones.update({
        "skip_download": True,
    })

    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=False)

        print(f"[TERMINAL] ✅ Información extraída: {info.get('title')}")

        return jsonify(
            {
                "titulo": info.get("title"),
                "duracion": info.get("duration"),
                "canal": info.get("uploader"),
            }
        )
    except Exception as e:
        print(f"[TERMINAL] ❌ Error extrayendo info: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("===================================================")
    print(f"SERVIDOR PLAYTUVE (MODO TERMINAL) EN PUERTO {port}")
    print("===================================================")
    app.run(host="0.0.0.0", port=port, debug=False)