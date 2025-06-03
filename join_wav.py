#!/usr/bin/env python3
"""
Script para combinar múltiples archivos WAV en un solo archivo WAV final.
Reutiliza el método de unión del script principal.
"""

import argparse
import glob
import os
import re
import struct
import time
from datetime import datetime
from pathlib import Path


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


def parse_wav_header(wav_data: bytes) -> dict:
    """
    Extrae información del encabezado WAV.
    Retorna un diccionario con los parámetros del audio.
    """
    if len(wav_data) < 44:
        raise ValueError("Archivo WAV demasiado pequeño o corrupto")
    
    # Verificar firma RIFF
    if wav_data[:4] != b'RIFF':
        raise ValueError("No es un archivo WAV válido (falta RIFF)")
    
    # Verificar formato WAVE
    if wav_data[8:12] != b'WAVE':
        raise ValueError("No es un archivo WAV válido (falta WAVE)")
    
    # Buscar el chunk 'fmt '
    fmt_pos = wav_data.find(b'fmt ')
    if fmt_pos == -1:
        raise ValueError("No se encontró el chunk 'fmt ' en el archivo WAV")
    
    # Leer parámetros del fmt chunk (después de 'fmt ' + 4 bytes de tamaño)
    fmt_data_start = fmt_pos + 8
    
    # Desempacar los datos del formato
    format_data = struct.unpack('<HHIIHH', wav_data[fmt_data_start:fmt_data_start + 16])
    
    audio_format = format_data[0]
    num_channels = format_data[1]
    sample_rate = format_data[2]
    byte_rate = format_data[3]
    block_align = format_data[4]
    bits_per_sample = format_data[5]
    
    return {
        'audio_format': audio_format,
        'num_channels': num_channels,
        'sample_rate': sample_rate,
        'byte_rate': byte_rate,
        'block_align': block_align,
        'bits_per_sample': bits_per_sample
    }


def extract_audio_data(wav_data: bytes) -> bytes:
    """
    Extrae solo los datos de audio de un archivo WAV (sin encabezados).
    """
    # Buscar el chunk 'data'
    data_pos = wav_data.find(b'data')
    if data_pos == -1:
        raise ValueError("No se encontró el chunk 'data' en el archivo WAV")
    
    # Los datos de audio comienzan después de 'data' + 4 bytes de tamaño
    data_size_pos = data_pos + 4
    data_size = struct.unpack('<I', wav_data[data_size_pos:data_size_pos + 4])[0]
    audio_data_start = data_size_pos + 4
    
    return wav_data[audio_data_start:audio_data_start + data_size]


def create_wav_header(audio_data_size: int, params: dict) -> bytes:
    """
    Crea un encabezado WAV con los parámetros especificados.
    """
    chunk_size = 36 + audio_data_size
    
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        chunk_size,
        b"WAVE",
        b"fmt ",
        16,  # Tamaño del fmt chunk
        params['audio_format'],
        params['num_channels'],
        params['sample_rate'],
        params['byte_rate'],
        params['block_align'],
        params['bits_per_sample'],
        b"data",
        audio_data_size
    )
    return header


def load_wav_file(file_path: str) -> tuple[bytes, dict]:
    """
    Carga un archivo WAV y retorna los datos de audio y sus parámetros.
    """
    try:
        with open(file_path, "rb") as f:
            wav_data = f.read()
        
        params = parse_wav_header(wav_data)
        audio_data = extract_audio_data(wav_data)
        
        return audio_data, params
    except Exception as e:
        raise Exception(f"Error al cargar {file_path}: {e}")


def join_wav_files(input_files: list, output_file: str, force_params: dict = None):
    """
    Une múltiples archivos WAV en un solo archivo.
    
    Args:
        input_files: Lista de rutas a archivos WAV
        output_file: Ruta del archivo WAV de salida
        force_params: Parámetros a forzar (opcional). Si None, usa los del primer archivo.
    """
    if not input_files:
        raise ValueError("No se proporcionaron archivos de entrada")
    
    combined_audio_data = b""
    reference_params = force_params
    incompatible_files = []
    
    print(f"Procesando {len(input_files)} archivos WAV...")
    
    for i, file_path in enumerate(input_files):
        try:
            print(f"Procesando archivo {i+1}/{len(input_files)}: {os.path.basename(file_path)}")
            
            audio_data, params = load_wav_file(file_path)
            
            # Usar el primer archivo como referencia si no se especificaron parámetros
            if reference_params is None:
                reference_params = params
                print(f"Usando parámetros de referencia del primer archivo:")
                print(f"  - Canales: {params['num_channels']}")
                print(f"  - Frecuencia de muestreo: {params['sample_rate']} Hz")
                print(f"  - Bits por muestra: {params['bits_per_sample']}")
            
            # Verificar compatibilidad
            compatibility_issues = []
            if params['num_channels'] != reference_params['num_channels']:
                compatibility_issues.append(f"canales ({params['num_channels']} vs {reference_params['num_channels']})")
            if params['sample_rate'] != reference_params['sample_rate']:
                compatibility_issues.append(f"frecuencia ({params['sample_rate']} vs {reference_params['sample_rate']})")
            if params['bits_per_sample'] != reference_params['bits_per_sample']:
                compatibility_issues.append(f"bits por muestra ({params['bits_per_sample']} vs {reference_params['bits_per_sample']})")
            
            if compatibility_issues:
                incompatible_files.append(f"{os.path.basename(file_path)}: {', '.join(compatibility_issues)}")
                print(f"  ⚠️  ADVERTENCIA: Incompatibilidad detectada - {', '.join(compatibility_issues)}")
                log_error(f"Archivo incompatible {file_path}: {', '.join(compatibility_issues)}")
            
            # Agregar los datos de audio (incluso si hay incompatibilidades)
            combined_audio_data += audio_data
            print(f"  ✓ Agregado ({len(audio_data):,} bytes)")
            
        except Exception as e:
            print(f"  ❌ Error al procesar {file_path}: {e}")
            log_error(f"Error al procesar {file_path}: {e}")
            continue
    
    if not combined_audio_data:
        raise ValueError("No se pudieron procesar archivos válidos")
    
    # Mostrar advertencias de compatibilidad
    if incompatible_files:
        print(f"\n⚠️  ADVERTENCIAS DE COMPATIBILIDAD:")
        for warning in incompatible_files:
            print(f"  - {warning}")
        print("Los archivos se combinaron de todas formas, pero el resultado podría tener problemas de reproducción.\n")
    
    # Crear el archivo WAV final
    print(f"Creando archivo WAV combinado...")
    print(f"Tamaño total de datos de audio: {len(combined_audio_data):,} bytes")
    
    final_wav_header = create_wav_header(len(combined_audio_data), reference_params)
    final_wav_data = final_wav_header + combined_audio_data
    
    # Verificar permisos de escritura
    try:
        test_file = f"test_permissions_{int(time.time())}.tmp"
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
    except Exception as e:
        log_error(f"Error de permisos de escritura: {e}")
        # Intentar escribir en /tmp si hay problemas de permisos
        backup_path = f"/tmp/{os.path.basename(output_file)}"
        print(f"Advertencia: Problemas de permisos, guardando en: {backup_path}")
        output_file = backup_path
    
    save_binary_file(output_file, final_wav_data)
    
    # Calcular duración aproximada
    if reference_params['sample_rate'] > 0 and reference_params['block_align'] > 0:
        duration_seconds = len(combined_audio_data) / (reference_params['sample_rate'] * reference_params['block_align'])
        duration_minutes = duration_seconds / 60
        print(f"Duración aproximada: {duration_minutes:.1f} minutos ({duration_seconds:.1f} segundos)")
    
    return output_file


def main():
    parser = argparse.ArgumentParser(
        description="Une múltiples archivos WAV en un solo archivo WAV final.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s file1.wav file2.wav file3.wav -o combined.wav
  %(prog)s *.wav -o all_combined.wav
  %(prog)s folder/*.wav -o output.wav
  %(prog)s audio1.wav audio2.wav  # Salida automática: audio1_combined.wav
        """
    )
    
    parser.add_argument(
        "input_files", 
        nargs="+", 
        help="Archivos WAV a combinar. Acepta patrones glob (ej: *.wav)"
    )
    
    parser.add_argument(
        "-o", "--output", 
        help="Archivo WAV de salida. Si no se especifica, se genera automáticamente."
    )
    
    parser.add_argument(
        "--sort", 
        action="store_true", 
        help="Ordenar archivos alfabéticamente antes de combinar"
    )
    
    parser.add_argument(
        "--sort-numeric", 
        action="store_true", 
        help="Ordenar archivos numéricamente (útil para archivos como file1.wav, file2.wav, ...)"
    )
    
    args = parser.parse_args()
    
    # Expandir patrones glob y recopilar todos los archivos
    all_files = []
    for pattern in args.input_files:
        if '*' in pattern or '?' in pattern:
            # Es un patrón glob
            matched_files = glob.glob(pattern)
            if not matched_files:
                print(f"Advertencia: No se encontraron archivos que coincidan con '{pattern}'")
            all_files.extend(matched_files)
        else:
            # Es un archivo específico
            if os.path.exists(pattern):
                all_files.append(pattern)
            else:
                print(f"Advertencia: Archivo no encontrado: {pattern}")
    
    # Eliminar duplicados manteniendo el orden
    seen = set()
    unique_files = []
    for f in all_files:
        abs_path = os.path.abspath(f)
        if abs_path not in seen:
            seen.add(abs_path)
            unique_files.append(f)
    
    if not unique_files:
        print("Error: No se encontraron archivos WAV válidos para procesar.")
        return 1
    
    # Verificar que son archivos WAV
    wav_files = []
    for f in unique_files:
        if f.lower().endswith('.wav'):
            wav_files.append(f)
        else:
            print(f"Advertencia: Saltando archivo que no es WAV: {f}")
    
    if not wav_files:
        print("Error: No se encontraron archivos WAV para procesar.")
        return 1
    
    # Ordenar archivos si se solicita
    if args.sort_numeric:
        # Ordenamiento numérico inteligente
        def numeric_sort_key(filename):
            # Extraer números del nombre del archivo para ordenamiento numérico
            numbers = re.findall(r'\d+', os.path.basename(filename))
            return [int(num) for num in numbers] if numbers else [0]
        
        wav_files.sort(key=numeric_sort_key)
        print("Archivos ordenados numéricamente.")
    elif args.sort:
        wav_files.sort()
        print("Archivos ordenados alfabéticamente.")
    
    # Generar nombre de salida si no se especifica
    if args.output:
        output_file = args.output
    else:
        first_file = Path(wav_files[0])
        output_file = first_file.with_name(f"{first_file.stem}_combined.wav")
        print(f"Archivo de salida automático: {output_file}")
    
    # Asegurar extensión .wav (convertir a string si es necesario)
    output_file_str = str(output_file)
    if not output_file_str.lower().endswith('.wav'):
        output_file = output_file_str + '.wav'
    else:
        output_file = output_file_str
    
    print(f"\n=== ARCHIVOS A COMBINAR ===")
    for i, f in enumerate(wav_files, 1):
        print(f"{i:2}. {f}")
    print(f"Total: {len(wav_files)} archivos")
    print(f"Salida: {output_file}\n")
    
    try:
        final_output = join_wav_files(wav_files, output_file)
        print(f"\n✅ Combinación completada exitosamente!")
        print(f"Archivo final: {final_output}")
        
        # Mostrar información adicional
        try:
            file_size = os.path.getsize(final_output)
            print(f"Tamaño del archivo: {file_size:,} bytes ({file_size / (1024*1024):.1f} MB)")
        except:
            pass
            
    except Exception as e:
        print(f"\n❌ Error durante la combinación: {e}")
        log_error(f"Error en join_wav_files: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
