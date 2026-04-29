import asyncio
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter

async def create_master_context(input_dir="celsia_knowledge_base_clean"):
    all_text = ""
    # 1. Leer todos los archivos limpios
    for filename in os.listdir(input_dir):
        if filename.endswith(".txt"):
            with open(os.path.join(input_dir, filename), "r", encoding="utf-8") as f:
                all_text += f"\n\n--- DOCUMENTO: {filename} ---\n"
                all_text += f.read()

    # 2. Configurar el Chunking (Segmentación semántica)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " "]
    )
    
    chunks = text_splitter.split_text(all_text)
    
    # 3. Guardar el contexto consolidado para el prompt
    with open("master_context.txt", "w", encoding="utf-8") as f:
        f.write("\n\n".join(chunks))
    
    print(f"✅ Contexto preparado: {len(chunks)} fragmentos generados.")

if __name__ == "__main__":
    asyncio.run(create_master_context())



import os
import re

async def create_master_context_clean(ruta_carpeta, archivo_salida):
    contenido_unico = set()
    documentos_procesados = []

    # 1. Leer todos los archivos de la carpeta
    archivos = [f for f in os.listdir(ruta_carpeta) if f.endswith(('.txt', '.md'))]
    
    print(f"Procesando {len(archivos)} archivos...")

    for nombre_archivo in archivos:
        with open(os.path.join(ruta_carpeta, nombre_archivo), "r", encoding="utf-8") as f:
            lineas = f.readlines()
            
            texto_limpio = []
            for linea in lineas:
                linea = linea.strip()
                
                # 2. Filtrar líneas inútiles o de "ruido"
                basura = [
                    "Estamos en mantenimiento", "mejoramos tu experiencia", 
                    "Cerrar", "close", "Registro exitoso", "¡Te damos la bienvenida!",
                    "--- DOCUMENTO:", "FUENTE ORIGINAL:", "-------"
                ]
                
                if any(b in linea for b in basura) or len(linea) < 5:
                    continue
                
                # 3. Evitar duplicados exactos de párrafos
                if linea not in contenido_unico:
                    texto_limpio.append(linea)
                    contenido_unico.add(linea)
            
            if texto_limpio:
                documentos_procesados.append(f"--- INFO DE: {nombre_archivo} ---\n" + "\n".join(texto_limpio))

    # 4. Guardar el resultado final
    with open(archivo_salida, "w", encoding="utf-8") as f:
        f.write("\n\n".join(documentos_procesados))
    
    print(f"✅ ¡Hecho! Archivo creado: {archivo_salida}")
    print(f"Se eliminaron miles de caracteres repetidos.")

# Ejecución (asegúrate de que la carpeta 'data' es donde tienes tus txt)
# await create_master_context_clean("tu_carpeta_de_documentos", "master_context_clean.txt")

if __name__ == "__main__":
    asyncio.run(create_master_context_clean())