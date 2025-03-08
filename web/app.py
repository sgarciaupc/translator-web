import os
import requests
from flask import Flask, request, render_template, jsonify, send_from_directory
import moviepy.editor as mp
from pydub import AudioSegment, silence
import pyttsx3

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

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No se ha enviado ningún archivo"}), 400

    file = request.files["file"]
    filename = file.filename
    source_lang = request.form.get("source_lang", "en")
    target_lang = request.form.get("target_lang", "es")
    voice_gender = request.form.get("voice_gender", "male")  # 'male' o 'female'

    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    # Obtener texto traducido
    response = requests.post(
        WHISPER_API_URL,
        files={"file": open(file_path, "rb")},
        data={"source_lang": source_lang, "target_lang": target_lang}
    )
    result = response.json()
    translated_text = result.get("transcription")

    # Extraer audio original completo
    original_clip = mp.VideoFileClip(file_path)
    original_audio_path = os.path.join(OUTPUT_FOLDER, "original_audio.mp3")
    original_clip.audio.write_audiofile(original_audio_path)
    original_audio = AudioSegment.from_mp3(original_audio_path)

    # Detectar silencios para obtener inicio y final de voz original
    non_silences = silence.detect_nonsilent(
        original_audio, min_silence_len=700, silence_thresh=original_audio.dBFS - 16
    )

    inicio_voz = non_silences[0][0]
    fin_voz = non_silences[-1][1]

    # Separar intro y outro musical
    intro = original_audio[:inicio_voz]
    outro = original_audio[fin_voz:]

    # Generar audio traducido con pyttsx3 (voz personalizable hombre/mujer)
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    
    # Seleccionar voz según género
    voice_id = voices[0].id if voice_gender == "male" else voices[1].id
    engine.setProperty('voice', voice_id)

    # Generar audio traducido en wav
    audio_translated_path_wav = os.path.join(OUTPUT_FOLDER, "audio_translated.wav")
    engine.save_to_file(translated_text, audio_translated_path_wav)
    engine.runAndWait()

    # Convertir audio WAV generado a MP3
    translated_voice = AudioSegment.from_wav(audio_translated_path_wav)

    # Ajustar duración exacta de audio traducido para coincidir exactamente con voz original
    duration_original_voice = (fin_voz - inicio_voz)
    translated_voice = translated_voice.set_frame_rate(44100)
    translated_voice = translated_voice.speedup(playback_speed=(len(translated_voice) / duration_original_voice))

    # Ensamblar audio final completo: intro + voz traducida + outro
    final_audio = intro + translated_voice + outro
    final_audio_path = os.path.join(OUTPUT_FOLDER, f"{os.path.splitext(filename)[0]}_{target_lang}_final.mp3")
    final_audio.export(final_audio_path, format="mp3")

    # Combinar audio final con video original
    final_audio_clip = mp.AudioFileClip(final_audio_path)
    final_video_clip = original_clip.set_audio(final_audio_clip)

    translated_video_filename = f"{os.path.splitext(filename)[0]}_{target_lang}_translated.mp4"
    translated_video_path = os.path.join(TRANSLATED_VIDEO_FOLDER, translated_video_filename)
    final_video_clip.write_videofile(translated_video_path, codec="libx264", audio_codec="aac")

    return jsonify({
        "message": "Procesamiento completado",
        "transcription": translated_text,
        "translated_audio": f"/download/{os.path.basename(final_audio_path)}",
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
