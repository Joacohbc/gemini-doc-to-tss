# Para ejecutar este código, necesitas instalar las siguientes dependencias:
# pip install google-genai (según el comentario original del usuario)

import argparse
import glob
import json
import os
import re # Para limpiar nombres de archivo
import struct # Para convert_to_wav
import time # Para el espaciado entre generaciones
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Asumiendo que estas importaciones son correctas para la biblioteca 'google-genai'
# que el usuario tiene, basándose en su script original.
from google import genai
from google.genai import types


# Parámetros del modelo y de generación (del script original)
# Estos se usarán para cada llamada.
MODEL_NAME = "gemini-2.5-flash-preview-tts"
VOICE_NAME = "Zephyr"
TEMPERATURE = 1

# --- Funciones de Ayuda (directamente del script original del usuario) ---

def log_error(message):
    """Guarda errores en el archivo logs.txt con timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open("logs.txt", "a", encoding="utf-8") as log_file:
            log_file.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass  # Si no se puede escribir al log, continuar silenciosamente

def save_binary_file(file_name, data):
    """Guarda datos binarios en un archivo."""
    try:
        with open(file_name, "wb") as f:
            f.write(data)
        print(f"Archivo guardado en: {file_name}")
    except IOError as e:
        print(f"Error al guardar el archivo {file_name}")
        log_error(f"Error al guardar el archivo {file_name}: {e}")

def parse_audio_mime_type(mime_type: str) -> dict[str, int | None]:
    """
    Analiza los bits por muestra y la tasa de muestreo de una cadena de tipo MIME de audio.
    (Función original del usuario)
    """
    bits_per_sample = 16
    rate = 24000

    # Extract rate from parameters
    parts = mime_type.split(";")
    for param in parts: # Skip the main type part
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate_str = param.split("=", 1)[1]
                rate = int(rate_str)
            except (ValueError, IndexError):
                # Handle cases like "rate=" with no value or non-integer value
                pass # Keep rate as default
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass # Keep bits_per_sample as default if conversion fails

    return {"bits_per_sample": bits_per_sample, "rate": rate}

def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    """
    Genera un encabezado de archivo WAV para los datos de audio y parámetros dados.
    Asume que audio_data es PCM crudo.
    (Función original del usuario)
    """
    parameters = parse_audio_mime_type(mime_type)
    bits_per_sample = parameters.get("bits_per_sample", 16) # Default si no se encuentra
    sample_rate = parameters.get("rate", 24000)       # Default si no se encuentra
    
    if bits_per_sample is None or sample_rate is None: # Chequeo básico
        print(f"Advertencia: No se pudieron determinar los parámetros de audio desde mime_type: {mime_type}. Usando defaults.")
        bits_per_sample = bits_per_sample or 16
        sample_rate = sample_rate or 24000

    num_channels = 1  # Asumimos mono para TTS
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size  # 36 bytes para campos de encabezado antes del tamaño del chunk de datos

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        chunk_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        num_channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b"data",
        data_size
    )
    return header + audio_data

# --- Lógica Modificada para los Requisitos ---

def create_results_file(filename: str, successful_ids: list, failed_ids: list, target_ids: set = None):
    """
    Crea un archivo de texto con los resultados del procesamiento.
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=== RESULTADOS DEL PROCESAMIENTO DE AUDIO ===\n")
            f.write(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            if target_ids:
                f.write(f"IDs solicitados para procesar: {sorted(target_ids)}\n")
                f.write(f"Total IDs solicitados: {len(target_ids)}\n\n")
            else:
                f.write("Modo: Procesar todos los IDs disponibles\n\n")
            
            f.write(f"IDs procesados exitosamente ({len(successful_ids)}):\n")
            if successful_ids:
                for id_item in sorted(successful_ids):
                    f.write(f"  ✓ {id_item}\n")
            else:
                f.write("  (Ninguno)\n")
            
            f.write(f"\nIDs que fallaron ({len(failed_ids)}):\n")
            if failed_ids:
                for id_item in sorted(failed_ids):
                    f.write(f"  ✗ {id_item}\n")
            else:
                f.write("  (Ninguno)\n")
            
            f.write(f"\nResumen:\n")
            f.write(f"  Total procesados: {len(successful_ids) + len(failed_ids)}\n")
            f.write(f"  Exitosos: {len(successful_ids)}\n")
            f.write(f"  Fallidos: {len(failed_ids)}\n")
            
            if len(successful_ids) + len(failed_ids) > 0:
                success_rate = (len(successful_ids) / (len(successful_ids) + len(failed_ids))) * 100
                f.write(f"  Tasa de éxito: {success_rate:.1f}%\n")
        
        print(f"Archivo de resultados creado: {filename}")
        
    except Exception as e:
        print(f"Error al crear archivo de resultados: {e}")
        log_error(f"Error al crear archivo de resultados {filename}: {e}")

def generate_audio_for_text(
    text_input: str,
    title: str,
    item_id: str,
    client: genai.Client, # Usando genai.Client como en el script original
    model_name: str,
    base_generate_config: types.GenerateContentConfig,
    text_index: int,
    output_folder: str,
    max_retries: int = 3
) -> tuple[bytes | None, str | None, bool]:
    """
    Genera un chunk de audio para un texto dado usando la estructura de API original.
    Devuelve los bytes de audio crudos, el mime_type y un booleano indicando éxito.
    Incluye sistema de reintentos con espera de 1 minuto en caso de fallo.
    """
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=text_input),
            ],
        ),
    ]

    for attempt in range(max_retries):
        accumulated_audio_data = b""
        first_mime_type = None
        
        print(f"Generando audio para ID '{item_id}': '{title}' - Intento {attempt + 1}/{max_retries}")
        try:
            # Usando client.models.generate_content_stream como en el script original
            for chunk in client.models.generate_content_stream(
                model=model_name,
                contents=contents,
                config=base_generate_config, # Pasa la configuración completa
            ):
                if (
                    chunk.candidates is None
                    or not chunk.candidates # Asegura que la lista de candidatos no esté vacía
                    or chunk.candidates[0].content is None
                    or chunk.candidates[0].content.parts is None
                    or not chunk.candidates[0].content.parts # Asegura que la lista de parts no esté vacía
                ):
                    continue
                
                part = chunk.candidates[0].content.parts[0]
                if part.inline_data and part.inline_data.data:
                    if first_mime_type is None: # Captura el mime_type del primer chunk de datos
                        first_mime_type = part.inline_data.mime_type
                    accumulated_audio_data += part.inline_data.data
                # En el script original, se imprimía chunk.text aquí si no era inline_data
                # elif part.text:
                #     print(f"Texto recibido en chunk (no audio): {part.text}")

            # Si llegamos aquí sin excepción y tenemos datos de audio, el intento fue exitoso
            if accumulated_audio_data:
                print(f"Audio generado exitosamente en intento {attempt + 1}.")
                
                # Guardar archivo individual
                try:
                    # Usar el título como nombre base del archivo
                    clean_title = re.sub(r'[<>:"/\\|?*]', '_', title)
                    clean_title = clean_title.strip()
                    if not clean_title:
                        clean_title = f"audio_{item_id}"
                    
                    individual_filename = f"{item_id}_{clean_title}.wav"
                    individual_file_path = os.path.join(output_folder, individual_filename)
                    individual_wav_data = convert_to_wav(accumulated_audio_data, first_mime_type)
                    
                    with open(individual_file_path, "wb") as f:
                        f.write(individual_wav_data)
                    print(f"Archivo individual guardado: {individual_file_path}")
                    
                except Exception as e:
                    log_error(f"Error al guardar archivo individual para ID '{item_id}': '{title}': {e}")
                    print(f"Advertencia: No se pudo guardar el archivo individual para ID '{item_id}': '{title}'")
                
                print(f"Esperando 5 segundos antes de la siguiente generación...")
                time.sleep(5)
                return accumulated_audio_data, first_mime_type, True
            else:
                print(f"Advertencia: No se recibieron datos de audio para ID '{item_id}': '{title}' en intento {attempt + 1}")
                log_error(f"No se recibieron datos de audio para ID '{item_id}': '{title}' (contenido: '{text_input[:30]}...') en intento {attempt + 1}")
                
        except Exception as e:
            print(f"Error durante la llamada API para ID '{item_id}': '{title}' en intento {attempt + 1}")
            log_error(f"Error durante la llamada API para ID '{item_id}': '{title}' (contenido: '{text_input[:30]}...') en intento {attempt + 1}: {e}")
        
        # Si no es el último intento, esperar 1 minuto antes del siguiente intento
        if attempt < max_retries - 1:
            print(f"Esperando 1 minuto antes del siguiente intento...")
            time.sleep(60)
    
    # Si llegamos aquí, todos los intentos fallaron
    print(f"Error: No se pudo generar audio para ID '{item_id}': '{title}' después de {max_retries} intentos")
    log_error(f"Error: No se pudo generar audio para ID '{item_id}': '{title}' (contenido: '{text_input[:30]}...') después de {max_retries} intentos")
    return None, None, False


def main():
    parser = argparse.ArgumentParser(description="Genera y combina audio desde textos en un JSON con formato [{'id': '', 'title': '', 'content': ''}], usando la estructura original de genai.Client.")
    parser.add_argument("json_file", help="Ruta al archivo JSON que contiene un array de objetos con 'id', 'title' y 'content'.")
    parser.add_argument("test_name", help="Nombre de la prueba (se usará para generar el nombre del archivo de salida).")
    parser.add_argument("--ids", nargs='*', help="IDs específicos a procesar. Si no se especifica, se procesan todos los IDs.")
    parser.add_argument("--api_key", help="Clave API de Gemini. También se puede configurar mediante la variable de entorno GEMINI_API_KEY.")
    parser.add_argument("--max_workers", type=int, default=5, help="Número máximo de hilos para procesamiento en paralelo.")
    parser.add_argument("--model_name", default=MODEL_NAME, help=f"Nombre del modelo a usar (por defecto: {MODEL_NAME}).")
    parser.add_argument("--voice_name", default=VOICE_NAME, help=f"Nombre de la voz a usar (por defecto: {VOICE_NAME}).")
    parser.add_argument("--temperature", type=float, default=TEMPERATURE, help=f"Temperatura para la generación (por defecto: {TEMPERATURE}).")
    args = parser.parse_args()

    api_key_value = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key_value:
        print("Error: GEMINI_API_KEY no configurada. Por favor, establece la variable de entorno o usa el argumento --api_key.")
        return

    try:
        with open(args.json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # Validar formato del JSON
        if not isinstance(json_data, list):
            print("Error: El archivo JSON debe contener un array de objetos.")
            return
        
        texts_to_process = []
        titles_to_process = []
        ids_to_process = []
        
        # Determinar qué IDs procesar
        target_ids = set(args.ids) if args.ids else None
        
        for i, item in enumerate(json_data):
            if not isinstance(item, dict):
                print(f"Error: El elemento {i+1} debe ser un objeto con 'id', 'title' y 'content'.")
                return
            
            required_fields = ['id', 'title', 'content']
            for field in required_fields:
                if field not in item:
                    print(f"Error: El elemento {i+1} debe tener la propiedad '{field}'.")
                    return
            
            if not isinstance(item['id'], str) or not isinstance(item['title'], str) or not isinstance(item['content'], str):
                print(f"Error: 'id', 'title' y 'content' del elemento {i+1} deben ser strings.")
                return
            
            # Solo procesar este item si su ID está en la lista target o si no se especificaron IDs
            if target_ids is None or item['id'] in target_ids:
                texts_to_process.append(item['content'])
                titles_to_process.append(item['title'])
                ids_to_process.append(item['id'])
        
        # Verificar si algunos IDs especificados no se encontraron
        if target_ids:
            found_ids = set(ids_to_process)
            missing_ids = target_ids - found_ids
            if missing_ids:
                print(f"Advertencia: Los siguientes IDs no se encontraron en el JSON: {sorted(missing_ids)}")
        
        if not texts_to_process:
            if target_ids:
                print("No se encontraron textos para procesar con los IDs especificados.")
            else:
                print("El archivo JSON está vacío o no contiene textos para procesar.")
            return
    except FileNotFoundError:
        print(f"Error: Archivo JSON no encontrado en {args.json_file}")
        return
    except json.JSONDecodeError:
        print(f"Error: No se pudo decodificar JSON desde {args.json_file}")
        return
    
    # Inicializa el cliente genai.Client() una vez, como en el script original
    try:
        client = genai.Client(api_key=api_key_value)
    except Exception as e:
        print("Error inicializando genai.Client")
        print("Asegúrate de que la biblioteca 'google-genai' esté instalada y que la API key sea válida.")
        log_error(f"Error inicializando genai.Client: {e}")
        return

    base_generate_content_config = types.GenerateContentConfig(
        temperature=args.temperature,
        response_modalities=["audio"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=args.voice_name
                )
            )
        ),
    )

    all_audio_segments_data = []
    first_valid_mime_type = None
    successful_ids = []
    failed_ids = []

    # Crear carpeta para archivos individuales
    try:
        clean_test_name = re.sub(r'[<>:"/\\|?*]', '_', args.test_name)
        clean_test_name = clean_test_name.strip()
        if not clean_test_name:
            clean_test_name = "audio_test"
        
        output_folder = f"{clean_test_name}_audios"
        os.makedirs(output_folder, exist_ok=True)
        print(f"Carpeta creada para archivos individuales: {output_folder}/")
    except Exception as e:
        print(f"Error al crear la carpeta para archivos individuales: {e}")
        log_error(f"Error al crear la carpeta para archivos individuales: {e}")
        output_folder = "."  # Usar directorio actual como fallback

    print(f"Iniciando procesamiento de {len(texts_to_process)} textos con hasta {args.max_workers} hilos...")
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        future_to_data = {
            executor.submit(generate_audio_for_text, content, title, item_id, client, args.model_name, base_generate_content_config, i, output_folder): (item_id, title, content)
            for i, (item_id, title, content) in enumerate(zip(ids_to_process, titles_to_process, texts_to_process))
        }

        for i, future in enumerate(future_to_data):
            item_id, title, content = future_to_data[future]
            print(f"Esperando resultado para ID '{item_id}': '{title}' ({i+1}/{len(texts_to_process)})")
            try:
                audio_data, mime_type, success = future.result()
                if success and audio_data and mime_type:
                    all_audio_segments_data.append(audio_data)
                    successful_ids.append(item_id)
                    if first_valid_mime_type is None:
                        first_valid_mime_type = mime_type
                    elif first_valid_mime_type != mime_type:
                        print(f"ADVERTENCIA: Discrepancia en el tipo MIME")
                        log_error(f"ADVERTENCIA: Discrepancia en el tipo MIME. Esperado {first_valid_mime_type}, obtenido {mime_type}. Se usará el primer tipo MIME ({first_valid_mime_type}) para el encabezado WAV. Esto podría generar un audio incorrecto si los formatos base no son compatibles.")
                elif success and audio_data and not mime_type:
                     print(f"Advertencia: Se recibieron datos de audio pero no mime_type para ID '{item_id}': '{title}'")
                     log_error(f"Advertencia: Se recibieron datos de audio pero no mime_type para ID '{item_id}': '{title}'")
                     successful_ids.append(item_id)
                else:
                    failed_ids.append(item_id)

            except Exception as exc:
                print(f"Error al procesar ID '{item_id}': '{title}' (fuera de la llamada API)")
                log_error(f"Error al procesar ID '{item_id}': '{title}' (fuera de la llamada API): {exc}")
                failed_ids.append(item_id)

    # Crear archivo de resultados incluso si no hay audio exitoso
    try:
        clean_test_name = re.sub(r'[<>:"/\\|?*]', '_', args.test_name)
        clean_test_name = clean_test_name.strip()
        if not clean_test_name:
            clean_test_name = "audio_test"
        results_filename = f"{clean_test_name}_resultados.txt"
        create_results_file(results_filename, successful_ids, failed_ids, target_ids)
    except Exception as e:
        log_error(f"Error al crear archivo de resultados: {e}")

    if not all_audio_segments_data or first_valid_mime_type is None:
        print("No se generaron datos de audio con éxito o no se pudo determinar el tipo MIME.")
        print(f"IDs exitosos: {len(successful_ids)}, IDs fallidos: {len(failed_ids)}")
        return

    print("Concatenando todos los segmentos de audio...")
    combined_raw_audio_data = b"".join(all_audio_segments_data)

    if not combined_raw_audio_data:
        print("Los datos de audio combinados están vacíos. No se puede crear el archivo WAV.")
        return

    print(f"Convirtiendo datos de audio combinados a formato WAV usando mime_type base: {first_valid_mime_type}...")
    try:
        final_wav_data = convert_to_wav(combined_raw_audio_data, first_valid_mime_type)
        
        # Generar nombre de archivo basado en el nombre de prueba
        try:
            # Limpiar el nombre de prueba para que sea válido como nombre de archivo
            clean_test_name = re.sub(r'[<>:"/\\|?*]', '_', args.test_name)
            clean_test_name = clean_test_name.strip()
            
            if clean_test_name:
                output_filename = f"{clean_test_name}_completo.wav"
            else:
                output_filename = "audio_generado_completo.wav"
        except Exception:
            output_filename = "audio_generado_completo.wav"
        
        # Verificar permisos de escritura
        try:
            # Intentar crear un archivo temporal para verificar permisos
            test_file = f"test_permissions_{int(time.time())}.tmp"
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
        except Exception as e:
            log_error(f"Error de permisos de escritura: {e}")
            output_filename = f"/tmp/{output_filename}"  # Intentar escribir en /tmp
            print(f"Advertencia: Problemas de permisos, guardando en: {output_filename}")
            
        save_binary_file(output_filename, final_wav_data)
        print(f"Audio combinado guardado exitosamente en {output_filename}")
        
        # Crear archivo de resultados con el mismo nombre base
        results_filename = f"{clean_test_name}_resultados.txt"
        create_results_file(results_filename, successful_ids, failed_ids, target_ids)
        
        # Mostrar resumen de archivos generados
        print("\n=== RESUMEN DE ARCHIVOS GENERADOS ===")
        print(f"Archivo combinado: {output_filename}")
        print("Archivos individuales:")
        individual_files_pattern = os.path.join(output_folder, "*.wav")
        individual_files = glob.glob(individual_files_pattern)
        for file in sorted(individual_files):
            print(f"  - {file}")
        print(f"Total archivos individuales: {len(individual_files)}")
        print(f"Carpeta de archivos individuales: {output_folder}/")
        
    except Exception as e:
        print("Error durante la conversión final a WAV o al guardar")
        log_error(f"Error durante la conversión final a WAV o al guardar: {e}")

if __name__ == "__main__":
    main()