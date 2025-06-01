# Doc-to-TTS (Document to Text-to-Speech)

Una aplicación de Python que convierte documentos JSON estructurados en archivos de audio utilizando la API de Google Gemini para síntesis de voz.

## 📋 Descripción

Esta aplicación toma un archivo JSON con contenido estructurado en títulos y texto, y genera archivos de audio WAV usando la tecnología de síntesis de voz de Google Gemini. Ideal para crear audiolibros, podcasts educativos o contenido de audio accesible.

## 🔧 Instalación

### Requisitos Previos

- Python 3.8 o superior
- Una clave API de Google Gemini (free en IA Studio [https://aistudio.google.com/app/apikey])

### Dependencias

Instala las dependencias necesarias:

```bash
pip install google-genai
```

### Configuración de la API Key

Puedes configurar tu clave API de Google Gemini de dos formas:

1. **Variable de entorno (recomendado):**
   ```bash
   export GEMINI_API_KEY="tu_clave_api_aquí"
   ```

2. **Parámetro de línea de comandos:**
   ```bash
   python main.py archivo.json nombre_prueba --api_key "tu_clave_api_aquí"
   ```

## 📁 Formato del Archivo JSON

El archivo JSON debe contener un array de objetos, donde cada objeto representa una sección del contenido:

```json
[
    {
        "title": "Introducción",
        "content": "Bienvenidos a este audiolibro sobre experiencia de usuario..."
    },
    {
        "title": "Capítulo 1: Fundamentos",
        "content": "La experiencia de usuario es un campo multidisciplinario..."
    }
]
```

### Estructura Requerida

- **Array principal:** Lista de objetos JSON
- **Objeto individual:**
  - `title` (string): Título de la sección
  - `content` (string): Contenido de texto a convertir en audio

## 🚀 Uso

### Comando Básico

```bash
python main.py <archivo_json> <nombre_prueba>
```

### Ejemplo

```bash
python main.py example.json "Mi_Audiolibro"
```

### Parámetros

- `json_file`: Ruta al archivo JSON con el contenido
- `test_name`: Nombre de la prueba/proyecto (se usa para nombrar archivos de salida)
- `--api_key`: (Opcional) Clave API de Gemini
- `--max_workers`: (Opcional) Número máximo de hilos para procesamiento paralelo (por defecto: 5)

### Ejemplo Completo

```bash
python main.py input.json "Curso_UX" --api_key "tu_clave_api" --max_workers 3
```

## 📤 Archivos de Salida

La aplicación genera dos tipos de archivos:

1. **Archivos individuales:** Un archivo WAV por cada sección del JSON
   - Formato: `{título_limpio}_{índice}.wav`
   - Ejemplo: `Introducción_1.wav`, `Capítulo_1_2.wav`

2. **Archivo combinado:** Un archivo WAV que contiene todo el audio concatenado
   - Formato: `{nombre_prueba}_completo.wav`
   - Ejemplo: `Mi_Audiolibro_completo.wav`

## ⚙️ Configuración del Modelo

La aplicación utiliza los siguientes parámetros por defecto:

- **Modelo:** `gemini-2.5-flash-preview-tts`
- **Voz:** `Zephyr`
- **Temperatura:** `1`
- **Formato de salida:** WAV (mono, 24kHz, 16-bit)

## 🔄 Características

- **Procesamiento paralelo:** Múltiples hilos para generar audio más rápido
- **Sistema de reintentos:** 3 intentos por sección con espera automática
- **Limpieza de nombres:** Nombres de archivo seguros y válidos
- **Logging de errores:** Registro automático en `logs.txt`
- **Validación de datos:** Verificación completa del formato JSON

## 📝 Archivos del Proyecto

- `main.py`: Script principal de la aplicación
- `example.json`: Archivo de ejemplo con formato correcto
- `prompt.txt`: Prompt para generar contenido estructurado
- `logs.txt`: Archivo de registro de errores (generado automáticamente)
- `*.wav`: Archivos de audio generados

## 🛠️ Resolución de Problemas

### Error: GEMINI_API_KEY no configurada

```bash
export GEMINI_API_KEY="tu_clave_api_aquí"
```

### Error de formato JSON

Asegúrate de que tu archivo JSON:
- Sea un array válido `[...]`
- Cada elemento tenga `title` y `content`
- Ambos campos sean strings

### Problemas de permisos

Si hay problemas de escritura, la aplicación intentará guardar en `/tmp/`

### Audio no generado

- Verifica tu conexión a internet
- Confirma que tu API key sea válida
- Revisa el archivo `logs.txt` para detalles del error

## 📊 Ejemplo de Uso Completo

1. **Crear archivo JSON:**
   ```json
   [
       {
           "title": "Introducción al UX",
           "content": "La experiencia de usuario es fundamental en el diseño..."
       },
       {
           "title": "Investigación de Usuarios",
           "content": "Comprender a los usuarios es el primer paso..."
       }
   ]
   ```

2. **Ejecutar el script:**
   ```bash
   python main.py mi_contenido.json "Curso_UX_2024"
   ```

3. **Archivos generados:**
   - `Introducción_al_UX_1.wav`
   - `Investigación_de_Usuarios_2.wav`
   - `Curso_UX_2024_completo.wav`

## 📋 Registro de Actividad

Todos los errores y advertencias se guardan automáticamente en `logs.txt` con timestamp para facilitar la depuración.

## 🔐 Seguridad

- No compartas tu clave API de Google Gemini
- Mantén actualizada la biblioteca `google-genai`
- Revisa los logs regularmente para detectar problemas

## 📞 Soporte

Para problemas técnicos:
1. Revisa el archivo `logs.txt`
2. Verifica el formato de tu archivo JSON
3. Confirma que tu API key sea válida
4. Asegúrate de tener conexión a internet estable

---

**Nota:** Esta aplicación requiere una conexión activa a internet y una clave API válida de Google Gemini para funcionar correctamente.
