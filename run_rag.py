from langchain_ollama import OllamaEmbeddings
from langchain_ollama import ChatOllama

from src.rag.generic_rag import CustomQdrantVectorStore, RAGSolution
from src.web_scraper.web_scrapper import web_scraping_init


def initialize_rag():
    """Función para inicializar el motor RAG de forma compartida"""
    PERSIST_PATH = "data/vectorial_database/qdrant_storage"
    COLLECTION_NAME = "celsia_knowledge_base"
    
    # 1. Inicializar modelo y embeddings (puedes ajustar esto para usar Gemini o cualquier otro modelo)
    # model = init_chat_model("ollama:gemma4:latest")
    
    # model = ChatOllama(model="ollama:gemma4:latest",temperature=0.1)
    model = ChatOllama(model="mistral:latest",temperature=0.1)
    embeddings = OllamaEmbeddings(model="nomic-embed-text-v2-moe:latest")

    # 2. Crear el almacén (STORE)
    custom_store = CustomQdrantVectorStore(
        persist_path=PERSIST_PATH,
        collection_name=COLLECTION_NAME,
        embedding_model=embeddings # La variable que definiste arriba
    )

    # 3. Inyectar el store en RAGSolution (Aquí estaba el error)
    rag = RAGSolution(store=custom_store, model=model, embeddings=embeddings)
    return rag, rag.build_graph()

# Inicializamos para que sea importable
rag_engine, app_graph = initialize_rag()

# async def main():
#     await web_scraping_init("https://www.celsia.com/es/mapa-del-sitio/", output_dir_clean="data/celsia_knowledge_base_clean", output_dir_markdown="data/celsia_knowledge_base_markdown")

#     RE_INGESTAR = True 

#     if RE_INGESTAR:
#         print("🗑️ Limpiando colección para evitar duplicados...")
#         rag_engine.vector_store.clear_all_data()

#         # Solo ejecutamos la ingestión si corremos este script directamente
#         print("🚀 Iniciando ingestión de datos...")
#         num_docs = rag_engine.ingest_data()
#         print(f"🎉 Ingestión completada: {num_docs} chunks")

#     print(app_graph.get_graph().draw_ascii())

#     # Paso 4: Construir grafo para pruebas
#     print("\n🔧 Construyendo grafo de agente...")

#     # Paso 5: Prueba rápida de búsqueda
#     print("\n🔍 Prueba de búsqueda semántica:")
#     # test_query = "¿Qué beneficios tiene la energía solar para pymes?"
#     test_query = "¿En que sitios puedo encontrar celsia?"
#     docs = rag_engine.vector_store.similarity_search(test_query, k=5)
#     for i, doc in enumerate(docs, 1):
#         print(f"\n[{i}] Score: {doc.metadata.get('score', 'N/A')}")
#         print(f"    Fuente: {doc.metadata.get('source', 'N/A')}")
#         print(f"    Contenido: {doc.page_content[:400]}...")
    
#     # Paso 6: Cerramos la conexión al finalizar
#     rag_engine.vector_store.close()      

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())

async def main():
    # Iniciamos el scraper
    await web_scraping_init(
        "https://www.celsia.com/es/mapa-del-sitio/", 
        output_dir_clean="data/celsia_knowledge_base_clean", 
        output_dir_markdown="data/celsia_knowledge_base_markdown"
    )

    RE_INGESTAR = True 

    try:
        if RE_INGESTAR:
            print("🗑️ Limpiando colección para evitar duplicados...")
            rag_engine.vector_store.clear_all_data()

            print("🚀 Iniciando ingestión de datos...")
            # Aquí se asume que tu RAGSolution tiene el método de hash para los 400 puntos
            num_docs = rag_engine.ingest_data() 
            print(f"🎉 Ingestión completada: {num_docs} chunks")

        # Dibujar Grafo
        print(app_graph.get_graph().draw_ascii())

        # Prueba de búsqueda
        print("\n🔍 Prueba de búsqueda semántica:")
        test_query = "¿En qué sitios puedo encontrar Celsia?"
        
        # Usamos el store para buscar
        docs = rag_engine.vector_store.similarity_search(test_query, k=5)
        
        for i, doc in enumerate(docs, 1):
            print(f"\n[{i}] Fuente: {doc.metadata.get('url', doc.metadata.get('source'))}")
            print(f"    Contenido: {doc.page_content[:250]}...")

    except Exception as e:
        print(f"💥 Error durante la ejecución: {e}")
    
    finally:
        # ESTO LIBERA EL ARCHIVO LOCK PARA QUE PUEDAS VOLVER A CORRER EL SCRIPT
        print("\n🔧 Cerrando recursos...")
        rag_engine.vector_store.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())