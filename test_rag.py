from run_batch import app_graph, context


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
        docs = context.vector_store.similarity_search(query, k=3)
        
        for i, doc in enumerate(docs, 1):
            print(f"\n  [{i}] 📄 {doc.metadata.get('source')}")
            print(f"      🏷️  Metadata: { {k:v for k,v in doc.metadata.items() if k not in ['source']} }")
            print(f"      📝 Preview: {doc.page_content[:200].replace(chr(10), ' ')}...")
    
    # Estadísticas generales
    try:
        collection_info = context.vector_store.client.get_collection(context.vector_store.collection_name)
        print(f"\n📊 Colección: {context.vector_store.collection_name}")
        print(f"   • Total puntos: {collection_info.points_count}")
        print(f"   • Dimensión vector: {collection_info.config.params.vectors.size}")
    except Exception as e:
        print(f"⚠️ No se pudo obtener info de colección: {e}")

    finally:
        context.vector_store.close()  # Cerramos la conexión al finalizar

if __name__ == "__main__":
    main()