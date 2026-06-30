from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

DOWNLOAD_FOLDER = "descargas"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route("/")
def home():
    return jsonify({"status": "ok", "mensaje": "PlayTuve backend local funcionando"})

@app.route("/descargar", methods=["POST"])
def descargar_audio():
    data = request.get_json()

    if not data or "url" not in data:
        return jsonify({"error": "Falta el parámetro 'url'"}), 400

    url = data["url"]
    nombre_archivo = str(uuid.uuid4())
    ruta_salida = os.path.join(DOWNLOAD_FOLDER, f"{nombre_archivo}.%(ext)s")

    opciones = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": ruta_salida,
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
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=True)
            titulo = info.get("title", "audio")

        ruta_final = os.path.join(DOWNLOAD_FOLDER, f"{nombre_archivo}.m4a")

        if not os.path.exists(ruta_final):
            return jsonify({"error": "No se pudo generar el archivo de audio"}), 500

        return send_file(
            ruta_final,
            as_attachment=True,
            download_name=f"{titulo}.m4a",
            mimetype="audio/mp4",
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
    }

    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=False)

        return jsonify(
            {
                "titulo": info.get("title"),
                "duracion": info.get("duration"),
                "canal": info.get("uploader"),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)