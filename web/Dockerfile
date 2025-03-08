FROM python:3.9-slim

# Instalar dependencias
RUN apt-get update && apt-get install -y ffmpeg libsm6 libxext6 espeak-ng git && rm -rf /var/lib/apt/lists/*
RUN pip install flask flask-cors requests gtts moviepy==1.0.3 pydub numpy pyttsx3


# Establecer directorio de trabajo
WORKDIR /app

# Copiar los archivos de la web
COPY . /app/

# Exponer el puerto de la API
EXPOSE 5002

# Ejecutar la aplicación Flask
CMD ["python", "app.py"]
#CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5002", "app:app"]
