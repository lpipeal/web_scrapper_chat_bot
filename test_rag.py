from run_rag import app_graph, rag_engine

# def main():  
#     print("\n🔍 Prueba de búsqueda semántica:")
#     # test_query = "¿Qué beneficios tiene la energía solar para pymes?"
#     test_query = "¿Quien es el presidente de celsia?"
#     docs = rag_engine.vector_store.similarity_search(test_query, k=5)
#     for i, doc in enumerate(docs, 1):
#         print(f"\n[{i}] Score: {doc.metadata.get('score', 'N/A')}")
#         print(f"    Fuente: {doc.metadata.get('source', 'N/A')}")
#         print(f"    Contenido: {doc.page_content[:400]}...")
    
# if __name__ == "__main__":
#     main()



def main(sample_queries: list = None):
    """Inspecciona el contenido de la base vectorial para debugging"""
    
    if sample_queries is None:
        sample_queries = [
            "sedes oficinas Celsia",
            "dónde está Celsia", 
            "puntos de atención",
            "cobertura geográfica"
        ]
    
    print("\n" + "="*80)
    print("🔬 DEBUG: Contenido indexado en vector store")
    print("="*80)
    
    for query in sample_queries:
        print(f"\n❓ Query de prueba: '{query}'")
        docs = rag_engine.vector_store.similarity_search(query, k=3)
        
        for i, doc in enumerate(docs, 1):
            print(f"\n  [{i}] 📄 {doc.metadata.get('source')}")
            print(f"      🏷️  Metadata: { {k:v for k,v in doc.metadata.items() if k not in ['source']} }")
            print(f"      📝 Preview: {doc.page_content[:200].replace(chr(10), ' ')}...")
    
    # Estadísticas generales
    try:
        collection_info = rag_engine.vector_store.client.get_collection(rag_engine.vector_store.collection_name)
        print(f"\n📊 Colección: {rag_engine.vector_store.collection_name}")
        print(f"   • Total puntos: {collection_info.points_count}")
        print(f"   • Dimensión vector: {collection_info.config.params.vectors.size}")
    except Exception as e:
        print(f"⚠️ No se pudo obtener info de colección: {e}")

    finally:
        rag_engine.vector_store.close()  # Cerramos la conexión al finalizar

if __name__ == "__main__":
    main()