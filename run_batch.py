import asyncio
from langchain_ollama import OllamaEmbeddings, ChatOllama
from src.rag.custom_quadrant_vector_store import CustomQdrantVectorStore 
from src.context.agent_context import AgentContext
from src.rag.rag_solution import RAGSolution
from src.graph_solution.graph_factory import CelsiaWorkflow
# from src.graph_solution.graph import CelsiaWorkflow

from src.web_scraper.web_scrapper import web_scraping_init


def get_agent_app():
    
    PERSIST_PATH = "data/vectorial_database/qdrant_storage"
    COLLECTION_NAME = "celsia_knowledge_base"
    
    # 1. Inicializar modelo y embeddings (puedes ajustar esto para usar Gemini o cualquier otro modelo)
    llm = ChatOllama(model="mistral:latest", temperature=0.1)
    embeddings = OllamaEmbeddings(model="nomic-embed-text-v2-moe:latest")
    
    # 2. Crear el almacén (STORE)
    vector_store = CustomQdrantVectorStore(
        persist_path=PERSIST_PATH,
        collection_name=COLLECTION_NAME,
        embedding_model=embeddings # La variable que definiste arriba
    )
    
    context = AgentContext(
        llm=llm, 
        embeddings=embeddings, 
        vector_store=vector_store, 
        basic_info_path="data/documents/basic_information.json"
    )
    
    # 2. Build
    rag_engine = RAGSolution(context)
    app_graph = CelsiaWorkflow(context).build()
    return app_graph, rag_engine, context

# Variable global para que otros archivos puedan importar
app_graph, rag_engine, context = get_agent_app()



async def main():

    try:
        # 1. Scraper (Opcional, se puede comentar si los datos ya existen)
        await web_scraping_init("https://www.celsia.com/es/mapa-del-sitio/", 
                                 output_dir_clean="data/celsia_knowledge_base_clean", 
                                 output_dir_markdown="data/celsia_knowledge_base_markdown")

        # 6. Ejecución
        print("\n🤖 Bot de Celsia Online. Haz tu pregunta:")
        query = "¿Cuál es el NIT y qué servicios tienen para empresas?"
        
        result = await app_graph.ainvoke({"query": query})
        print(f"\n--- RESPUESTA ---\n{result['final_answer']}")

        print(app_graph.get_graph().draw_ascii())
    
    finally:
        if hasattr(context.vector_store, 'close'):
            context.vector_store.close()

if __name__ == "__main__":
    asyncio.run(main())