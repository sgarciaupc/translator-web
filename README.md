# Video Web Translator

Una aplicación multi-contenedor diseñada para traducir videos entre inglés, español, francés, alemán e italiano. El proyecto integra el procesamiento de video, la transcripción (usando Whisper API con soporte para GPU) y una interfaz web para gestionar y visualizar los resultados.

## Tabla de Contenidos

- [Descripción](#descripción)
- [Características](#características)
- [Arquitectura](#arquitectura)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Uso](#uso)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Contribuciones](#contribuciones)
- [Licencia](#licencia)

## Descripción

El proyecto **Video Web Translator** facilita la traducción de videos a través de un sistema modular basado en Docker. Cada servicio se encarga de una tarea específica:

- **video-processor:** Procesa el video, realizando tareas como la extracción del audio y preprocesamiento.
- **whisper-api:** Utiliza el modelo Whisper para transcribir el audio y gestionar la traducción, con soporte para aceleración por GPU.
- **translator-web:** Proporciona una interfaz web para la carga de videos, visualización de resultados y gestión general de la aplicación.

## Características

- **Procesamiento de Video:** Manejo y preprocesamiento de archivos de video.
- **Transcripción y Traducción:** Uso del modelo Whisper para transcribir y traducir audio a múltiples idiomas.
- **Interfaz Web:** Portal para subir videos y visualizar resultados.
- **Soporte GPU:** Configuración para utilizar GPU Nvidia y acelerar el procesamiento.
- **Orquestación con Docker Compose:** Integración y despliegue simplificado de servicios.

## Arquitectura

La aplicación se compone de tres contenedores principales, definidos en el archivo `docker-compose.yml`:

- **video-processor:**  
  - Construido desde `./video-processor`
  - Puerto expuesto: `5001`
  - Volúmenes:  
    - `./uploads` para archivos subidos  
    - `./outputs` para resultados del procesamiento

- **whisper-api:**  
  - Construido desde `./whisper-api`
  - Puerto expuesto: `5000`
  - Volúmenes:  
    - `./uploads`  
    - `./transcriptions` para almacenar las transcripciones generadas  
  - **Soporte GPU:** Configuración para utilizar una GPU Nvidia, lo que mejora el rendimiento del procesamiento.

- **translator-web:**  
  - Construido desde `./web`
  - Puerto expuesto: `5002`
  - Volúmenes:  
    - `./uploads`  
    - `./outputs`  
    - `./transcriptions`  
    - `./translated_videos` para almacenar los videos traducidos
  - **Dependencias:** Se inicia después de los servicios `video-processor` y `whisper-api`.

## Requisitos

- [Docker](https://www.docker.com/get-started) y [Docker Compose](https://docs.docker.com/compose/install/)
- (Opcional) Tarjeta gráfica Nvidia con drivers y runtime configurado para Docker, en caso de querer utilizar aceleración GPU en `whisper-api`.

## Instalación

1. **Clona el repositorio:**

   ```bash
   git clone https://github.com/sgarciaupc/video-web-translator.git
   cd video-web-translator
   ```
2. **Construye y levanta los servicios:**
  ```bash
  docker-compose up --build
  ```

   Esto creará y ejecutará los contenedores necesarios para la aplicación.


## Uso:
- Accede a la interfaz web en http://localhost:5002.
- Sube un video utilizando la interfaz web.
- El servicio video-processor procesará el video y whisper-api se encargará de la transcripción y traducción.
- Una vez finalizado el procesamiento, podrás visualizar y descargar el video traducido desde la interfaz.

## Estructura del proyecto:
```bash
video-web-translator/
├── docker-compose.yml
├── video-processor/        # Servicio de procesamiento de video
├── whisper-api/            # Servicio para transcripción y traducción usando Whisper
├── web/                    # Interfaz web para la aplicación
├── uploads/                # Directorio para archivos subidos
├── outputs/                # Resultados del procesamiento de video
├── transcriptions/         # Archivos de transcripción generados
└── translated_videos/      # Videos traducidos
```
##Contribuciones
¡Las contribuciones son bienvenidas! Si deseas mejorar el proyecto o agregar nuevas funcionalidades, sigue estos pasos:

- Realiza un fork del repositorio.
- Crea una rama para tu feature o corrección.
- Envía un pull request describiendo tus cambios.

##Licencia
Este proyecto se distribuye bajo la Licencia MIT.
