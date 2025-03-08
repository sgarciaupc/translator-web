import os
import moviepy.editor as mp
import cv2

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

def extract_audio(video_path):
    """Extrae el audio de un video y lo guarda como un archivo .mp3"""
    clip = mp.VideoFileClip(video_path)
    audio_path = os.path.join(OUTPUT_FOLDER, os.path.basename(video_path) + ".mp3")
    clip.audio.write_audiofile(audio_path)
    return audio_path

def extract_frames(video_path):
    """Extrae los frames de un video y los guarda como imágenes"""
    vidcap = cv2.VideoCapture(video_path)
    success, image = vidcap.read()
    count = 0
    frame_paths = []

    video_name = os.path.splitext(os.path.basename(video_path))[0]
    frame_dir = os.path.join(OUTPUT_FOLDER, video_name)
    os.makedirs(frame_dir, exist_ok=True)

    while success:
        frame_path = os.path.join(frame_dir, f"frame_{count}.jpg")
        cv2.imwrite(frame_path, image)
        frame_paths.append(frame_path)
        success, image = vidcap.read()
        count += 1

    return frame_paths
