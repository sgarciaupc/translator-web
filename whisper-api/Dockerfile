# Usa una imagen base con Python y GPU si es necesario
FROM python:3.9-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y ffmpeg libsndfile1 --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


# Establecer la variable de caché de Hugging Face y OpenAI Whisper
ENV HF_HOME=/app/models
ENV WHISPER_MODELS_DIR=/app/models

# Crear directorio para los modelos
RUN mkdir -p /app/models

# Descargar el modelo de Whisper (ajusta según el que uses)
RUN python -c "import whisper; whisper.load_model('large')"
RUN python -c "import whisper; whisper.load_model('small')"

# Descargar el modelo de Hugging Face (ajusta según el que uses)
RUN python -c "from transformers import MarianMTModel; MarianMTModel.from_pretrained('Helsinki-NLP/opus-mt-en-es').save_pretrained('/app/models/opus-mt-en-es')"

# Copiar los archivos de la aplicación
COPY app/ app/

# Exponer el puerto de la API
EXPOSE 5000

# Comando para ejecutar la API
#CMD ["python", "app/main.py"]
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app.main:app"]
