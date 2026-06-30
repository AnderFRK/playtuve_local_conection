# PlayTuve Backend (Local)

Backend desarrollado con **Flask** y **yt-dlp** para obtener información y descargar audio de videos de YouTube en formato **M4A**.

Este proyecto está pensado para ejecutarse **únicamente en una red local (LAN)** y ser consumido por la aplicación Flutter.

Descargar zip ejecutable en este link:
[Playtuve Local Server Executable](https://drive.google.com/file/d/1u_9LWvOJg0USvh95zFZZdOBgu-9dwVVq/view?usp=sharing)

---

# Características

- Descarga audio de videos de YouTube en formato **M4A**.
- Obtiene información del video sin necesidad de descargarlo.
- API REST sencilla para integrarse con Flutter.
- Compatible con dispositivos conectados a la misma red WiFi.
- Utiliza **FFmpeg** para la conversión del audio.

---

# Requisitos

- Python 3.10 o superior
- FFmpeg instalado y agregado al `PATH`
- Dependencias del proyecto

Instalar las dependencias:

```bash
pip install -r requirements.txt
```

---

# Estructura del proyecto

```text
PlayTuveBackend/
│
├── app.py
├── requirements.txt
├── descargas/
└── README.md
```

---

# Ejecutar el servidor

Desde la carpeta del proyecto:

```bash
python app.py
```

El servidor iniciará por defecto en:

```text
http://localhost:5000
```

También será accesible desde otros dispositivos de la misma red mediante la IP local de tu computadora.

Ejemplo:

```text
http://122.10.1.20:5000
```

---

# Endpoints

## GET /

Verifica que el servidor esté funcionando.

### Respuesta

```json
{
  "status": "ok",
  "mensaje": "PlayTuve backend local funcionando"
}
```

---

## POST /info

Obtiene la información de un video sin descargarlo.

### Body

```json
{
  "url": "https://www.youtube.com/watch?v=XXXXXXXXXXX"
}
```

### Respuesta

```json
{
  "titulo": "Nombre del video",
  "duracion": 228,
  "canal": "Nombre del canal"
}
```

---

## POST /descargar

Descarga el audio del video y devuelve directamente el archivo `.m4a`.

### Body

```json
{
  "url": "https://www.youtube.com/watch?v=XXXXXXXXXXX"
}
```

### Respuesta

Archivo de audio en formato **M4A**.

---

# Uso desde Flutter

```dart
final response = await http.post(
  Uri.parse('http://192.168.1.20:5000/descargar'),
  headers: {
    'Content-Type': 'application/json',
  },
  body: jsonEncode({
    'url': urlYoutube,
  }),
);

if (response.statusCode == 200) {
  final archivo = File(rutaLocal);
  await archivo.writeAsBytes(response.bodyBytes);
}
```

Para obtener la información del video:

```dart
final response = await http.post(
  Uri.parse('http://10.0.0.0:5000/info'),
  headers: {
    'Content-Type': 'application/json',
  },
  body: jsonEncode({
    'url': urlYoutube,
  }),
);

if (response.statusCode == 200) {
  final data = jsonDecode(response.body);
  print(data['titulo']);
}
```

---

# Notas

- El servidor debe permanecer ejecutándose mientras la aplicación Flutter lo utilice.
- El teléfono y la computadora deben estar conectados a la misma red WiFi.
- Si la dirección IP de la computadora cambia, también deberá actualizarse en la aplicación Flutter.
- Los archivos descargados se almacenan temporalmente en la carpeta `descargas/`.

---

# Tecnologías

- Python
- Flask
- yt-dlp
- FFmpeg
```