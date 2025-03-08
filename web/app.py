import os
import uuid
import threading
import time
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Diccionario global para almacenar el estado de los trabajos
jobs = {}  # jobs[job_id] = {"status": ..., "progress": ..., "transcription": ..., "video_url": ...}

UPLOAD_FOLDER = "/"
TRANSLATED_VIDEOS_FOLDER = "translated_videos"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRANSLATED_VIDEOS_FOLDER, exist_ok=True)

########################################
# 1. Página principal con formulario
########################################
@app.route("/")
def index():
    return render_template("index.html")  # En este HTML estará la barra de progreso y el form

########################################
# 2. Endpoint /upload
########################################
@app.route("/upload", methods=["POST"])
def upload_file():
    """Recibe el archivo y parámetros de idioma. Lanza el procesamiento en un hilo."""
    if 'file' not in request.files:
        return jsonify({"error": "No se ha enviado ningún archivo"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nombre de archivo vacío"}), 400

    # Generar un job_id único
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "uploading",
        "progress": 0,
        "transcription": "",
        "video_url": None,
        "error": None
    }

    source_lang = request.form.get("source_lang", "en")
    target_lang = request.form.get("target_lang", "es")

    # Guardamos el archivo
    filename = file.filename
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    # Lanza un hilo para no bloquear la petición
    thread = threading.Thread(target=process_file, args=(job_id, file_path, source_lang, target_lang))
    thread.start()

    # Devolvemos el job_id inmediatamente
    return jsonify({"job_id": job_id})

########################################
# 3. Función que hace el trabajo real (en un hilo)
########################################
def process_file(job_id, file_path, source_lang, target_lang):
    try:
        # 3a) Cambiamos estado a "upload_done"
        jobs[job_id]["status"] = "upload_done"
        jobs[job_id]["progress"] = 10

        # 3b) Llamamos a whisper-api para transcribir y traducir el texto
        jobs[job_id]["status"] = "transcribing"
        jobs[job_id]["progress"] = 30

        # Ejemplo de llamada al whisper-api (asumiendo que se llama "http://whisper-api:5000/transcribe")
        # y que este endpoint permite enviar 'file' directamente, o un path, etc.
        with open(file_path, "rb") as f:
            files = {"file": (file_path, f)}
            data = {
                "source_lang": source_lang,
                "target_lang": target_lang
            }
            response = requests.post("http://whisper-api:5000/transcribe", files=files, data=data)
        
        if response.status_code != 200:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = f"Error en whisper-api: {response.text}"
            return
        
        transcription_json = response.json()
        transcription_text = transcription_json.get("transcription", "")
        jobs[job_id]["transcription"] = transcription_text
        jobs[job_id]["status"] = "transcribed"
        jobs[job_id]["progress"] = 50

        # 3c) Llamamos a video-processor para generar el video traducido (ejemplo)
        #     Supongamos que en "video-processor" hay un endpoint /process_video
        #     que recibe el file_path y la transcripción y produce un MP4 con subtítulos
        jobs[job_id]["status"] = "generating_video"
        jobs[job_id]["progress"] = 70

        resp = requests.post(
            "http://video-processor:5001/process_video",
            json={
                "file_path": file_path,
                "transcription": transcription_text,
                "target_lang": target_lang
            }
        )
        if resp.status_code != 200:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = f"Error en video-processor: {resp.text}"
            return
        
        # Supongamos que el video-processor devuelve la ruta final del video
        processed_json = resp.json()
        translated_video_name = processed_json.get("translated_video_name", "translated.mp4")
        video_url = os.path.join(TRANSLATED_VIDEOS_FOLDER, translated_video_name)

        jobs[job_id]["video_url"] = f"/download_video/{translated_video_name}"
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 100

    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)

########################################
# 4. Endpoint para consultar el estado: /status/<job_id>
########################################
@app.route("/status/<job_id>", methods=["GET"])
def get_status(job_id):
    """Devuelve el estado del trabajo en JSON."""
    job_info = jobs.get(job_id)
    if not job_info:
        return jsonify({"error": "Job no encontrado"}), 404
    return jsonify({
        "status": job_info["status"],
        "progress": job_info["progress"],
        "transcription": job_info["transcription"],
        "video_url": job_info["video_url"],
        "error": job_info["error"]
    })

########################################
# 5. (Opcional) Endpoint para descargar video
########################################
@app.route("/download_video/<filename>", methods=["GET"])
def download_video(filename):
    """Devuelve el archivo de video final (si existe)."""
    path = os.path.join(TRANSLATED_VIDEOS_FOLDER, filename)
    if not os.path.exists(path):
        return jsonify({"error": "Video no encontrado"}), 404

    # En Flask se puede devolver un archivo con send_file
    from flask import send_file
    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
