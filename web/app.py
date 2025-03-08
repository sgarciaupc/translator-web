import os
import requests
from flask import Flask, request, render_template, jsonify, send_from_directory
import moviepy.editor as mp
from pydub import AudioSegment, silence
from TTS.api import TTS  # Usamos Coqui-TTS
import tempfile

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")
TRANSLATED_VIDEO_FOLDER = os.path.join(BASE_DIR, "translated_videos")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(TRANSLATED_VIDEO_FOLDER, exist_ok=True)

WHISPER_API_URL = "http://whisper-api:5000/transcribe"

@app.route("/")
def index():
    return render_template("index.html")

def generate_speech(text, lang="es", model="tts_models/es/css10/vits"):
    """Genera voz a partir de texto con Coqui-TTS y devuelve la ruta del archivo de audio."""
    tts = TTS(model_name=model)
    audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
    tts.tts_to_file(text=text, file_path=audio_path)
    return audio_path

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No se ha enviado ningún archivo"}), 400

    file = request.files["file"]
    filename = file.filename
    source_lang = request.form.get("source_lang", "en")
    target_lang = request.form.get("target_lang", "es")

    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    # Llamada a Whisper API para transcripción y traducción
    response = requests.post(
        WHISPER_API_URL,
        files={"file": open(file_path, "rb")},
        data={"source_lang": source_lang, "target_lang": target_lang}
    )
    translated_text = response.json().get("transcription")

    # Extraer audio completo del vídeo original
    original_clip = mp.VideoFileClip(file_path)
    original_audio_path = os.path.join(OUTPUT_FOLDER, "original_audio.mp3")
    original_clip.audio.write_audiofile(original_audio_path)

    original_audio = AudioSegment.from_mp3(original_audio_path)

    # Detectar segmentos sin silencio (voz hablada)
    nonsilent_parts = silence.detect_nonsilent(
        original_audio, min_silence_len=500, silence_thresh=original_audio.dBFS - 14
    )

    if nonsilent_parts:
        inicio_voz = nonsilent_parts[0][0]
        fin_voz = nonsilent_parts[-1][1]
    else:
        inicio_voz, fin_voz = 0, len(original_audio)

    # Extraer segmentos intro, voz original y outro
    intro = original_audio[:inicio_voz]
    outro = original_audio[fin_voz:]
    original_voice_segment = original_audio[inicio_voz:fin_voz]

    # Procesar el texto para eliminar pausas innecesarias
    clean_text = translated_text.replace("\n", " ").replace(". ", " ")

    # Generar audio traducido
    translated_audio_path = generate_speech(clean_text, lang=target_lang)
    translated_voice = AudioSegment.from_wav(translated_audio_path)

    # Ajustar velocidad de voz traducida para sincronización exacta
    duration_original_voice = len(original_voice_segment) / 1000  # Convertir a segundos
    duration_translated_voice = len(translated_voice) / 1000

    if duration_original_voice > 0 and duration_translated_voice > 0:
        speed_factor = duration_translated_voice / duration_original_voice
        speed_factor = max(0.9, min(speed_factor, 1.1))  # Evita distorsiones extremas
    else:
        speed_factor = 1.0

    translated_voice = translated_voice.speedup(playback_speed=speed_factor, crossfade=30)

    # Reconstruir audio completo con intro y outro original
    final_audio = intro + translated_voice + outro
    audio_final_path = os.path.join(OUTPUT_FOLDER, f"sync_{os.path.splitext(filename)[0]}_{target_lang}.mp3")
    final_audio.export(audio_final_path, format="mp3")

    # Crear el vídeo final con audio traducido sincronizado
    final_audio_clip = mp.AudioFileClip(audio_final_path)
    final_video_clip = original_clip.set_audio(final_audio_clip)

    translated_video_filename = f"{os.path.splitext(filename)[0]}_{target_lang}_translated.mp4"
    translated_video_path = os.path.join(TRANSLATED_VIDEO_FOLDER, translated_video_filename)
    final_video_clip.write_videofile(translated_video_path, codec="libx264", audio_codec="aac")

    return jsonify({
        "message": "Procesamiento completado",
        "transcription": translated_text,
        "translated_audio": f"/download/{os.path.basename(audio_final_path)}",
        "translated_video": f"/download_video/{translated_video_filename}"
    })

@app.route("/download/<filename>")
def download_audio(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

@app.route("/download_video/<filename>")
def download_translated_video(filename):
    return send_from_directory(TRANSLATED_VIDEO_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
