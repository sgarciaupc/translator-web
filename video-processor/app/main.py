from flask import Flask, request, jsonify
import os
from werkzeug.utils import secure_filename
from utils import extract_audio, extract_frames

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return jsonify({"message": "Servidor de procesamiento de video en ejecución"}), 200

@app.route('/process', methods=['POST'])
def process_video():
    if 'file' not in request.files:
        return jsonify({"error": "No se ha enviado ningún archivo"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nombre de archivo vacío"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    # Procesar el video
    audio_path = extract_audio(file_path)
    frames_paths = extract_frames(file_path)

    return jsonify({
        "message": "Procesamiento completado",
        "audio_file": audio_path,
        "frames": frames_paths[:5]  # Solo mostramos las primeras 5 imágenes para no sobrecargar la respuesta
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
