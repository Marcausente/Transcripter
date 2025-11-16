# Transcripter - Transcribir Audio a Texto

Aplicación simple con interfaz gráfica para transcribir archivos de audio (MP3, WAV, M4A, FLAC) a texto usando OpenAI Whisper.

## Instalación

1. Instala las dependencias:
```bash
pip install -r requirements.txt
```

## Uso

1. Ejecuta la aplicación:
```bash
python main.py
```

2. Haz clic en "Seleccionar archivo MP3" y elige tu archivo de audio
3. Haz clic en "Transcribir" y espera a que se complete la transcripción
4. El texto aparecerá en el área de texto
5. Haz clic en "Copiar al portapapeles" para copiar el texto

## Características

- Interfaz gráfica simple e intuitiva
- Soporta múltiples formatos de audio (MP3, WAV, M4A, FLAC)
- Transcripción automática usando Whisper
- Fácil copiar y pegar del texto transcrito
- Indicador de progreso durante la transcripción

## Notas

- La primera vez que uses la aplicación, se descargará el modelo Whisper 'base' (aproximadamente 150 MB)
- El tiempo de transcripción depende de la duración del audio
- El modelo 'base' ofrece un buen balance entre velocidad y precisión

