from flask import Flask, request, jsonify
import whisper
import os
from googletrans import Translator

app = Flask(__name__)

model = whisper.load_model("small")
translator = Translator()

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "transcriptions"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if 'file' not in request.files:
        return jsonify({"error": "No se ha enviado ningún archivo"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nombre de archivo vacío"}), 400

    filename = file.filename
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    source_lang = request.form.get("source_lang", "en")
    target_lang = request.form.get("target_lang", "es")

    # Primero transcribe o traduce (Whisper solo traduce a inglés)
    if source_lang == target_lang:
        result = model.transcribe(file_path, language=source_lang)
        transcription_text = result["text"]
    elif target_lang == "en":
        result = model.transcribe(file_path, language=source_lang, task="translate")
        transcription_text = result["text"]
    else:
        # Traducir primero al inglés
        result = model.transcribe(file_path, language=source_lang, task="translate")
        intermediate_text = result["text"]
        # Ahora traducir del inglés al idioma destino
        translated = translator.translate(intermediate_text, src='en', dest=target_lang)
        transcription_text = intermediate_text if target_lang == 'en' else intermediate_text
        transcription_text = translator.translate(intermediate_text, src='en', dest=target_lang).text

    output_file_path = os.path.join(OUTPUT_FOLDER, filename + ".txt")
    with open(output_file_path, "w") as text_file:
        text_file.write(transcription_text)

    return jsonify({
        "message": "Procesamiento completado",
        "transcription": transcription_text,
        "file": output_file_path
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
