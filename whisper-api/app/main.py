from flask import Flask, request, jsonify
import whisper
import os
import torch

# Importes de Hugging Face
from transformers import MarianMTModel, MarianTokenizer
import sentencepiece  # Se instala, pero no siempre se importa directamente

app = Flask(__name__)

# ----------------------------------------------------------------
# 1. Cargar modelos
# ----------------------------------------------------------------
# Carga de Whisper (puedes usar "small", "base", "medium", etc.)
model = whisper.load_model("small")

# Carga del modelo MarianMT (ejemplo: inglés->español)
MODEL_NAME = "Helsinki-NLP/opus-mt-en-es"
tokenizer = MarianTokenizer.from_pretrained(MODEL_NAME)
transformer_model = MarianMTModel.from_pretrained(MODEL_NAME)

# Usar GPU si está disponible
device = "cuda" if torch.cuda.is_available() else "cpu"
transformer_model.to(device)

# ----------------------------------------------------------------
# 2. Configurar rutas de carpetas
# ----------------------------------------------------------------
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "transcriptions"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ----------------------------------------------------------------
# 3. Funciones de traducción con chunking
# ----------------------------------------------------------------
def chunk_text(text, max_size=400):
    """
    Divide el texto en trozos de longitud máxima 'max_size'.
    Con MarianMT conviene usar trozos pequeños para evitar problemas
    de memoria o tiempos de procesamiento muy largos.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_size
        chunks.append(text[start:end])
        start = end
    return chunks

def translate_chunk_marian(chunk):
    """
    Traduce un chunk de texto usando MarianMT.
    Asumimos aquí que el texto de entrada está en inglés
    y queremos traducirlo a español.
    """
    tokens = tokenizer([chunk], return_tensors="pt", padding=True, truncation=True)
    tokens = {k: v.to(device) for k, v in tokens.items()}
    translated_tokens = transformer_model.generate(**tokens)
    translated_text = tokenizer.decode(translated_tokens[0], skip_special_tokens=True)
    return translated_text

def translate_large_text_marian(text):
    """
    Aplica 'translate_chunk_marian' a cada trozo y los concatena.
    """
    translated_chunks = []
    for chunk in chunk_text(text):
        translated_chunks.append(translate_chunk_marian(chunk))
    return " ".join(translated_chunks)

# ----------------------------------------------------------------
# 4. Endpoint principal
# ----------------------------------------------------------------
@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """
    - Recibe un archivo en la clave 'file'.
    - Guarda el archivo en UPLOAD_FOLDER.
    - Lee source_lang y target_lang del formulario.
    - Usa Whisper para transcribir o traducir a inglés.
    - Si target_lang != 'en', usa MarianMT para traducir de inglés a target_lang.
    - Devuelve la transcripción final en JSON.
    """
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

    # 1) Si el idioma de origen es igual al de destino, no hay traducción
    if source_lang == target_lang:
        result = model.transcribe(file_path, language=source_lang)
        transcription_text = result["text"]

    # 2) Si el destino es inglés, Whisper puede traducir directamente al inglés
    elif target_lang == "en":
        result = model.transcribe(file_path, language=source_lang, task="translate")
        transcription_text = result["text"]

    else:
        # a) Usamos Whisper para pasar de source_lang a inglés
        result = model.transcribe(file_path, language=source_lang, task="translate")
        intermediate_text = result["text"]

        # b) Ahora traducimos de inglés a target_lang con MarianMT
        transcription_text = translate_large_text_marian(intermediate_text)

    # Guardamos la transcripción en un archivo .txt
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
