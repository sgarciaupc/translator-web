# Imagen base con Python y utilidades necesarias
FROM python:3.9-slim

# Evita preguntas en instalación de paquetes
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    ffmpeg libsm6 libxext6 git && \
    rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar y instalar dependencias de Python
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y ffmpeg libsm6 libxext6 git && rm -rf /var/lib/apt/lists/*
RUN pip install "moviepy==1.0.3"

# Copiar la aplicación
COPY app/ app/

# Crear carpetas necesarias
RUN mkdir -p /app/uploads /app/outputs

# Exponer el puerto de la API
EXPOSE 5001

# Comando para ejecutar la API
#CMD ["python", "app/main.py"]
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5001", "app.main:app"]
