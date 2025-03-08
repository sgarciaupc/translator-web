# Usa una imagen base con Python y GPU si es necesario
FROM python:3.9-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y ffmpeg libsndfile1 --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar los archivos de la aplicación
COPY app/ app/

# Exponer el puerto de la API
EXPOSE 5000

# Comando para ejecutar la API
CMD ["python", "app/main.py"]
