# Terminal Transcription Tool

Herramienta de terminal para transcripción de audio en tiempo real usando Whisper de OpenAI.

## Características

- Grabación de audio desde el micrófono
- Transcripción local usando modelos Whisper
- Soporte para múltiples idiomas
- Transcripción de archivos de audio existentes
- Exportación de transcripciones a archivos de texto
- Modo verbose con timestamps
- **Nuevo**: Síntesis de voz (TTS) usando Piper - respuestas habladas
- **Nuevo**: Control de terminal por voz usando Claude AI

## Requisitos

- Python 3.8+
- Micrófono funcional

## Instalación

### En Termux (Android)

```bash
# Instalar dependencias del sistema
pkg update
pkg install python ffmpeg portaudio

# Instalar dependencias de Python
pip install -r requirements.txt
```

### En Linux

```bash
# Debian/Ubuntu
sudo apt-get install python3-pip ffmpeg portaudio19-dev

# Fedora
sudo dnf install python3-pip ffmpeg portaudio-devel

# Instalar dependencias de Python
pip install -r requirements.txt
```

### En macOS

```bash
brew install python ffmpeg portaudio
pip install -r requirements.txt
```

## Uso

### Uso básico

```bash
# Grabar y transcribir (presiona Ctrl+C para detener)
python transcribe.py

# Grabar durante 10 segundos
python transcribe.py -d 10

# Transcribir archivo existente
python transcribe.py -f audio.mp3
```

### Opciones avanzadas

```bash
# Usar modelo más preciso
python transcribe.py -m medium

# Especificar idioma (mejora precisión y velocidad)
python transcribe.py -l es  # Español
python transcribe.py -l en  # Inglés

# Guardar transcripción a archivo
python transcribe.py -d 5 -o transcript.txt

# Modo verbose con timestamps
python transcribe.py -v

# Mantener archivo de audio grabado
python transcribe.py --keep-audio
```

### Modo Comandos por Voz (Claude AI)

Habla instrucciones en lenguaje natural y Claude las interpretará como comandos de terminal.

**Configuración:**

```bash
# Obtén tu API key en: https://console.anthropic.com/
export ANTHROPIC_API_KEY='tu-api-key-aqui'
```

**Uso:**

```bash
# Modo comando por voz (con confirmación)
python transcribe.py -p -l es

# Ejemplos de instrucciones que puedes decir:
# "lista todos los archivos python"
# "muéstrame el contenido del directorio actual"
# "busca archivos que contengan la palabra config"
# "crea un directorio llamado proyectos"
# "elimina el archivo temporal"

# Ejecución automática SIN confirmación (¡usar con cuidado!)
python transcribe.py -p -l es --auto-execute

# Especificar duración de grabación
python transcribe.py -p -d 5 -l es

# Usar API key directamente (sin variable de entorno)
python transcribe.py -p --api-key tu-api-key
```

**Características del modo voz:**

- Claude interpreta tu instrucción en lenguaje natural
- Genera comandos seguros y apropiados para Termux/Linux
- Muestra explicación de lo que hace el comando
- Pide confirmación antes de ejecutar (a menos que uses `--auto-execute`)
- Advierte sobre comandos potencialmente peligrosos

**Ejemplo de flujo:**

```
$ python transcribe.py -p -l es
🎤 Recording... (Press Ctrl+C to stop)
⏹️  Recording stopped
🔄 Transcribing audio...

==================================================
📝 TRANSCRIPTION
==================================================
lista todos los archivos python en este directorio
==================================================

🤖 Asking Claude to interpret: 'lista todos los archivos python en este directorio'

==================================================
🤖 INTERPRETACIÓN DE CLAUDE
==================================================
Comando: ls *.py
Explicación: Lists all Python files in current directory
==================================================

⚠️  COMANDO A EJECUTAR:
   ls *.py
==================================================

¿Ejecutar este comando? [y/N]: y

🚀 Ejecutando: ls *.py

transcribe.py
✅ Comando ejecutado exitosamente
```

### Síntesis de Voz (Text-to-Speech)

La herramienta puede **hablar** las respuestas usando Piper TTS, un motor de síntesis de voz rápido y eficiente.

**Uso:**

```bash
# Transcribir y escuchar la transcripción
python transcribe.py --speak -l es

# Modo comando con respuestas habladas
python transcribe.py -p -l es --speak

# Transcribir archivo y escucharlo
python transcribe.py -f audio.mp3 --speak -l es
```

**Voces disponibles por idioma:**

- Español: `es_ES-mls_10246-low`
- Inglés: `en_US-lessac-medium`
- Francés: `fr_FR-siwis-medium`
- Alemán: `de_DE-thorsten-medium`
- Italiano: `it_IT-riccardo-x_low`
- Portugués: `pt_BR-faber-medium`
- Chino: `zh_CN-huayan-medium`

**Usar voz personalizada:**

```bash
# Especificar una voz diferente
python transcribe.py --speak --tts-voice en_US-amy-medium -l en
```

**Nota:** Los modelos de voz se descargan automáticamente la primera vez que se usan y se almacenan en `~/.local/share/piper/voices/`

### Modelos disponibles

| Modelo | Tamaño | RAM necesaria | Velocidad | Precisión |
|--------|--------|---------------|-----------|-----------|
| tiny   | ~75 MB | ~1 GB         | Muy rápida| Básica    |
| base   | ~150 MB| ~1 GB         | Rápida    | Buena     |
| small  | ~500 MB| ~2 GB         | Media     | Muy buena |
| medium | ~1.5 GB| ~5 GB         | Lenta     | Excelente |
| large  | ~3 GB  | ~10 GB        | Muy lenta | Máxima    |

Recomendación: Usa `base` para balance entre velocidad y precisión, o `small` si tienes suficiente RAM.

## Códigos de idioma comunes

- `es` - Español
- `en` - Inglés
- `fr` - Francés
- `de` - Alemán
- `it` - Italiano
- `pt` - Portugués
- `zh` - Chino
- `ja` - Japonés
- `ko` - Coreano

## Ejemplos

### Transcripción básica

```bash
# Transcribir una reunión en español
python transcribe.py -l es -m small -o reunion.txt -v

# Grabar una nota rápida de 30 segundos
python transcribe.py -d 30 -l es

# Transcribir un podcast descargado
python transcribe.py -f podcast.mp3 -m medium -o podcast_transcript.txt
```

### Comandos por voz

```bash
# Control básico del sistema
python transcribe.py -p -l es
# Di: "muéstrame los procesos que están usando más memoria"

# Navegación de archivos
python transcribe.py -p -l es -d 5
# Di: "busca archivos modificados hoy"

# Operaciones Git
python transcribe.py -p -l es
# Di: "muéstrame el estado de git"

# Gestión de paquetes
python transcribe.py -p -l es
# Di: "actualiza la lista de paquetes"
```

### Síntesis de voz (TTS)

```bash
# Asistente de voz completo (hablas y escuchas respuestas)
python transcribe.py -p -l es --speak
# Di: "lista los archivos de este directorio"
# La herramienta ejecutará el comando y te dirá el resultado

# Dictado con lectura
python transcribe.py --speak -l es -d 10
# Habla durante 10 segundos y escucha tu transcripción

# Leer archivo de audio transcrito
python transcribe.py -f audio.mp3 --speak -l es

# Conversación completa manos libres
python transcribe.py -p -l es --speak --auto-execute -d 5
# Habla comandos de 5 segundos y escucha los resultados automáticamente
```

## Permisos

### Termux
Necesitas otorgar permisos de micrófono:
```bash
termux-setup-storage
```

## Solución de problemas

### Error: "No se detecta el micrófono"
- En Termux: Verifica los permisos de micrófono en la configuración de Android
- En Linux: Verifica que PortAudio esté instalado correctamente

### Error: "Out of memory"
- Usa un modelo más pequeño (`tiny` o `base`)
- Cierra otras aplicaciones

### Transcripción incorrecta
- Especifica el idioma con `-l`
- Usa un modelo más grande
- Mejora la calidad del audio (reduce ruido de fondo)

### Errores con Claude API
- Verifica que tu API key sea válida
- Asegúrate de tener saldo en tu cuenta de Anthropic
- Revisa tu conexión a internet

### Errores con TTS (Text-to-Speech)
- Si no se escucha audio, verifica los permisos de audio del sistema
- Si falla la descarga del modelo, verifica tu conexión a internet
- Los modelos se descargan automáticamente la primera vez (puede tardar un momento)
- Si hay problemas de audio, prueba con `--tts-voice` para cambiar la voz

## Seguridad

### Modo comandos por voz

- Por defecto, el sistema **siempre pide confirmación** antes de ejecutar cualquier comando
- Revisa cuidadosamente el comando propuesto antes de aceptarlo
- Usa `--auto-execute` solo en entornos controlados y con instrucciones que conoces
- Claude intenta generar comandos seguros, pero siempre verifica antes de ejecutar
- No uses este modo con comandos destructivos sin revisar la salida primero

### Recomendaciones

1. Prueba primero con `-l es` (o tu idioma) para mejorar precisión
2. Usa frases claras y específicas
3. Revisa siempre el comando generado antes de ejecutar
4. Para comandos críticos, ejecuta manualmente después de ver la sugerencia

## Licencia

MIT
