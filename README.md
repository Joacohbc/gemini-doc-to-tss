# Gemini Doc-to-TTS (Document to Text-to-Speech)

Una aplicación de Python que convierte documentos JSON estructurados en archivos de audio utilizando la API de Google Gemini para síntesis de voz (TTS).

## 📋 Descripción

Esta aplicación toma un archivo JSON con contenido estructurado con IDs, títulos y texto, y genera archivos de audio WAV usando la tecnología de síntesis de voz de Google Gemini. Ideal para crear audiolibros, contenido educativo o cualquier tipo de narración automática a partir de texto estructurado.

## 🔧 Instalación

### Requisitos Previos

- Python 3.8 o superior
- Una clave API de Google Gemini (disponible gratis en [AI Studio](https://aistudio.google.com/app/apikey))

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
        "id": "intro",
        "title": "Introducción",
        "content": "Bienvenidos a este audiolibro sobre experiencia de usuario..."
    },
    {
        "id": "cap1",
        "title": "Capítulo 1: Fundamentos",
        "content": "La experiencia de usuario es un campo multidisciplinario..."
    }
]
```

### Estructura Requerida

- **Array principal:** Lista de objetos JSON
- **Objeto individual:**
  - `id` (string): Identificador único de la sección
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
- `--ids`: (Opcional) IDs específicos a procesar. Si no se especifica, se procesan todos
- `--api_key`: (Opcional) Clave API de Gemini
- `--max_workers`: (Opcional) Número máximo de hilos para procesamiento paralelo (por defecto: 5)
- `--model_name`: (Opcional) Nombre del modelo a usar (por defecto: gemini-2.5-flash-preview-tts)
- `--voice_name`: (Opcional) Nombre de la voz a usar (por defecto: Zephyr)
- `--temperature`: (Opcional) Temperatura para la generación (por defecto: 1)

### Ejemplos de Uso

**Procesar todos los elementos:**
```bash
python main.py input.json "Curso_UX" --api_key "tu_clave_api" --max_workers 3
```

**Procesar solo elementos específicos:**
```bash
python main.py input.json "Curso_UX" --ids intro cap1 cap3
```

**Cambiar modelo y voz:**
```bash
python main.py input.json "Mi_Audiolibro" --model_name "gemini-2.5-flash-preview-tts" --voice_name "Zephyr" --temperature 0.8
```

## 📤 Archivos de Salida

La aplicación genera varios tipos de archivos:

### 1. Archivos Individuales
- **Ubicación:** Carpeta `{nombre_prueba}_audios/`
- **Formato:** `{id}_{título_limpio}.wav`
- **Ejemplo:** `intro_Introducción.wav`, `cap1_Capítulo_1_Fundamentos.wav`

### 2. Archivo Combinado
- **Formato:** `{nombre_prueba}_completo.wav`
- **Ejemplo:** `Mi_Audiolibro_completo.wav`
- **Contenido:** Todo el audio concatenado en orden

### 3. Archivo de Resultados
- **Formato:** `{nombre_prueba}_resultados.txt`
- **Contenido:** Resumen detallado del procesamiento:
  - IDs procesados exitosamente
  - IDs que fallaron
  - Estadísticas de éxito
  - Tasa de éxito porcentual

### 4. Archivo de Logs
- **Nombre:** `logs.txt`
- **Contenido:** Errores y advertencias con timestamp

## ⚙️ Configuración del Modelo

La aplicación utiliza los siguientes parámetros por defecto:

- **Modelo:** `gemini-2.5-flash-preview-tts`
- **Voz:** `Zephyr`
- **Temperatura:** `1`
- **Formato de salida:** WAV (mono, 24kHz, 16-bit)
- **Modalidad de respuesta:** Audio únicamente

## 🔄 Características Avanzadas

### Procesamiento Paralelo
- Múltiples hilos simultáneos para acelerar la generación
- Configurable hasta 5 workers por defecto

### Sistema de Reintentos
- 3 intentos automáticos por cada sección que falle
- Espera de 1 minuto entre reintentos
- Espera de 5 segundos entre generaciones exitosas

### Procesamiento Selectivo
- Procesar solo IDs específicos con el parámetro `--ids`
- Validación de IDs faltantes con advertencias

### Gestión de Errores
- Logging automático con timestamp en `logs.txt`
- Continuación del procesamiento aunque algunas secciones fallen
- Reporte detallado de éxitos y fallos

### Limpieza de Nombres
- Eliminación automática de caracteres especiales en nombres de archivo
- Nombres seguros para todos los sistemas operativos

## 🛠️ Resolución de Problemas

### Error: GEMINI_API_KEY no configurada
```bash
export GEMINI_API_KEY="tu_clave_api_aquí"
```

### Error de formato JSON
Asegúrate de que tu archivo JSON:
- Sea un array válido `[...]`
- Cada elemento tenga `id`, `title` y `content` como strings
- Los IDs sean únicos

### Problemas de permisos
Si hay problemas de escritura, la aplicación intentará guardar en `/tmp/`

### Audio no generado para algunas secciones
- Verifica tu conexión a internet
- Confirma que tu API key sea válida y tenga cuota disponible
- Revisa el archivo `logs.txt` para detalles específicos
- Considera reducir `--max_workers` si hay problemas de límite de velocidad

### IDs específicos no encontrados
La aplicación mostrará advertencias si especificas IDs que no existen en el JSON

## 📊 Ejemplo de Uso Completo

1. **Crear archivo JSON:**
   ```json
   [
       {
           "id": "intro",
           "title": "Introducción al UX",
           "content": "La experiencia de usuario es fundamental en el diseño moderno..."
       },
       {
           "id": "research",
           "title": "Investigación de Usuarios",
           "content": "Comprender a los usuarios es el primer paso en cualquier proyecto..."
       },
       {
           "id": "conclusion",
           "title": "Conclusiones",
           "content": "En resumen, el diseño UX requiere un enfoque centrado en el usuario..."
       }
   ]
   ```

2. **Ejecutar el script completo:**
   ```bash
   python main.py mi_contenido.json "Curso_UX_2024"
   ```

3. **Procesar solo introducción y conclusión:**
   ```bash
   python main.py mi_contenido.json "Curso_UX_Resumen" --ids intro conclusion
   ```

4. **Archivos generados:**
   - **Carpeta:** `Curso_UX_2024_audios/`
     - `intro_Introducción_al_UX.wav`
     - `research_Investigación_de_Usuarios.wav`
     - `conclusion_Conclusiones.wav`
   - **Archivo combinado:** `Curso_UX_2024_completo.wav`
   - **Reporte:** `Curso_UX_2024_resultados.txt`

## 📋 Monitoreo y Logs

### Archivo de Resultados
Cada ejecución genera un reporte detallado que incluye:
- Fecha y hora de procesamiento
- IDs solicitados vs procesados
- Lista de éxitos y fallos
- Estadísticas de rendimiento
- Tasa de éxito porcentual

### Logs de Errores
- Timestamp automático para cada error
- Detalles específicos de fallos de API
- Información de contexto para debugging

## 🔐 Seguridad y Mejores Prácticas

- **Nunca compartas tu clave API** de Google Gemini
- Mantén actualizada la biblioteca `google-genai`
- Revisa los logs regularmente para detectar patrones de error
- Usa variables de entorno para la API key en producción
- Considera limitar `--max_workers` para evitar límites de velocidad

## ⚡ Optimización de Rendimiento

- **Procesamiento paralelo:** Aumenta `--max_workers` para archivos grandes (máximo recomendado: 10)
- **IDs específicos:** Usa `--ids` para procesar solo secciones necesarias
- **Gestión de cuota:** El sistema de reintentos y esperas evita límites de API
- **Almacenamiento:** Los archivos individuales permiten recuperación parcial

## 📞 Soporte y Debugging

Para problemas técnicos, revisa en orden:

1. **Archivo de resultados:** `{nombre_prueba}_resultados.txt`
2. **Logs de error:** `logs.txt`
3. **Formato JSON:** Valida la estructura requerida
4. **API Key:** Confirma validez y cuota disponible
5. **Conectividad:** Verifica conexión a internet estable

### Comandos de Diagnóstico

```bash
# Verificar formato JSON
python -m json.tool mi_archivo.json

# Probar con un solo ID
python main.py mi_archivo.json "test" --ids primer_id --max_workers 1

# Ejecutar con logging detallado
python main.py mi_archivo.json "debug" --max_workers 1 2>&1 | tee debug.log
```

---

**Nota:** Esta aplicación requiere una conexión activa a internet y una clave API válida de Google Gemini para funcionar correctamente. El procesamiento de archivos grandes puede tomar tiempo considerable dependiendo del contenido y la velocidad de la API.